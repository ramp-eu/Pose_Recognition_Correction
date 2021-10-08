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
    'pose_2': {
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
    'pose_8': {
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


def build_struct(data):
    res = ergonomics_template.copy()
    for k, v in data.items():
        res[k]['value'] = v

    return res


