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

from ergonomics_struct import build_struct

np.set_printoptions(precision=2, suppress=True)

from modules.draw import draw_poses
from modules.realsense_utils import convert_2d_to_3d
from modules.ergonomics import get_ergonomics_stats, visualise_ergonomics
from model import PoseEstimator

parser = argparse.ArgumentParser(description='List the content of a folder')
parser.add_argument('-m', '--model_path', type=Path, help='Path to model')
parser.add_argument('-pc', '--posture_conditions_path', type=Path, help='Path to posture conditions JSON file', default="posture_conditions.json")
parser.add_argument('-pp', '--posture_points_path', type=Path, help='Path to posture points JSON file', default="posture_points.json")
parser.add_argument('-tf', '--num_tolerance_frame', type=int, help='Number of frames to consider for smoothing of the result', default=10)
parser.add_argument('-sid', '--session_id', type=str, help='The session id', default='28b1927b-f063-491d-ae30-11093846e7a8')
parser.add_argument('-wid', '--worker_id', type=str, help='The worker id', default='7cc2cc78-a09c-4618-8ab0-7d62e8252496')
args = parser.parse_args()


def get_ergonomics_skeleton():
    return {
        'body_angle': 0.0,
        'upper_limbs_angle': 0.0,
        'lower_limbs_angle': 0.0,
        'pose_1': 0.0,
        'pose_2': 0.0,
        'pose_3': 0.0,
        'pose_4': 0.0,
        'pose_5': 0.0,
        'pose_6': 0.0,
        'pose_7': 0.0,
        'pose_8': 0.0,
        'pose_9': 0.0,
        'pose_10': 0.0,
        'pose_11': 0.0,
        'pose_12': 0.0,
        'pose_13': 0.0,
        'pose_14': 0.0,
        'eaws_score': 0.0,
        'session': args.session_id,
        'time': round(time.time() * 1000)
    }


def publish_ergonomics_continuous(time_interval=10):
    global ergonomic_data
    url = 'http://cognitivehri.collab-cloud.eu:1026/v2/entities'
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
    while True:
        time.sleep(time_interval)
        # update entity
        entity_id = args.worker_id
        url = f'http://cognitivehri.collab-cloud.eu:1026/v2/entities/{entity_id}/attrs'
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

def check_in_bounds(limits, val):
    if val is not None:
        if val >= limits['min'] and val <= limits['max']:
            return True
    return False


def check_postures_in_bounds(posture_limits, posture):
    is_body_angle_in_bound = True
    is_left_arm_angle_in_bound = True
    is_right_arm_angle_in_bound = True
    is_left_knee_angle_in_bound = True
    is_right_knee_angle_in_bound = True

    if 'body_angle' in posture_limits.keys():
        is_body_angle_in_bound = check_in_bounds(posture_limits['body_angle'],
                                                 posture['body_angle'])
    if 'left_arm_angles' in posture_limits.keys():
        is_left_arm_angle_in_bound = check_in_bounds(
            posture_limits['left_arm_angles'], posture['arm_angles'][0])
    if 'right_arm_angles' in posture_limits.keys():
        is_right_arm_angle_in_bound = check_in_bounds(
            posture_limits['right_arm_angles'], posture['arm_angles'][1])
    if 'left_knee_angles' in posture_limits.keys():
        is_left_knee_angle_in_bound = check_in_bounds(
            posture_limits['left_knee_angles'], posture['knee_angles'][0])
    if 'right_knee_angles' in posture_limits.keys():
        is_right_knee_angle_in_bound = check_in_bounds(
            posture_limits['right_knee_angles'], posture['knee_angles'][1])

    return is_body_angle_in_bound and is_left_arm_angle_in_bound and is_right_arm_angle_in_bound and is_left_knee_angle_in_bound and is_right_knee_angle_in_bound


def get_all_posture_status(postures_group_conditions, posture):
    current_posture_group_status = {}
    for postures_group_id, postures_group in postures_group_conditions.items():
        is_posture_in_bounds = False
        for posture_limit in postures_group:
            is_posture_in_bounds = is_posture_in_bounds or check_postures_in_bounds(
                posture_limit, posture)

        current_posture_group_status[postures_group_id] = is_posture_in_bounds
    return current_posture_group_status


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

def main():
    global ergonomic_data
    time_unit_s_per_minute = [3, 4, 6, 9, 12, 16, 20, 30, 40, 50]
    loop_frequency_per_unit_time = 10
    loop_counter = 0
    max_tolerance_frames = args.num_tolerance_frame
    results_smoothing_queue = []

    with open(args.posture_points_path) as f:
        posture_points = json.load(f)

    with open(args.posture_conditions_path) as f:
        posture_conditions = json.load(f)

    current_pose_loop_counter = {}
    accumulated_points = {}

    ergonomics_publisher_thread = threading.Thread(target=publish_ergonomics_continuous, kwargs={'time_interval': 5})
    ergonomics_publisher_thread.start()

    for pose_id, pp in posture_points.items():
        current_pose_loop_counter[pose_id] = 0
        accumulated_points[pose_id] = 0

    # Configure depth and color streams
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

    # create model
    pe = PoseEstimator(args.model_path)

    while True:
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

        if poses_2d.shape[0] > 0:
            p = poses_2d[0, :54]

            # draw_poses(color_image, poses_2d)

            p_reshaped = p.reshape((-1, 3))
            cam_points_3d = convert_2d_to_3d(p_reshaped, depth_image,
                                             depth_intrinsics)

            ergonomics_stats = get_ergonomics_stats(cam_points_3d)
            current_posture = {
                'body_angle': ergonomics_stats['BODY'],
                'arm_angles': ergonomics_stats['UL'],
                'knee_angles': ergonomics_stats['LL']
            }
            current_posture_status = get_all_posture_status(
                posture_conditions, current_posture)

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

            visualise_ergonomics(color_image, p_reshaped, ergonomics_stats)
        else:
            with threading.Lock():
                ergonomic_data = get_ergonomics_skeleton()

        cv2.imshow('Visualisation', color_image)

        if cv2.waitKey(1) == 27:
            break  # esc to quit

    cv2.destroyAllWindows()
    pipeline.stop()


if __name__ == '__main__':
    main()
