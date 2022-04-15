import os
import pathlib
import sys
sys.path.insert(0, os.path.join(pathlib.Path().absolute(), 'lib'))

import cv2

from modules.inference_engine import InferenceEngine
# from modules.draw import Plotter3d, draw_poses
from modules.parse_poses import parse_poses

class PoseEstimator(object):
    def __init__(self, model_path, device='CPU'):
        self.stride = 8
        self.input_height = 256

        self.inference_engine = InferenceEngine(model_path, device, self.stride)


    def predict(self, frame):
        input_scale = self.input_height / frame.shape[0]

        scaled_img = cv2.resize(frame, dsize=None, fx=input_scale, fy=input_scale)
        if input_scale < 0:  # Focal length is unknown
            input_scale = np.float32(0.8 * frame.shape[1])

        inference_result = self.inference_engine.infer(scaled_img)
        poses_3d, poses_2d = parse_poses(inference_result, input_scale, self.stride, input_scale, True)

        return poses_3d, poses_2d
