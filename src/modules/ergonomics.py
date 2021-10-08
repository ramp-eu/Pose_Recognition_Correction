import cv2
import numpy as np
from skspatial.objects import Plane, Points, Vector

JOINT_LUT = {
    'NECK' : 0,
    'NOSE' : 1,
    'L_SHOULDER' : 3,
    'L_ELBOW' : 4,
    'L_WRIST' : 5,
    'L_HIP' : 6,
    'L_KNEE' : 7,
    'L_ANKLE' : 8,
    'R_SHOULDER' : 9,
    'R_ELBOW' : 10,
    'R_WRIST' : 11,
    'R_HIP' : 12,
    'R_KNEE' : 13,
    'R_ANKLE' : 14,
    'R_EYE' : 15,
    'L_EYE' : 16,
    'R_EAR' : 17,
    'L_EAR' : 18,
}

def compute_body_angle(points_3d):
    # extract body points
    BODY_POINTS = ['L_SHOULDER', 
                   'R_SHOULDER', 
                   'L_HIP', 
                   'R_HIP', 
                   'NECK', 
                   'NOSE', 
                   'L_EYE', 
                   'R_EYE', 
                   'R_EAR']
    joints = [points_3d[JOINT_LUT[p],:].tolist() for p in BODY_POINTS if points_3d[JOINT_LUT[p],:].any()]

    if len(joints) >= 3:
        body_plane = Plane.best_fit(Points(joints))
        body_angle = np.degrees(Vector(body_plane.normal).angle_between([0,1,0])) - 90

        return body_angle
    else:
        return None

def compute_arm_angles(points_3d):
    UPPER_LIMBS_POINTS = ['L_SHOULDER', 'L_ELBOW', 'L_WRIST', 'R_SHOULDER', 'R_ELBOW', 'R_WRIST']
    joints = {p: points_3d[JOINT_LUT[p],:] for p in UPPER_LIMBS_POINTS if points_3d[JOINT_LUT[p],:].any()}

    if all(joint in joints.keys() for joint in ['L_SHOULDER', 'L_ELBOW']):
        l_arm_angle = np.degrees(Vector(joints['L_ELBOW']-joints['L_SHOULDER']).angle_between([0,1,0]))
    else:
        l_arm_angle = None

    if all(joint in joints.keys() for joint in ['R_SHOULDER', 'R_ELBOW']):
        r_arm_angle = np.degrees(Vector(joints['R_ELBOW']-joints['R_SHOULDER']).angle_between([0,1,0]))
    else:
        r_arm_angle = None

    return l_arm_angle, r_arm_angle

def compute_knee_angles(points_3d):
    # knee poses
    LOWER_LIMBS_POINTS = ['L_HIP', 'L_KNEE', 'L_ANKLE', 'R_HIP', 'R_KNEE', 'R_ANKLE']
    joints = {p: points_3d[JOINT_LUT[p],:] for p in LOWER_LIMBS_POINTS if points_3d[JOINT_LUT[p],:].any()}

    if all(joint in joints.keys() for joint in ['L_HIP', 'L_KNEE', 'L_ANKLE']):
        l_knee_angle = np.degrees(Vector(joints['L_HIP']-joints['L_KNEE']).angle_between(Vector(joints['L_ANKLE']-joints['L_KNEE'])))
    else:
        l_knee_angle = None

    if all(joint in joints.keys() for joint in ['R_HIP', 'R_KNEE', 'R_ANKLE']):
        r_knee_angle = np.degrees(Vector(joints['R_HIP']-joints['R_KNEE']).angle_between(Vector(joints['R_ANKLE']-joints['R_KNEE'])))
    else:
        r_knee_angle = None

    return l_knee_angle, r_knee_angle


