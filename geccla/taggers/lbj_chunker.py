#!/usr/bin/python

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import config

from collections import OrderedDict
from cmd import wc


class LBJChunker():
    
    CHUNKS = 'ADJP ADVP CONJP INTJ LST NP PP PRT SBAR UCP VP'.split(' ')

    POSES = '$ `` \'\' , -LRB- -RRB- . : CC CD DT EX FW IN JJ JJR JJS LS MD ' \
        'NN NNP NNPS NNS PDT POS PRP PRP$ RB RBR RBS RP SYM TO UH VB VBD ' \
        'VBG VBN VBP VBZ WDT WP WP$ WRB #'.split(' ')

    def __init__(self):
        self.chunker_cmd = config.TOOLS.LBJ_CHUNKER
        self.parallel_cmd = config.TOOLS.PARALLEL

    def chunks_and_pos_tags(self, file):
        with open(self.__raw_chunks_and_pos_tags(file)) as file_io:
            for line in file_io:
                yield self.__parse_chunks(line) 

    def __parse_chunks(self, line):
        chunks = OrderedDict()
        
        i = 0
        j = 0
        chunk = {'words': [], 'pos': []}

        for tok in line.strip().split():
            if self.__is_chunk_start(tok):
                if chunk['words']:
                    chunk['i'] = i
                    chunk['j'] = j
                    chunks[ (i,j) ] = chunk
                    i = j
                    chunk = {'words': [], 'pos': []}
                chunk['chunk'] = tok[1:]
            elif self.__is_pos(tok):
                chunk['pos'].append(tok[1:])
            elif self.__is_word(tok):
                chunk['words'].append(tok[:-1])
                j += 1
            elif self.__is_chunk_end(tok):
                chunk['i'] = i
                chunk['j'] = j
                chunks[ (i,j) ] = chunk
                i = j
                chunk = {'words': [], 'pos': []}
            else:
                print >> sys.stderr, "Unrecognized token: {0}".format(tok)
        if chunk['words']:
            chunk['i'] = i
            chunk['j'] = j
            chunks[ (i,j) ] = chunk

        return Chunks(chunks)

    def __is_chunk_start(self, tok):
        return tok[0] == '[' and tok[1:] in LBJChunker.CHUNKS

    def __is_chunk_end(self, tok):
        return tok == ']'

    def __is_pos(self, tok):
        return tok[0] == '(' and tok[1:] in LBJChunker.POSES

    def __is_word(self, tok):
        return tok[-1] == ')' and len(tok) > 1

    def __raw_chunks_and_pos_tags(self, file):
        outfile = file + '.chunks'

        if not os.path.isfile(outfile) or wc(file) != wc(outfile):
            os.system("cat {0} | {1} {2} > {3}".format(file, \
                self.parallel_cmd, self.chunker_cmd, outfile))
        
        n1 = wc(file) 
        n2 = wc(outfile) 
        assert n1 == n2, 'File {0} has {1} sentences and {2} chunks'.format(file, n1, n2)

        return '{0}.chunks'.format(file)


class Chunks():
    def __init__(self, chunks={}):
        self.chunks = chunks
        self.words = self.__words()
        self.pos = self.__pos_tags()

    def get_chunk_by_word_idx(self, idx):
        if self.__idx_out_of_range(idx):
            return None
        for (i, j), chunk in self.chunks.iteritems():
            if idx >= i and idx < j:
                return chunk
        return None

    def get_n_words_after_chunk(self, idx, n):
        if self.__idx_out_of_range(idx):
            return None
        for (i, j), chunk in self.chunks.iteritems():
            if idx >= i and idx < j:
                words_with_afterwords = self.words + ([None]*n)
                return words_with_afterwords[j:j+n]
        return None

    def is_NP_starting_at(self, idx):
        if self.__idx_out_of_range(idx):
            return None
        for (i, j), chunk in self.chunks.iteritems():
            if i == idx and 'chunk' in chunk and chunk['chunk'] == 'NP':
                return True
            if i > idx:
                return False
        return False

    def is_NP_ending_at(self, idx):
        if self.__idx_out_of_range(idx):
            return None
        for (i, j), chunk in self.chunks.iteritems():
            if j == idx and 'chunk' in chunk and chunk['chunk'] == 'NP':
                return True
            if j > idx:
                return False
        return False

    def __idx_out_of_range(self, idx):
        return idx < 0 or idx > len(self.words) - 1

    def __str__(self):
        txt = ' '.join(self.words) + "\n"
        for pos, chunk in self.chunks.iteritems():
            txt += "  {0}: ".format(pos)
            if 'chunk' in chunk:
                txt += "chunk: '{0}', ".format(chunk['chunk'])
            if 'words' in chunk:
                txt += "words: '{0}', ".format(' '.join(chunk['words']))
            if 'pos' in chunk:
                txt += "pos: '{0}'".format(' '.join(chunk['pos']))
            txt += "\n"
        return txt

    def __words(self):
        return [word for chunk in self.chunks.values() for word in chunk['words']]

    def __pos_tags(self):
        return [pos for chunk in self.chunks.values() for pos in chunk['pos']]


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "usage: python {} input_file".format(sys.argv[0])
        exit()

    chunker = LBJChunker()
    for chunks in chunker.chunks_and_pos_tags(sys.argv[1]):
        print chunks
