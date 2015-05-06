import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from confusion_set import ConfusionSet
from difflib import SequenceMatcher


class BasicFinder():

    def __init__(self, conf_set):
        self.confusion_set = ConfusionSet(conf_set) 

    def find_confusion_words(self, corpus, greedy=True, nulls=False):
        with open(corpus) as corpus_io:
            for s, line in enumerate(corpus_io):
                err_toks, edits = self.parse_corpus_line(line)
                added = False

                for i, err in enumerate(err_toks):
                    if (i,i+1) in edits:
                        cor = edits[(i,i+1)][1]
                        if greedy or self.confusion_set.include(cor):
                            yield (s, i, i+1, err, cor)
                            added = True
                    elif (i,i) in edits and (greedy or self.confusion_set.include_null()):
                        cor = edits[(i,i)][1]
                        yield (s, i, i, '<null>', cor)
                        added = False
                    elif self.confusion_set.include(err):
                        yield (s, i, i+1, err, err)
                        added = True
                    elif nulls and not added:
                        yield (s, i, i, '<null>', '<null>')
                        added = False
                    else:
                        added = False

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
                if self.confusion_set.include(err_tok) and self.confusion_set.include(cor_tok):
                    edits[(i1, i2)] = (err_tok, cor_tok)
            elif tag == 'insert':
                if self.confusion_set.include(cor_tok):
                    edits[(i1, i2)] = ('<null>', cor_tok)
            elif tag == 'delete':
                if self.confusion_set.include(err_tok):
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
