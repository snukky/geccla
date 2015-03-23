import sys


def iterate_text_and_confs(text_file, cnfs_file):
    """
    Iterates confusion examples for each sentence from source text file.
    Yields a tuple: (a number of sentence, [confusion examples], a sentence).
    """
    text_io = open(text_file)
    cnfs_io = open(cnfs_file)

    n = 0
    m = 0
    cnfs_n, i, j, err, cor, feats = parse_conf_line(cnfs_io.readline())

    for line in text_io:
        examples = []

        while cnfs_n == n:
            examples.append( (i, j, err, cor, feats) )
            cnfs_n, i, j, err, cor, feats = parse_conf_line(cnfs_io.readline())
            m += 1
        
        yield (n, examples, line.strip())
        n += 1

    text_io.close()
    cnfs_io.close()


def format_conf(conf, features={}):
    """
    Formats single line for .cnfs file from a tuple with six elements or from a
    tuple with five elements and features provided as a dict.
    """
    if len(conf) == 6:
        features = conf[5]
    return "{}|||{} {}|||{}|||{}|||{}".format(conf[0], conf[1], conf[2], 
        conf[3], conf[4], __format_conf_features(features))

def __format_conf_features(features={}):
    return ' '.join([ "{}={}".format(__escape_chars(key), __escape_chars(val))
                      for key, val in features.iteritems() ])

def __escape_chars(text):
    return text.replace(' ', '_').replace('=', '<eq>')


def parse_conf_line(line, with_features=False):
    """
    Parses single line from .cnfs line as a tuple with six elements. Features
    are returned as a list by default or as a dict.
    """
    if not line:
        return (None, None, None, None, None, None)

    s, ij, err, cor, feats = line.strip().split('|||')
    i, j = ij.split()
    if with_features:
        feats = dict([ pair.split('=') for pair in feats.split() ])
    else:
        feats = feats.split()

    return (int(s), int(i), int(j), err, cor, feats)
