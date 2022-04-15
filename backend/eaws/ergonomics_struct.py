import time

ergonomics_template = {
    'body_angle': {
        'type': 'Float'
    },
    'upper_limbs_angle': {
        'type': 'Float'
    },
    'lower_limbs_angle': {
        'type': 'Float'
    },
    'pose_1': {
        'type': 'Float'
    },
    'pose_3': {
        'type': 'Float'
    },
    'pose_4': {
        'type': 'Float'
    },
    'pose_5': {
        'type': 'Float'
    },
    'pose_6': {
        'type': 'Float'
    },
    'pose_7': {
        'type': 'Float'
    },
    'pose_9': {
        'type': 'Float'
    },
    'pose_10': {
        'type': 'Float'
    },
    'pose_11': {
        'type': 'Float'
    },
    'pose_12': {
        'type': 'Float'
    },
    'pose_13': {
        'type': 'Float'
    },
    'pose_14': {
        'type': 'Float'
    },
    'pose_15': {
        'type': 'Float'
    },
    'eaws_score': {
        'type': 'Float'
    },
    'time': {
        'type': 'Integer'
    },
    'session': {
        'type': 'String'
    }
}


def get_ergonomics_skeleton():
    return {
        'body_angle': 0.0,
        'upper_limbs_angle': 0.0,
        'lower_limbs_angle': 0.0,
        'pose_1': 0.0,
        'pose_3': 0.0,
        'pose_4': 0.0,
        'pose_5': 0.0,
        'pose_6': 0.0,
        'pose_7': 0.0,
        'pose_9': 0.0,
        'pose_10': 0.0,
        'pose_11': 0.0,
        'pose_12': 0.0,
        'pose_13': 0.0,
        'pose_14': 0.0,
        'pose_15': 0.0,
        'eaws_score': 0.0,
        'time': round(time.time() * 1000),
        'session': ''
    }


def build_struct(data):
    res = ergonomics_template.copy()
    for k, v in data.items():
        res[k]['value'] = v

    return res


