#!/usr/bin/python

import os
import sys
import argparse
import math
import random

DEBUG = True


def main():
    args = parse_user_arguments()

    num_to_skip = calculate_num_of_sents_to_delete(args.m2_file, args.error_rate)
    idxes_to_skip = get_sents_to_delete(args.m2_file, num_to_skip, args.shuffle)

    if not args.error_rate:
        return

    with open(args.m2_file) as m2_io:
        for idx, line in enumerate(m2_io):
            if idx in idxes_to_skip or (idx-1) in idxes_to_skip:
                continue
            print line,


def get_sents_to_delete(m2_file, to_delete, shuffle=False):
    if to_delete <= 0:
        return []

    sents_with_no_ann = []

    with open(m2_file) as m2_io:
        see_good_sent = False
        for idx, line in enumerate(m2_io):
            if line.startswith("S "):
                see_good_sent = True
            elif line.startswith("A "):
                see_good_sent = False
            else:
                if see_good_sent:
                    sents_with_no_ann.append(idx - 1)
                see_good_sent = False
    if shuffle:
        random.shuffle(sents_with_no_ann)
    return set(sents_with_no_ann[:to_delete+1])
    
def calculate_num_of_sents_to_delete(m2_file, error_rate):
    num_of_sents = int(run_cmd("grep '^S ' {} | wc -l".format(m2_file)))
    num_of_annos = int(run_cmd("grep '^A ' {} | wc -l".format(m2_file)))

    if num_of_sents <= 0:
        debug("warning: M2 file is empty?")
        return 0

    ann_rate = num_of_annos / float(num_of_sents)
    debug("current annotation rate: {}".format(ann_rate))

    if not error_rate:
        return 0

    debug("desired annotation rate: {}".format(error_rate))

    if error_rate <= ann_rate:
        debug("decreasing of annotation rate is not supported")
        return 0

    num_to_delete = num_of_sents - int(math.floor(num_of_annos / error_rate))
    debug("number of sentences to delete: {}".format(num_to_delete))

    return max(0, num_to_delete)


def run_cmd(cmd):
    return os.popen(cmd).read().strip()

def debug(msg):
    if DEBUG:
        print >> sys.stderr, msg


def parse_user_arguments():
    parser = argparse.ArgumentParser(description="Delete sentences from M2" \
        " file to ensure desired error rate.")

    parser.add_argument('m2_file', help="M2 file")
    parser.add_argument('-e', '--error-rate', type=float,
        help="desired annotation-to-sentence rate")
    parser.add_argument('--shuffle', action='store_true',
        help="remove random sentences")
    return parser.parse_args()

if __name__ == '__main__':
    main()
