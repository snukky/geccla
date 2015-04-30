#!/usr/bin/python

import os
import sys
import math
import argparse


def main():
    args = parse_user_arguments()
    split_m2(args.m2_file, args.number, args.prefix, args.suffix)


def split_m2(m2_file, number, prefix=None, suffix=''):
    parts = format_part_endings(number)
    if not prefix:
        prefix = m2_file + '.'
    
    with open(m2_file) as m2_io:
        num_of_sents = sum(1 for line in m2_io if line.startswith("S "))
    part_size = math.ceil(num_of_sents / float(number))

    part_name = format_part_name(prefix, suffix, parts.pop(0))
    part_io = open(part_name, 'w+')

    s = 0
    with open(m2_file) as m2_io:
        for line in m2_io:
            if line.startswith("S "):
                s += 1
            part_io.write(line)
            if s >= part_size and line.strip() == '':
                part_io.close()
                part_name = format_part_name(prefix, suffix, parts.pop(0))
                part_io = open(part_name, 'w+')
                s = 0
    part_io.close()

def format_part_name(prefix, suffix, num):
    return '{}{}{}'.format(prefix, num, suffix)

def format_part_endings(size):
    return ["{:0>2d}".format(n) for n in xrange(size)]


def parse_user_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('m2_file', type=str, help="file to split")
    parser.add_argument('-n', '--number', type=int, required=True,
        help="number of parts")
    parser.add_argument('-p', '--prefix', type=str, default='',
        help="prefix for each part file")
    parser.add_argument('-s', '--suffix', type=str, default='',
        help="suffix for each part file")
    return parser.parse_args()

if __name__ == '__main__':
      main()
