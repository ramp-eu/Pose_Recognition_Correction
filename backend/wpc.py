import time
import requests
import argparse
from pathlib import Path
import time
import threading

import pyrealsense2 as rs
import cv2
import numpy as np
import json

from eaws.eaws import EAWS

from eaws.ergonomics_struct import build_struct, get_ergonomics_skeleton
from eaws.ergonomics import visualise_ergonomics

np.set_printoptions(precision=2, suppress=True)

from modules.realsense_utils import convert_2d_to_3d
from model import PoseEstimator

parser = argparse.ArgumentParser(description='List the content of a folder')
parser.add_argument('-m', '--model_path', type=Path, help='Path to model')
parser.add_argument('-pc', '--posture_conditions_path', type=Path, help='Path to posture conditions JSON file', default="posture_conditions.json")
parser.add_argument('-pp', '--posture_points_path', type=Path, help='Path to posture points JSON file', default="posture_points.json")
parser.add_argument('-tf', '--num_tolerance_frame', type=int, help='Number of frames to consider for smoothing of the result', default=10)
parser.add_argument('-sid', '--session_id', type=str, help='The session id', default='28b1927b-f063-491d-ae30-11093846e7a8')
parser.add_argument('-wid', '--worker_id', type=str, help='The worker id', default='7cc2cc78-a09c-4618-8ab0-7d62e8252496')
parser.add_argument('-use_rs', '--use_realsense', type=str, help='Use realsense cam true/false', default='false')
parser.add_argument('-o_url', '--orion_base_url', type=str, help='Base url for orion broker', default='http://localhost:1026')
parser.add_argument('-hl', '--headless', type=bool, help='Should we run headless?', default=False)
args = parser.parse_args()


def publish_ergonomics_continuous(time_interval=10):
    global ergonomic_data
    global keep_alive

    url = f'{args.orion_base_url}/v2/entities'
    n = 1
    with threading.Lock():
        body = build_struct(ergonomic_data)
    body['type'] = 'ergonomics'
    body['id'] = args.worker_id
    print(f"The api post data: {body}")
    try:
        r = requests.post(url, json=body)
        print(f'Return code {r.status_code}')
        print(r.text)
        print(f'{n} Ergonomics posted')
    except Exception as e:
        print(f'Exception {e}')

    keep_alive = True
    while keep_alive:
        time.sleep(time_interval)
        # update entity
        entity_id = args.worker_id
        url = f'{args.orion_base_url}/v2/entities/{entity_id}/attrs'
        with threading.Lock():
            body = build_struct(ergonomic_data)
        print(f"The api patched data: {body}")
        try:
            r = requests.patch(url, json=body)
            print(f'Return code {r.status_code}')
            print(r.text)
            print(f'{n} Ergonomics updated')
        except Exception as e:
            print(f'Exception {e}')
        n += 1



def main():
    global ergonomic_data
    global keep_alive

    # create model
    # The data to be published
    ergonomic_data = get_ergonomics_skeleton()
    ergonomic_data['session'] = args.session_id
    pe = PoseEstimator(args.model_path)

    ergonomics_publisher_thread = threading.Thread(target=publish_ergonomics_continuous, kwargs={'time_interval': 5})
    ergonomics_publisher_thread.start()

    # Configure depth and color streams
    if args.use_realsense == 'true':
        pipeline = rs.pipeline()
        config = rs.config()

        # Get device product line for setting a supporting resolution
        pipeline_wrapper = rs.pipeline_wrapper(pipeline)
        pipeline_profile = config.resolve(pipeline_wrapper)
        device = pipeline_profile.get_device()
        device_product_line = str(device.get_info(rs.camera_info.product_line))

        found_rgb = False
        for s in device.sensors:
            if s.get_info(rs.camera_info.name) == 'RGB Camera':
                found_rgb = True
                break
        if not found_rgb:
            print("The demo requires Depth camera with Color sensor")
            exit(0)

        config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        if device_product_line == 'L500':
            config.enable_stream(rs.stream.color, 960, 540, rs.format.bgr8, 30)
        else:
            config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

        # Start streaming
        profile = pipeline.start(config)

        # Getting the depth sensor's depth scale (see rs-align example for explanation)
        depth_sensor = profile.get_device().first_depth_sensor()
        depth_scale = depth_sensor.get_depth_scale()
        print("Depth Scale is: ", depth_scale)

        # We will be removing the background of objects more than
        #  clipping_distance_in_meters meters away
        clipping_distance_in_meters = 1  #1 meter
        clipping_distance = clipping_distance_in_meters / depth_scale

        # Create an align object
        # rs.align allows us to perform alignment of depth frames to others frames
        # The "align_to" is the stream type to which we plan to align depth frames.
        align_to = rs.stream.color
        align = rs.align(align_to)

        depth_profile = rs.video_stream_profile(profile.get_stream(
            rs.stream.depth))
        depth_intrinsics = depth_profile.get_intrinsics()
    else:
        vid = cv2.VideoCapture(0)

    if args.headless == False:
        cv2.namedWindow('Visualisation')

    keep_alive = True
    eaws_person = EAWS()
    while keep_alive:
        if args.use_realsense == 'true':
            # Get frameset of color and depth
            frames = pipeline.wait_for_frames()
            # Align the depth frame to color frame
            aligned_frames = align.process(frames)

            # Get aligned frames
            aligned_depth_frame = aligned_frames.get_depth_frame(
            )  # aligned_depth_frame is a 640x480 depth image
            color_frame = aligned_frames.get_color_frame()

            # Validate that both frames are valid
            if not aligned_depth_frame or not color_frame:
                continue

            depth_image = np.asanyarray(aligned_depth_frame.get_data())
            color_image = np.asanyarray(color_frame.get_data())
            poses_3d, poses_2d = pe.predict(color_image[..., ::-1])
            p_3d_reshaped = []
            if poses_2d.shape[0] > 0:
                p = poses_2d[0, :54]
                p_reshaped = p.reshape((-1, 3))
                p_3d_reshaped = convert_2d_to_3d(p_reshaped, depth_image,
                                            depth_intrinsics)
            frame = color_image
        else:
            ret, frame = vid.read()
            poses_3d, poses_2d = pe.predict(frame)
            p_3d_reshaped = []
            if poses_3d.shape[0] > 0:
                p_3d = poses_3d[0, :76]
                p_3d_reshaped = p_3d.reshape((-1, 4))
                p_3d_reshaped = p_3d_reshaped[:,:3]

        if len(p_3d_reshaped):
            if poses_2d.shape[0] > 0:
                p = poses_2d[0, :54]
                p_reshaped = p.reshape((-1, 3))

            eaws_person.update_pose(p_3d_reshaped, time.time())
            with threading.Lock():
                ergonomic_data = eaws_person.get_ergonomics_data()
            visualise_ergonomics(frame, p_reshaped, eaws_person.current_ergonomic_stats)
        else:
            with threading.Lock():
                ergonomic_data = get_ergonomics_skeleton()
                ergonomic_data['session'] = args.session_id

        if args.headless == False:
            cv2.imshow('Visualisation', frame)
            if cv2.waitKey(1) == 27:
                break  # esc to quit

    if args.headless == False:
        cv2.destroyAllWindows()
    # pipeline.stop()
    print(f'Ready to leave but I am still waiting for publisher to join')
    keep_alive = False
    ergonomics_publisher_thread.join()


if __name__ == '__main__':
    main()
