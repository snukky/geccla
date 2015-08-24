#!/usr/bin/python

import os
import sys
import re
import argparse
import math

from difflib import SequenceMatcher

VERBOSE = False


def main():
    args = parse_user_args()
    rm_files = []

    if args.m2:
        debug("parallelizing input M2 file")

        args.input_file = parallelize_m2_file(args.input_file)
        rm_files.append(args.input_file)

    if args.info:
        debug("calculating statistics")
        num_all, num_err, _ = calculate_statistics(args.input_file, 
                                                   args.confusion_set,
                                                   args.annotator)
        print num_err / float(num_all)
        
        if not args.no_clean:
            for file in rm_files:
                debug("removing temporary file: {}".format(file))
                os.remove(file)
        exit()

    if args.reference:
        debug("calculating error rate from reference data")

        if args.m2_reference:
            debug("parallelizing reference M2 file")

            args.reference = parallelize_m2_file(args.reference)
            rm_files.append(args.reference)

        num_all, num_err, _ = calculate_statistics(args.reference, 
                                                   args.confusion_set,
                                                   args.annotator)
        ref_rate = num_err / float(num_all)
        args.error_rate *= ref_rate

    sents_to_del = []
    if args.error_rate:
        debug("finding sentences to delete")

        sents_to_del = find_sentences_to_delete(args.input_file, 
                                                args.confusion_set, 
                                                args.error_rate)

    finder = ConfusionWordFinder(args.confusion_set, greedy=args.greedy, 
                                                     aa_edits=False,
                                                     debug=(VERBOSE > 1))
    debug("iterating confusion words")
    texts = finder.iterate_texts(args.input_file)
    
    for idx, (err_text, anns) in enumerate(texts):
        if idx in sents_to_del:
            continue

        if args.m2_output:
            print format_m2_entry(err_text, anns, category=args.category)
        else:
            cor_texts = apply_annotations(err_text, anns)
            print format_txt_line(err_text, cor_texts)

    if not args.no_clean:
        for file in rm_files:
            debug("removing temporary file: {}".format(file))
            os.remove(file)


def find_sentences_to_delete(txt_file, conf_set, err_rate, ann_id=0):
    num_all, num_err, cor_stats = calculate_statistics(txt_file, conf_set, ann_id)
    num_del = __find_edits_to_delete(err_rate, num_all, num_err)

    debug("number of edits to delete: {}".format(num_del))
    if not num_del:
        return set()
        
    del_sents = []
    for sent_id, num_edits in cor_stats.iteritems():
        if num_del <= 0:
            break
        num_del -= num_edits
        del_sents.append(sent_id)
    
    return set(del_sents)

def calculate_statistics(txt_file, conf_set, annotator=0):
    num_of_all = 0
    num_of_err = 0
    cor_stats = {}

    finder = ConfusionWordFinder(conf_set, greedy=False)

    idx = 0
    for _, cwords in finder.iterate_texts(txt_file):
        # FIXME: take into account all annotators?
        edit_types = [err.lower() == cor.lower() 
                      for _, _, err, cor in cwords[annotator]]

        num_err = edit_types.count(False)
        num_cor = edit_types.count(True)

        if num_cor > 0 and num_err == 0:
            cor_stats[idx] = num_cor

        num_of_all += len(edit_types)
        num_of_err += num_err
        idx += 1

    debug("all edits: {}".format(num_of_all))
    debug("AB edits: {}".format(num_of_err))
    debug("AA edits: {}".format(num_of_all - num_of_err))

    return num_of_all, num_of_err, cor_stats

def __find_edits_to_delete(err_rate, num_all, num_err):
    if num_all <= 0 or num_err <= 0:
        return 0

    old_rate = num_err / float(num_all)

    debug("current error rate: {}".format(old_rate))
    debug("desired error rate: {}".format(err_rate))

    if err_rate <= old_rate:
        debug("decreasing error rate is not supported!")
        return 0

    return max(0, num_all - int(math.floor(num_err / err_rate)))


