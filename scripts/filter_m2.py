#!/usr/bin/python

import sys
import argparse
import re

DEBUG = False


def main():
    global DEBUG

    args = parse_user_arguments()
    DEBUG = args.debug
    categories = args.pattern.strip().split(',')

    for sent, anns in parse_m2_file(sys.stdin):
        if not anns:
            print format_m2_sent(sent)
            continue
        
        if args.correct:
            sent, anns = insert_corrections(sent, anns, categories)
        else:
            anns = filter(lambda ann: ann[2] in categories, anns)
        print format_m2_sent(sent, anns)

def insert_corrections(sent, anns, categories=[]):
    debug("sent: {}".format(sent))
    toks = sent.split()

    for (i, j, cat, cor, tail) in anns:
        err = ' '.join(toks[i:j])
        debug("  ({}, {}) '{}' -> '{}' /{}".format(i, j, err, cor, cat))
        
        if i > len(toks) - 1 or j > len(toks) - 1:
            debug("  index i/j out of range")
            continue

        if cat in categories:
            if not toks[i].startswith("ANN;;;"):
                toks[i] = "ANN;;;{};;;{};;;{};;;{};;;{}" \
                    .format(toks[i], j-i, cat, cor, tail).replace(' ', '^^^')
            else:
                print >> sys.stderr, "succesive annot. at index {}".format(i)
                print >> sys.stderr, "sent: {}".format(sent)
            continue

        if not err:
            if i == 0:
                toks[0] = cor + ' ' + toks[0]
            else:
                toks[i-1] = toks[i-1] + ' ' + cor
        elif not cor:
            for k in xrange(i, j):
                toks[k] = ''
        else:
            toks[i] = cor
            for k in xrange(i+1, j):
                toks[k] = ''
            
    new_toks = re.sub(' +',' ',' '.join(toks)).split()
    new_anns = []

    for i, tok in enumerate(new_toks):
        if tok.startswith("ANN;;;"):
            word, dif, cat, cor, tail = tok[6:].replace('^^^', ' ').strip().split(';;;')
            new_anns.append( (i, i+int(dif), cat, cor, tail) )
            new_toks[i] = word

    new_sent = ' '.join(new_toks)
    debug("news: {}".format(new_sent))

    return new_sent, new_anns
        
def format_m2_sent(sent, anns=[]):
    txt = "S {0}\n".format(sent)
    for i, j, _, _, tail in anns:
        txt += "A {0} {1}|||{2}\n".format(i, j, tail)
    return txt

def parse_m2_file(file):
    sent = None
    anns = []
    for line in file:
        if line.startswith('S '):
            sent = line.strip()[2:]
        elif line.startswith('A '):
            fields = line.strip()[2:].split('|||')
            i, j = map(int, fields[0].split())
            # (i, j, category, correction, tail)
            anns.append( (i, j, fields[1], fields[2], '|||'.join(fields[1:])) )
        else:
            yield sent, anns
            sent = None
            anns = []
    if sent:
        yield sent, anns


def debug(msg):
    if DEBUG:
        print >> sys.stderr, msg

def parse_user_arguments():
    parser = argparse.ArgumentParser(description="Extract selected error "
        "categories from M2 file")

    parser.add_argument('-p', '--pattern', required=True,
        help="comma-separated list of error categories")
    parser.add_argument('-5', '--five_errors', action='store_true', 
        help="five error categories from CoNLL 2013")
    parser.add_argument('-c', '--correct', action='store_true',
        help="correct other error categories")
    parser.add_argument('--debug', action='store_true',
        help="show debug")

    args = parser.parse_args()
    if args.five_errors:
        args.pattern = 'ArtOrDet,Nn,Prep,SVA,Vform'
    return args

if __name__ == '__main__':
    main()
