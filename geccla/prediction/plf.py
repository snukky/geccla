import os
import sys
import re

sys.path.insert(0, os.path.dirname(__file__))


def parse_plf_line(line):
    """
    Iterates over edges represented as arrays of (text, weight, length) triples.
    """
    for val in line.strip()[3:-4].split(',),(('):
        elems = val[:-1].split('),(') if '),(' in val else [val[:-1]]
        edges = []
        for elem in elems:
            text = re.search(r"'(.*)'", elem).group(1)
            weight, length = elem[elem.rfind("'")+2:].split(',')
            edges.append( (text, float(weight), int(length)) )
        yield edges
