from ast import arg
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

from eaws.ergonomics_struct import build_struct, get_ergonomics_skeleton
from eaws.ergonomics import get_ergonomics_stats, visualise_ergonomics
from eaws.posture_conditions import get_all_posture_status

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


def build_ergonomics_data(accumulated_points, current_posture):
    ergonomics_dict = {}
    ergonomics_dict['body_angle'] = current_posture['body_angle']
    ergonomics_dict['upper_limbs_angle'] = current_posture['arm_angles'][0]
    ergonomics_dict['lower_limbs_angle'] = current_posture['knee_angles'][0]

    eaws_score = 0
    for pose_id, pose_points in accumulated_points.items():
        ergonomics_dict[f'pose_{pose_id}'] = pose_points
        eaws_score += pose_points

    ergonomics_dict['eaws_score'] = eaws_score
    ergonomics_dict['time'] = round(time.time() * 1000)
    ergonomics_dict['session'] = args.session_id

    return ergonomics_dict


# The data to be published
ergonomic_data = get_ergonomics_skeleton()
ergonomic_data['session'] = args.session_id

def main():
    global ergonomic_data
    global keep_alive

    # create model
    pe = PoseEstimator(args.model_path)

    time_unit_s_per_minute = [3, 4, 6, 9, 12, 16, 20, 30, 40, 50]
    loop_frequency_per_unit_time = 10
    loop_counter = 0
    max_tolerance_frames = args.num_tolerance_frame
    results_smoothing_queue = []

    with open('eaws/posture_points.json') as f:
        posture_points = json.load(f)

    current_pose_loop_counter = {}
    accumulated_points = {}

    ergonomics_publisher_thread = threading.Thread(target=publish_ergonomics_continuous, kwargs={'time_interval': 5})
    ergonomics_publisher_thread.start()

    for pose_id, pp in posture_points.items():
        current_pose_loop_counter[pose_id] = 0
        accumulated_points[pose_id] = 0

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
    while keep_alive:
        if args.use_realsense == 'true':
            # Get frameset of color and depth
            frames = pipeline.wait_for_frames()
            # frames.get_depth_frame() is a 640x360 depth image
            loop_counter += 1
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
            print(frame.shape)
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
            ergonomics_stats = get_ergonomics_stats(p_3d_reshaped)
            current_posture = {
                'body_angle': ergonomics_stats['BODY'],
                'arm_angles': ergonomics_stats['UL'],
                'knee_angles': ergonomics_stats['LL'],
                'lower_arm_angles': ergonomics_stats['BL']
            }
            current_posture_status = get_all_posture_status(current_posture)

            if max_tolerance_frames:
                for pose_id, is_pose_in_bound in current_posture_status.items(
                ):
                    if is_pose_in_bound:
                        results_smoothing_queue.append(pose_id)
                        break
                max_tolerance_frames -= 1
            else:
                if len(results_smoothing_queue):
                    smoothed_pose_id = max(results_smoothing_queue,
                                        key=results_smoothing_queue.count)
                else:
                    smoothed_pose_id = None

                for pose_id, loop_val in current_pose_loop_counter.items():
                    if pose_id == smoothed_pose_id:
                        current_pose_loop_counter[pose_id] += 1
                    else:
                        current_pose_loop_counter[pose_id] = 0

                # reset the results queue and set the tolerance frame value
                results_smoothing_queue = []
                max_tolerance_frames = args.num_tolerance_frame

            # update accumulated points for actual unit of time considered
            if loop_counter % loop_frequency_per_unit_time == 0:  # if actual one unit of our considered time
                for pose_id, loop_val in current_pose_loop_counter.items():
                    if loop_val:
                        num_of_frames_in_pose = loop_val * args.num_tolerance_frame
                        actual_time_in_pose = int(num_of_frames_in_pose /
                                                loop_frequency_per_unit_time)
                        if actual_time_in_pose in time_unit_s_per_minute:
                            idx_time = time_unit_s_per_minute.index(
                                actual_time_in_pose)
                            accumulated_points[pose_id] += posture_points[
                                pose_id][idx_time]
                        break

            with threading.Lock():
                ergonomic_data = build_ergonomics_data(accumulated_points,
                                                current_posture)
            visualise_ergonomics(frame, p_reshaped, ergonomics_stats)
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
