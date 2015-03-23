
ALGORITHMS_AND_FORMATS = {
    'majority'  : 'libsvm',
    'snow'      : 'snow',
    'vw'        : 'vw',
    'liblinear' : 'libsvm',
    'maxent'    : 'maxent',
    'perfect'   : 'libsvm',
}

ALGORITHMS = ALGORITHMS_AND_FORMATS.keys()

FORMATS = list(set(ALGORITHMS_AND_FORMATS.values()))

def algorithm_to_format(algorithm):
    return ALGORITHMS_AND_FORMATS[algorithm]
