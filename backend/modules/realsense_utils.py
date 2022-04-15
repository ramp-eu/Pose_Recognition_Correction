import numpy as np
import pyrealsense2

def convert_2d_to_3d(points, depth_image, intrinsics):
    results = []
    for row in range(points.shape[0]):
        if points[row,-1] < 0:
            results.append((0,0,0))
            continue

        x = round(points[row, 0])
        y = round(points[row, 1])
        depth = depth_image[y][x]

        row_result = pyrealsense2.rs2_deproject_pixel_to_point(intrinsics, [x, y], depth)

        results.append(row_result)

    return np.array(results)

