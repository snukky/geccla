#!/usr/bin/python

import os
import sys
import argparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../geccla')))

from prediction.plf import join_plf_lines


def main():
    if '-h' in sys.argv or '--help' in sys.argv:
        print "usage: {} file1.plf file2.plf [file3.plf ...]".format(__file__)
        exit()

    plf_files = [open(file, 'r') for file in sys.argv[1:]]
    
    for idx, line in enumerate(plf_files[0]):
        for file in plf_files[1:]:
            line = join_plf_lines(line, file.next(), idx)
        print line

    for file in plf_files:
        file.close()
        

if __name__ == '__main__':
    main()
