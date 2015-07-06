#!/usr/bin/python

import os
import sys
import argparse
import shutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../geccla')))

from FAdo.fa import *
from FAdo.reex import *

from prediction.plf import parse_plf_line


def main():
    args = parse_user_args()
    
    dot_io = sys.stdout
    if args.pdf:
        pid = os.getpid()
        dot_io = open("{}.dot".format(pid), 'w+')

    for line in convert_plf_to_dot(args.plf_input):
        dot_io.write(line + "\n")

    if args.pdf:
        dot_io.close()
        os.popen("dot -Tps2 {0}.dot -o {0}.ps | ps2pdf {0}.ps".format(pid))
        shutil.move("{}.pdf".format(pid), args.pdf)
        os.remove("{}.dot".format(pid))
        os.remove("{}.ps".format(pid))


def convert_plf_to_dot(plf_io):
    for line in plf_io:
        if not line.strip():
            continue
        dfa = DFA()
        dfa.addState(0)
        dfa.setInitial(0)
        for idx, edges in enumerate(parse_plf_line(line)):
            dfa.addState(idx + 1)
            for text, weight, length in edges:
                label = "{} ({})".format(text, weight)
                dfa.addTransition(idx, label, idx + length)
        yield dfa.dotFormat()


def parse_user_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('plf_input', type=argparse.FileType('r'), 
        default=sys.stdin, nargs='?', help="input PLF file (default STDIN)")
    parser.add_argument('--pdf', type=str, help="output PDF file")

    return parser.parse_args()

if __name__ == '__main__':
    main()
