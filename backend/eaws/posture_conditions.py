import json

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
                                                 posture['BODY_ANGLE'])
    if 'left_arm_angles' in posture_limits.keys():
        is_left_arm_angle_in_bound = check_in_bounds(
            posture_limits['left_arm_angles'], posture['SHOULDER_ANGLE'][0])
    if 'right_arm_angles' in posture_limits.keys():
        is_right_arm_angle_in_bound = check_in_bounds(
            posture_limits['right_arm_angles'], posture['SHOULDER_ANGLE'][1])
    if 'left_knee_angles' in posture_limits.keys():
        is_left_knee_angle_in_bound = check_in_bounds(
            posture_limits['left_knee_angles'], posture['KNEE_ANGLE'][0])
    if 'right_knee_angles' in posture_limits.keys():
        is_right_knee_angle_in_bound = check_in_bounds(
            posture_limits['right_knee_angles'], posture['KNEE_ANGLE'][1])

    return is_body_angle_in_bound and is_left_arm_angle_in_bound and is_right_arm_angle_in_bound and is_left_knee_angle_in_bound and is_right_knee_angle_in_bound


def get_all_posture_status(posture):
    with open('eaws/posture_conditions.json') as f:
        postures_group_conditions = json.load(f)
    current_posture_group_status = {}
    for postures_group_id, postures_group in postures_group_conditions.items():
        is_posture_in_bounds = False
        for posture_limit in postures_group:
            is_posture_in_bounds = is_posture_in_bounds or check_postures_in_bounds(
                posture_limit, posture)

        current_posture_group_status[postures_group_id] = is_posture_in_bounds
    return current_posture_group_status
