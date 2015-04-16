#!/usr/bin/python

import os
import sys
import math
import argparse


def main():
    args = parse_user_arguments()
    split_m2(args.m2_file, args.num_of_parts, args.part_prefix)


def split_m2(m2_file, num_of_parts, part_prefix=None):
    parts = format_part_endings(num_of_parts)
    if not part_prefix:
        part_prefix = m2_file
    
    with open(m2_file) as m2_io:
        num_of_sents = sum(1 for line in m2_io if line.startswith("S "))
    part_size = math.ceil(num_of_sents / float(num_of_parts))

    part_io = open('{}.{}'.format(part_prefix, parts.pop(0)), 'w+')
    s = 0
    with open(m2_file) as m2_io:
        for line in m2_io:
            if line.startswith("S "):
                s += 1
            part_io.write(line)
            if s >= part_size and line.strip() == '':
                part_io.close()
                part_io = open('{}.{}'.format(part_prefix, parts.pop(0)), 'w+')
                s = 0
    part_io.close()

def format_part_endings(size):
    return ["{:0>2d}".format(n) for n in xrange(size)]


def parse_user_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('m2_file', type=str, help="file to split")
    parser.add_argument('-n', '--num-of-parts', type=int, required=True,
        help="number of parts")
    parser.add_argument('-p', '--part-prefix', type=str,
        help="prefix for each part file")
    return parser.parse_args()

if __name__ == '__main__':
      main()
