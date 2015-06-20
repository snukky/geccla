#!/usr/bin/python

import argparse
import math
import random

from confusions.basic_finder import BasicFinder
from logger import log

import cmd

DEBUG_COUNTER = 100000


def main():
    args = parse_user_arguments()

    all_sents, err_sents, cor_sents = calculate_stats(args.input_file, args.confusion_set)
    to_del = num_of_sents_to_delete(args.error_rate, all_sents, len(err_sents))

    if not to_del:
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


def num_of_sents_to_delete(err_rate, num_of_sents, num_of_err_sents):
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
    log.debug("finding confusions...")

    idx = 0
    for s, i, j, err, cor in finder.find_confusion_words(file):
        idx += 1
        if err != cor:
            err_sents.append(s)
        if idx % DEBUG_COUNTER == 0:
            log.debug("[{}]".format(idx))

    num_of_sents = cmd.wc(file)
    err_sents_set = set(err_sents)
    cor_sents = [i for i in range(num_of_sents) if i not in err_sents_set]

    log.info("all sentences: {}".format(num_of_sents))
    log.info("sentences with error: {}".format(len(err_sents)))
    log.info("sentences no error: {}".format(len(cor_sents)))

    return num_of_sents, err_sents, cor_sents


def parse_user_arguments():
    parser = argparse.ArgumentParser(description="Delete sentences from M2" \
        " file to ensure desired error rate.")

    parser.add_argument('input_file', help="text file")
    parser.add_argument('-c', '--confusion-set', type=str, required=True,
        help="confusion set as comma-separated list of words")
    parser.add_argument('-e', '--error-rate', type=float,
        help="desired annotation-to-sentence rate")
    parser.add_argument('--shuffle', action='store_true',
        help="remove random sentences")
    return parser.parse_args()

if __name__ == '__main__':
    main()
