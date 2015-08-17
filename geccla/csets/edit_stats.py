import os
import sys
import difflib

from collections import Counter
import cPickle as pickle

sys.path.insert(0, os.path.dirname(__file__))

import csets

from logger import log


class EditStats():
    
    def __init__(self, corpus, 
                       force_new=False,
                       min_err=5, min_cor=3, 
                       no_spaces=False,
                       no_nulls=False,
                       remove_dots=True):

        self.corpus = corpus
        self.min_err = min_err
        self.min_cor = min_cor
        self.no_spaces = no_spaces
        self.no_nulls = no_nulls
        self.remove_dots = remove_dots

        self.all_freqs = Counter()
        self.freqs = Counter()
        self.edits = {}
        self.nulls = {}
        self.pp = csets.readable_dict

        edits, freqs = self.__extract_edits_and_freqs(corpus, force_new)
        self.__init_edits_info(edits, freqs)

    def info(self):
        print "<null>\t{}\t{}".format(self.freqs[''], self.pp(self.nulls))
        for word, freq in csets.sort_dict(self.freqs):
            if word not in self.edits or word == '':
                continue
            print "{}\t{}\t{}".format(word, freq, self.pp(self.edits[word]))

    
    def expand_edit_sets(self, sum_freqs=True, with_nulls=True):
        log.info("expanding edit sets")
        new_edits = {}

        for err, cors in self.edits.iteritems():
            exp_cors = []

            for cor, freq in cors.iteritems():
                if cor not in self.edits or cor == '':
                    continue
                
                cor_div = freq / float(self.freqs[cor])
                subcors = { subc: int(subf * cor_div) 
                            for subc, subf in self.edits[cor].iteritems() }

                if not with_nulls:
                    subcors = { subc: subf 
                                for subc, subf in subcors.iteritems()
                                if subc != '' }
                
                exp_cors.append( Counter(subcors) )

            if sum_freqs:
                if not with_nulls:
                    cors = { subc: subf 
                             for subc, subf in cors.iteritems()
                             if subc != '' }
                exp_cors.append( Counter(cors) )

            new_edits[err] = sum(exp_cors, Counter())

        self.edits = new_edits

    def pair_edit_sets(self):
        log.debug("pairing edit sets")
        pairs = {}

        for err, cors in self.edits.iteritems():
            pairs[err] = {}
            for cor, freq in cors.iteritems():
                pairs[err][cor] = freq
                if cor in self.edits:
                    pairs[err][cor] += self.edits[cor].get(err, 0)
                if cor not in pairs:
                    pairs[cor] = {}
                pairs[cor][err] = pairs[err][cor]

        self.edits = pairs

    def __extract_edits_and_freqs(self, corpus, force=False):
        edits = {}
        freqs = Counter()
        dumpf = corpus + '.edits.pkl'

        if not force and os.path.exists(dumpf):
            log.info("loading edits from file '{}'".format(dumpf))
            with open(dumpf) as file:
                edits = pickle.load(file)
                freqs = pickle.load(file)
            return edits, freqs
        
        log.info("extracing edit statistics from '{}' corpus".format(corpus))
        with open(corpus, 'r') as corpus_io:
            for i, line in enumerate(corpus_io):
                err_sent, cor_sent = line.strip().split("\t")
                sent_edits = self.__extract_edits(err_sent, cor_sent)

                for err, cor in sent_edits:
                    if self.no_nulls and (err == '' or cor == ''):
                        continue
                    if self.remove_dots:
                        if len(err) > 2 and err.endswith('.'):
                            err = err[:-1]
                        if len(cor) > 2 and cor.endswith('.'):
                            cor = cor[:-1]

                    if err in edits:
                        edits[err][cor] += 1
                    else:
                        edits[err] = Counter([cor])
                    freqs[err] += 1
        log.info("found {} unique words/phrases".format(len(freqs)))

        if not os.path.exists(dumpf):
            log.info("dumping edits to file '{}'".format(dumpf))
            with open(dumpf, 'wb') as file:
                pickle.dump(edits, file)
                pickle.dump(freqs, file)
            
        return edits, freqs
    
    def __init_edits_info(self, edits, freqs):
        self.all_freqs = freqs

        self.freqs = {}
        self.edits = {}
        self.nulls = {}

        for err, err_freq in csets.sort_dict(freqs):
            if err_freq < self.min_err:
                break

            cors = { cor: freq for cor, freq in edits[err].iteritems()
                               if freq >= self.min_cor }

            if self.no_spaces:
                if ' ' in err:
                    continue
                cors = { cor: freq for cor, freq in cors.iteritems()
                         if ' ' not in cor }

            if cors:
                if err == '':
                    self.nulls = cors
                else:
                    self.edits[err] = cors
                self.freqs[err] = sum(cors.values())

        log.info("edit statistics initialized")

    def __extract_edits(self, err_sent, cor_sent):
        err_toks = err_sent.lower().split()
        cor_toks = cor_sent.lower().split()

        matcher = difflib.SequenceMatcher(None, err_toks, cor_toks)
        edits = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag != 'equal':
                edit = (' '.join(err_toks[i1:i2]), ' '.join(cor_toks[j1:j2]))
                edits.append(edit)
    
        return edits
