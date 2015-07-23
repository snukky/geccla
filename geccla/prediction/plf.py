import os
import sys
import re

sys.path.insert(0, os.path.dirname(__file__))

from logger import log

DEBUG = True


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

def join_plf_lines(line1, line2, idx=None):
    graph1 = list(parse_plf_line(line1))
    graph2 = list(parse_plf_line(line2))

    graph = []
    idx1 = 0
    idx2 = 0

    if DEBUG and idx:
        log.debug("sid:   {}".format(idx))

    while idx1 < len(graph1) or idx2 < len(graph2):
        edges1 = graph1[idx1]
        edges2 = graph2[idx2]

        if DEBUG:
            log.debug("idxes: {} {}".format(idx1, idx2))
            log.debug("edges:\n{}\n{}".format(edges1, edges2))

        if len(edges1) == 1 and len(edges2) == 1:
            text1 = edges1[0][0].lower()
            text2 = edges2[0][0].lower()

            if DEBUG:
                log.debug("case:  1:1")
                if text1 != text2:
                    log.warn("different texts!")

            if text1 != text2:
                if text1 == graph2[idx2+1][0][0].lower():
                    idx2 += 1
                if text2 == graph1[idx1+1][0][0].lower():
                    idx1 += 1

            graph.append(edges1)
            idx1 += 1
            idx2 += 1

        # TODO: merge two nodes with multiple edges
        elif len(edges1) > 1 and len(edges2) > 1:
            if DEBUG:
                log.debug("case:  m:m")
            graph.append(edges1)
            idx1 += 1
            idx2 += 1

        elif len(edges1) == 1:
            if DEBUG:
                log.debug("case:  1:m")
            
            text1 = edges1[0][0]
            text2s = [edge[0] for edge in edges2]

            text2next = None
            if idx2 + 1 < len(graph2):
                text2snext = [edge[0] for edge in graph2[idx2 + 1]]
                if len(text2snext) == 1:
                    text2next = graph2[idx2 + 1][0][0]
           
            if text1 in text2s:
                graph.append(edges2)
                idx2 += 1
                if text1 != text2next:
                    idx1 += 1
            else:
                graph.append(edges1)
                idx1 += 1
                idx2 += 1

        elif len(edges2) == 1:
            if DEBUG:
                log.debug("case:  m:1")

            text2 = edges2[0][0]
            text1s = [edge[0] for edge in edges1]

            text1next = None
            if idx1 + 1 < len(graph1):
                text1snext = [edge[0] for edge in graph1[idx1 + 1]]
                if len(text1snext) == 1:
                    text1next = graph1[idx1 + 1][0][0]
           
            if text2 in text1s:
                graph.append(edges1)
                idx1 += 1
                if text2 != text1next:
                    idx2 += 1
            else:
                graph.append(edges1)
                idx1 += 1
                idx2 += 1

        else:
            if DEBUG:
                log.debug("case:  0:0")
            idx1 += 1
            idx2 += 1

        if DEBUG:
            log.debug("added: {}".format(graph[-1]))

    return format_plf_from_edges(graph)

def format_plf_from_edges(graph):
    line = ''
    for edges in graph:
        line += '('
        for text, weight, length in edges:
            line += "('{}',{},{}),".format(text, weight, length)
        line += '),'
    return '(' + line + ')'