def get_ergonomics_stats(points_3d):
    body_angle = compute_body_angle(points_3d)
    arm_angles = compute_arm_angles(points_3d)
    knee_angles = compute_knee_angles(points_3d)

    # print(f'Body angle: {body_angle}')
    # print(f'Arm angles: {arm_angles}')
    # print(f'Knee angles: {knee_angles}')

    return {
        'BODY' : body_angle,
        'UL' : arm_angles,
        'LL' : knee_angles
    }


body_edges = np.array(
    [[0, 1],  # neck - nose
     [1, 16], [16, 18],  # nose - l_eye - l_ear
     [1, 15], [15, 17],  # nose - r_eye - r_ear
     [0, 3], [3, 4], [4, 5],     # neck - l_shoulder - l_elbow - l_wrist
     [0, 9], [9, 10], [10, 11],  # neck - r_shoulder - r_elbow - r_wrist
     [0, 6], [6, 7], [7, 8],        # neck - l_hip - l_knee - l_ankle
     [0, 12], [12, 13], [13, 14]])  # neck - r_hip - r_knee - r_ankle

def visualise_ergonomics(img, joints_2d, ergonomics_stats):
    body_edges = [
        ('BODY', 'NECK', 'L_HIP'),
        ('BODY', 'NECK', 'R_HIP'),
        ('BODY', 'L_HIP', 'R_HIP'),
        ('UL', 'L_SHOULDER', 'L_ELBOW'),
        ('UL', 'R_SHOULDER', 'R_ELBOW'),
        ('LL', 'L_HIP', 'L_KNEE'),
        ('LL', 'L_KNEE', 'L_ANKLE'),
        ('LL', 'R_HIP', 'R_KNEE'),
        ('LL', 'R_KNEE', 'R_ANKLE'),
    ]

    for joint_type, joint1, joint2 in body_edges:
        color = (255,255,255)
        if joint_type == 'BODY':
            if ergonomics_stats['BODY'] is not None:
                value = np.clip(ergonomics_stats['BODY'], 0, 30) / 30
                value = value * 127 + 127
                value = np.array([[value]], dtype=np.uint8)
                color = cv2.applyColorMap(value, cv2.COLORMAP_JET)[0,0,:].tolist()

        elif joint_type == 'UL':
            if ergonomics_stats['UL'][0] is not None and joint1 == 'L_SHOULDER':
                value = np.clip(ergonomics_stats['UL'][0], 0, 150) / 150
                value = value * 127 + 127
                value = np.array([[value]], dtype=np.uint8)
                color = cv2.applyColorMap(value, cv2.COLORMAP_JET)[0,0,:].tolist()

            if ergonomics_stats['UL'][1] is not None and joint1 == 'R_SHOULDER':
                value = np.clip(ergonomics_stats['UL'][1], 0, 150) / 150
                value = value * 127 + 127
                value = np.array([[value]], dtype=np.uint8)
                color = cv2.applyColorMap(value, cv2.COLORMAP_JET)[0,0,:].tolist()
        else:
            if ergonomics_stats['LL'][0] is not None and joint1 in ['L_HIP', 'L_KNEE']:
                value = np.clip(abs(180 - ergonomics_stats['LL'][0]),0, 90) / 90
                value = value * 127 + 127
                value = np.array([[value]], dtype=np.uint8)
                color = cv2.applyColorMap(value, cv2.COLORMAP_JET)[0,0,:].tolist()

            if ergonomics_stats['LL'][1] is not None and joint2 in ['R_HIP', 'R_KNEE']:
                value = np.clip(abs(180 - ergonomics_stats['LL'][1]),0, 90) / 90
                value = value * 127 + 127
                value = np.array([[value]], dtype=np.uint8)
                color = cv2.applyColorMap(value, cv2.COLORMAP_JET)[0,0,:].tolist()

        # visualise
        j1 = joints_2d[JOINT_LUT[joint1]]
        j2 = joints_2d[JOINT_LUT[joint2]]
        if j1[2] > 0 and j2[2] > 0:
            cv2.line(img, (int(j1[0]), int(j1[1])), (int(j2[0]), int(j2[1])), color, 8)