def parallelize_m2_file(m2_file):
    txt_file = m2_file + '.parallel.tmp'

    if not os.path.exists(txt_file):
        with open(txt_file, 'w+') as txt_io:
            for text, anns in parse_m2_file(m2_file):
                cor_texts = apply_annotations(text, anns)
                txt_io.write("\t".join([text] + cor_texts) + "\n")

    return txt_file 

def parse_m2_file(m2_file, num_of_anns=None):
    """
    Iterates entries in M2 file generating tuples (text, [annotations, ...]) 
    where annotations are a list of (i, j, error, correction) tuples.
    Length of the second element in the base tuple is equal to the number of
    annotators.
    """
    if num_of_anns is None:
        num_of_anns = __count_annotators(m2_file)

    with open(m2_file) as m2_io:
        toks = []
        anns = [[] for _ in range(num_of_anns)]

        for line in m2_io:
            if line.startswith('S '):
                toks = line.strip()[2:].split()
            elif line.startswith('A '):
                fields = line.strip()[2:].split('|||')
                i, j = map(int, fields[0].split())
                
                err = ''
                if i >= 0 and j >= 0:
                    err = ' '.join(toks[i:j])
                cor = fields[2]

                ann_id = int(fields[-1])
                anns[ann_id].append( (i, j, err, cor) )
            else:
                yield ' '.join(toks), anns
                toks = []
                anns = [[] for _ in range(num_of_anns)]

        if toks:
            yield ' '.join(toks), anns

def __count_annotators(m2_file):
    num = os.popen("cat {} | grep '^A ' | sed -r " \
        "'s/.*\\|\\|\\|([0-9]+)$/\\1/' | sort -u | wc -l".format(m2_file)) \
        .read()
    return int(num.strip())


class ConfusionWordFinder():

    def __init__(self, conf_set, greedy=False, aa_edits=True, debug=False):
        self.conf_set = set([',' if cw == '<comma>' else cw 
                             for cw in conf_set.split(',')])
        self.greedy = greedy
        self.aa_edits = aa_edits
        self.debug = debug

    def iterate_texts(self, txt_file):
        with open(txt_file) as txt_io:
            for s, line in enumerate(txt_io):
                texts = line.strip().split("\t")

                err_toks = texts[0].split()
                anns = [self.find_confusion_words(err_toks, cor_text.split())
                        for cor_text in texts[1:]]

                if self.debug and any(len(cs) > 0 for cs in anns):
                    print >> sys.stderr, "text: {}".format(texts[0])
                    for ann_id, edits in enumerate(anns):
                        for i, j, err, cor in edits:
                            print >> sys.stderr, "  a{}: ({},{}) {} -> {}" \
                                .format(ann_id, i, j, err, cor)

                yield texts[0], anns 

    def find_confusion_words(self, err_toks, cor_toks):
        edits = self.find_edits(err_toks, cor_toks)
        cwords = []

        for i, err in enumerate(err_toks):
            if (i,i+1) in edits:
                cor = edits[(i,i+1)][1]
                cwords.append( (i, i+1, err, cor) )
            elif (i,i) in edits:
                cor = edits[(i,i)][1]
                cwords.append( (i, i, '', cor) )
            elif self.aa_edits and err.lower() in self.conf_set:
                cwords.append( (i, i+1, err, err) )

        return cwords 

    def find_edits(self, err_toks, cor_toks):
        matcher = SequenceMatcher(None, err_toks, cor_toks)
        edits = {}
     
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            err_tok = ' '.join(err_toks[i1:i2])
            cor_tok = ' '.join(cor_toks[j1:j2])
            
            if tag == 'replace':
                if self.greedy and (err_tok.lower() in self.conf_set \
                                    or cor_tok.lower() in self.conf_set):
                    edits[(i1, i2)] = (err_tok, cor_tok)

                elif err_tok.lower() in self.conf_set \
                        and cor_tok.lower() in self.conf_set:
                    edits[(i1, i2)] = (err_tok, cor_tok)

            elif tag == 'insert':
                if cor_tok.lower() in self.conf_set:
                    edits[(i1, i2)] = ('', cor_tok)

            elif tag == 'delete':
                if err_tok.lower() in self.conf_set:
                    edits[(i1, i2)] = (err_tok, '')
    
        return edits

