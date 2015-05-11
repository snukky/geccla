#!/usr/bin/python

import os
import sys
import argparse 
import difflib
import re

from collections import Counter


def main():
    args = parse_user_arguments()
    
    generator = ConfusionSetsGenerator(sys.stdin, args.min_err_count, 
        args.min_cor_count)
    csets = generator.generate_confusion_sets(args.words.split(','), 
                                              args.threshold,
                                              args.min_freq,
                                              args.allow_spaces_in_word,
                                              args.allow_outside_words)

    for word, conf_words in csets:
        print "{}\t{}".format(word, ','.join(conf_words))


class ConfusionSetsGenerator():

    def __init__(self, corpus_file, min_err_count=5, min_cor_count=3):
        self.freqs = Counter()
        self.conf_words = {}
        self.null_confs = None

        self.extract_confusion_words(corpus_file, min_err_count, min_cor_count)

    def print_all_edits(self):
        for a, words in self.conf_words.iteritems():
            for b, freq in words.iteritems():
                print "{}\t{}\t{}".format(a, b, freq)
        for b, freq in self.null_confs.iteritems():
                print " \t{}\t{}".format(b, freq)

    def generate_confusion_sets(self, words, threshold, 
                                      min_freq = 0.01,
                                      allow_spaces_in_word=False, 
                                      allow_outside_words=False):

        debug("generating confusion sets for words: '{}'".format(words))

        counts = {w: self.freqs[w] for w in words if w in self.freqs}

        for word in sorted(counts, key=counts.__getitem__, reverse=True):
            if word not in self.conf_words:
                continue
            
            cset = self.conf_words[word]
            if not allow_spaces_in_word:
                cset = {wrd: frq for wrd, frq in cset.iteritems() if ' ' not in wrd}
            if not allow_outside_words:
                all_words = words + [word]
                cset = {wrd: frq for wrd, frq in cset.iteritems() if wrd in all_words}
            cset = self.__cut_cset(cset, threshold, min_freq)

            debug("set for '{}':\t{}".format(word, self.__printable_cset(cset)))

            yield word, sorted(cset, key=cset.__getitem__, reverse=True)

    def __cut_cset(self, cset, frac_thr=0.99, min_freq=0.01):
        output = {}
        csum = float(sum(cset.values()))
        incfrac = 0.0

        for word in sorted(cset, key=cset.__getitem__, reverse=True):
            frac = cset[word] / csum
            if frac >= min_freq:
                output[word] = frac
            incfrac += frac
            if incfrac >= frac_thr:
                break

        return output
    
    def __printable_cset(self, cset):
        pairs = ["{} ({:.4f})".format(wrd, cset[wrd]) 
                 for wrd in sorted(cset, key=cset.__getitem__, reverse=True)]
        return ' '.join(pairs)

    def extract_confusion_words(self, corpus_file, min_err_freq, min_cor_freq):
        debug("extracting confusion words")
        sets = {}

        for i, line in enumerate(corpus_file):
            err_sent, cor_sent = line.strip().split("\t")
            edits = self.__extract_edits(err_sent.lower().split(), 
                                         cor_sent.lower().split())
            self.__update_confusion_sets(sets, self.freqs, edits)

        for err in sorted(self.freqs, key=self.freqs.__getitem__, reverse=True):
            if self.freqs[err] < min_err_freq:
                break

            cors = { cor: freq 
                     for cor, freq in sets[err].iteritems()
                         if freq >= min_cor_freq }
            if err == '':
                self.null_confs = Counter(cors)
                continue
            if len(cors):
                self.conf_words[err] = cors

        del sets

    def __extract_edits(self, err_toks, cor_toks):
        matcher = difflib.SequenceMatcher(None, err_toks, cor_toks)
        edits = []
         
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag != 'equal':
                edit = (' '.join(err_toks[i1:i2]), ' '.join(cor_toks[j1:j2]))
                edits.append(edit)
    
        return edits

    def __update_confusion_sets(self, sets, freqs, edits):
        for err, cor in edits:
            if err in sets:
                sets[err][cor] += 1
            else:
                sets[err] = Counter([cor])
            freqs[err] += 1

def debug(msg):
    print >> sys.stderr, msg

def parse_user_arguments():
    parser = argparse.ArgumentParser(description="Generates confusion sets" \
        " from parallel corpus given at STDIN.")

    parser.add_argument("-e", "--min-err-count", type=int, default=5,
        help="minimum count of erroneous word")
    parser.add_argument("-c", "--min-cor-count", type=int, default=2,
        help="minimum count of corrected word")

    parser.add_argument("-w", "--words", type=str,
        help="comma-separated list of words")
    parser.add_argument("-t", "--threshold", type=float, default=0.9,
        help="threshold (default 0.9)")

    parser.add_argument("-f", "--min-freq", type=float, default=0.02,
        help="minimum frequency for each word in confusion set")
    parser.add_argument("--allow-spaces-in-word", action='store_true',
        help="")
    parser.add_argument("--allow-outside-words", action='store_true',
        help="")

    return parser.parse_args()

if __name__ == '__main__':
    main()
