import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from confusion_set import ConfusionSet
from difflib import SequenceMatcher

from logger import log


class BasicFinder():

    def __init__(self, conf_set, left_conf_set=None, train_mode=False):
        self.train_mode = train_mode
        self.confusion_set = ConfusionSet(conf_set) 
        if left_conf_set:
            self.left_conf_set = ConfusionSet(left_conf_set)
        else:
            self.left_conf_set = self.confusion_set
        
    def find_confusion_words(self, corpus, all_nulls=False):
        with open(corpus) as corpus_io:
            count = 0
            for s, line in enumerate(corpus_io):
                err_toks, edits = self.parse_corpus_line(line)
                added = False

                for i, err in enumerate(err_toks):
                    if (i,i+1) in edits:
                        cor = edits[(i,i+1)][1]
                        if self.confusion_set.include(cor):
                            yield (s, i, i+1, err, cor)
                            count += 1
                            added = True
                    elif (i,i) in edits and self.left_conf_set.include_null() and self.train_mode:
                        cor = edits[(i,i)][1]
                        yield (s, i, i, '<null>', cor)
                        count += 1
                        added = False
                    elif self.left_conf_set.include(err):
                        yield (s, i, i+1, err, err)
                        count += 1
                        added = True
                    elif all_nulls and not added:
                        yield (s, i, i, '<null>', '<null>')
                        count += 1
                        added = False
                    else:
                        added = False
            log.info("found {} examples of confusion words".format(count))

    def parse_corpus_line(self, line):
        if "\t" in line:
            err_toks, cor_toks = [sent.split() for sent in line.strip().split("\t")]
            edits = self.find_edits(err_toks, cor_toks)
        else:
            err_toks = line.strip().split()
            edits = {}
        return (err_toks, edits)

    def find_edits(self, err_toks, cor_toks):
        matcher = SequenceMatcher(None, err_toks, cor_toks)
        edits = {}
     
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            err_tok = ' '.join(err_toks[i1:i2])
            cor_tok = ' '.join(cor_toks[j1:j2])
            
            if tag == 'replace':
                if self.left_conf_set.include(err_tok) and self.confusion_set.include(cor_tok):
                    edits[(i1, i2)] = (err_tok, cor_tok)
            elif tag == 'insert':
                if self.confusion_set.include(cor_tok):
                    edits[(i1, i2)] = ('<null>', cor_tok)
            elif tag == 'delete':
                if self.left_conf_set.include(err_tok):
                    edits[(i1, i2)] = (err_tok, '<null>')

        return edits

    def correction_from_edits(self, idx, edits, default=None):
        cor = default
        if (i,i+1) in edits:
            cor = edits[(i,i+1)][1]
        elif (i,i) in edits:
            cor = edits[(i,i)][1]
        if cor == '':
            cor = '<null>'
        return cor