def apply_annotations(text, anns):
    new_texts = []

    for edits in anns:
        toks = text.split()

        for (i, j, err, cor) in edits:
            if i < 0 or i > len(toks) - 1 or j < 0 or j > len(toks) - 1:
                continue

            if not err:
                if i == 0:
                    toks[0] = cor + ' ' + toks[0]
                else:
                    toks[i-1] = toks[i-1] + ' ' + cor
            elif not cor:
                for k in xrange(i, j):
                    toks[k] = ''
            else:
                toks[i] = cor
                for k in xrange(i+1, j):
                    toks[k] = ''
        
        new_texts.append( re.sub(' +', ' ', ' '.join(toks)) )
    return new_texts 

def format_m2_entry(text, anns, category='category'):
    entry = "S {}\n".format(text)
    for idx, edits in enumerate(anns):
        for i, j, _, cor in edits:
            entry += "A {i} {j}|||{cat}|||{cor}|||REQUIRED|||-NONE-|||{ann}\n" \
                .format(i=i, j=j, cat=category, cor=cor, ann=idx)
    return entry 

def format_txt_line(err_text, cor_texts, category=None):
    return "\t".join([err_text] + cor_texts)


def debug(msg):
    if VERBOSE:
        print >> sys.stderr, msg

def parse_user_args():
    parser = argparse.ArgumentParser()
    
    data = parser.add_argument_group("data arguments")
    data.add_argument('input_file', type=str,
        help="input file (.txt format by default)")

    data.add_argument('--m2', action='store_true',
        help="assume input is in M2 format")
    data.add_argument('--m2-output', action='store_true',
        help="print output in M2 format")

    base = parser.add_argument_group("base arguments")
    base.add_argument('-c', '--confusion-set', type=str, required=True,
        help="confusion set as comma-separated list of words")
    
    base.add_argument('-i', '--info', action='store_true',
        help="print error rate and exit")
    base.add_argument('-e', '--error-rate', type=float,
        help="desired error rate")
    base.add_argument('-a', '--annotator', type=int, default=0,
        help="chose annotator to calculate error rate")
    #base.add_argument('-m', '--multiplication', action='store_true',
        #help="use desired error rate as multiplication factor")
    #base.add_argument('-s', '--sentence-level', action='store_true',
        #help="work on sentence level instead of edits level")
    #base.add_argument('-r', '--random', action='store_true',
        #help="remove random sentences")
    base.add_argument('--reference', type=str,
        help="calculate an error rate from this data")
    base.add_argument('--m2-reference', action='store_true',
        help="assume reference corpus is in M2 format")

    filter = parser.add_argument_group("filter arguments")
    filter.add_argument('-f', '--filter', action='store_true',
        help="filter input data by confusion set")
    filter.add_argument('--category', type=str, default='CATEGORY',
        help="set error category name in M2 format")
    filter.add_argument('--greedy', action='store_true',
        help="keep edits that concern only one confusion word")

    parser.add_argument('-v', '--verbose', type=int, default=0,
        help="set level of verbosity")
    parser.add_argument('--no-clean', action='store_true',
        help="do not remove temporary files")

    args = parser.parse_args()

    global VERBOSE
    VERBOSE = args.verbose

    if args.reference and not args.error_rate:
        args.error_rate = 1.0

    if args.error_rate is not None and args.error_rate < 0.0:
        print "Error rate has to be greater than or equal to zero!"
        exit()

    return args

if __name__ == '__main__':
    main()
