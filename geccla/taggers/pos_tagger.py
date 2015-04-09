#!/usr/bin/python

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import config
import cmd

from logger import log


class StanfordPOSTagger():

    def __init__(self, threads=None):
        self.tagger_dir = config.TOOLS.STANFORD_TAGGER_DIR
        self.separator = '|'
        self.threads = threads or config.THREADS

    def tag_file(self, tok_file, pos_file=None, lazy=True):
        if pos_file is None:
            pos_file = tok_file + '.pos'
        ann_file = pos_file + '.ann' 

        if lazy and os.path.exists(pos_file):
            log.info("tagging skipped because file {} exists".format(pos_file))
            return pos_file
            
        log.info("tagging file {} into {}".format(tok_file, pos_file))

        command = "java -mx1025m -cp {0}/stanford-postagger.jar: " \
            "edu.stanford.nlp.tagger.maxent.MaxentTagger " \
            "-model {0}/models/english-left3words-distsim.tagger " \
            "-sentenceDelimiter newline -tokenize false -tagSeparator \"{3}\" " \
            "-textFile {1} -nthreads {4} 2> /dev/null > {2}" \
            .format(self.tagger_dir, tok_file, ann_file, self.separator, 
                    self.threads)
        cmd.run(command)

        self.__extract_pos_tags_in_file(ann_file, pos_file)
        os.remove(ann_file)
        return pos_file

    def __extract_pos_tags_in_file(self, ann_file, pos_file):
        log.debug("extracting tags from file {} into {}".format(ann_file, pos_file))

        pos_io = open(pos_file, 'w+')
        with open(ann_file) as ann_io:
            for line in ann_io:
                poses = [ann.split(self.separator)[-1]
                         for ann in line.strip().split()]
                pos_io.write(' '.join(poses) + "\n")
        pos_io.close()
        return pos_file


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print "usage: {} input_file output_file".format(sys.argv[0])
        exit()

    tagger = StanfordPOSTagger()
    tagger.tag_file(sys.argv[1], sys.argv[2])
