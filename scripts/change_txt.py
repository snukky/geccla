#!/usr/bin/python

import os
import sys
import argparse
import math
import random

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../geccla')))

from confusions.basic_finder import BasicFinder
from logger import log

import cmd

DEBUG_COUNTER = 100000


def main():
    args = parse_user_arguments()

    all_sents, err_sents, cor_sents, _ = \
        calculate_stats(args.input_file, args.confusion_set)
    to_del = sents_to_delete(args.error_rate, all_sents, len(err_sents))

    if not to_del:
        if args.error_rate is None:
            err_rate = len(err_sents) / float(all_sents) if all_sents else 0.0
            print "error rate:", err_rate
        exit()

    if args.shuffle:
        random.shuffle(cor_sents)
    del_sents = set(cor_sents[:to_del])

    with open(args.input_file) as input_io:
        for idx, line in enumerate(input_io):
            if idx not in del_sents:
                print line,
            if (idx + 1) % DEBUG_COUNTER == 0:
                log.debug("[{}]".format(idx + 1))


def sents_to_delete(err_rate, num_of_sents, num_of_err_sents):
    if not num_of_sents or not num_of_err_sents:
        return 0

    current_err_rate = num_of_err_sents / float(num_of_sents)
    log.debug("current annotation rate: {}".format(current_err_rate))

    if not err_rate:
        return 0

    log.debug("desired error rate: {}".format(err_rate))

    if err_rate <= current_err_rate:
        log.debug("decreasing of error rate is not supported")
        return 0

    num_to_delete = num_of_sents - int(math.floor(num_of_err_sents / err_rate))
    log.debug("number of sentences to delete: {}".format(num_to_delete))

    return max(0, num_to_delete)

def calculate_stats(file, confset):
    finder = BasicFinder(confset, train_mode=True)

    err_sents = []
    cnf_sents = []
    log.debug("finding confusions...")

    idx = 0
    for s, i, j, err, cor in finder.find_confusion_words(file):
        idx += 1
        cnf_sents.append(s)
        if err != cor:
            err_sents.append(s)
        if idx % DEBUG_COUNTER == 0:
            log.debug("[{}]".format(idx))

    num_of_sents = cmd.wc(file)
    cnf_sents_set = set(cnf_sents)
    cln_sents = [i for i in range(num_of_sents) if i not in cnf_sents_set]
    err_sents_set = set(err_sents)
    cor_sents = [i for i in range(num_of_sents) if i not in err_sents_set
                                               and i in cnf_sents_set]

    log.info("all sentences: {}".format(num_of_sents))
    log.info("sentences with confusion words: {}".format(len(cnf_sents_set)))
    log.info("sentences without confusion words: {}".format(len(cln_sents)))
    log.info("sentences with errors: {}".format(len(err_sents_set)))
    log.info("sentences without errors: {}".format(len(cor_sents)))

    return len(cnf_sents_set), list(err_sents_set), cor_sents, cln_sents


def parse_user_arguments():
    parser = argparse.ArgumentParser(description="Delete sentences from " \
        " parallel file to ensure desired error rate.")

    parser.add_argument('input_file', help="text file")
    parser.add_argument('-c', '--confusion-set', type=str, required=True,
        help="confusion set as comma-separated list of words")
    parser.add_argument('-e', '--error-rate', type=float,
        help="desired rate of erroneous sentences to all sentences")
    parser.add_argument('--shuffle', action='store_true',
        help="remove random sentences")
    return parser.parse_args()

if __name__ == '__main__':
    main()
