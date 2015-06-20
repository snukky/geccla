#!/usr/bin/python

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import config

from logger import log


class WordClassTagger:

    def __init__(self, dictionary=None):
        self.unknown_wc = '?'
        self.dictionary = dictionary or config.FILES.WORD_CLASSES
        self.__load_dictionary()

    def tag(self, tokens):
        return [self.dic.get(tok.lower(), self.unknown_wc) for tok in tokens]

    def tag_file(self, tok_file, awc_file=None, lazy=True):
        if awc_file is None:
            awc_file = tok_file + '.awc'

        if lazy and os.path.exists(awc_file):
            log.info("tagging skipped because file {} exists".format(awc_file))
            return awc_file

        log.info("tagging file {} into {}".format(tok_file, awc_file))
        output = open(awc_file, 'w+')

        with open(tok_file) as input:
            for line in input:
                output.write(' '.join(self.tag(line.strip().split())) + "\n")

        output.close()
        return awc_file

    def __load_dictionary(self):
        log.info("loading dictionary {}...".format(self.dictionary))
        self.dic = {}
        with open(self.dictionary) as f:
            for line in f:
                word, tag = line.split()[:2]
                self.dic[word] = tag
                if word.find('&apos;') != -1:
                    self.dic[word.replace('&apos;', "'")] = tag
                if word.find('&quot;') != -1:
                    self.dic[word.replace('&quot;', '"')] = tag


if __name__ == '__main__':
    tagger = WordClassTagger()
    for line in sys.stdin:
        print ' '.join(tagger.tag(line.strip().split()))
