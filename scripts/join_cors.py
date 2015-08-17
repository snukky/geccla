#!/usr/bin/python

import os
import sys
import argparse

from difflib import SequenceMatcher


def main():
    if '-h' in sys.argv or '--help' in sys.argv:
        print "usage: {} file1.cor file2.cor [file3.cor ...]".format(__file__)
        exit()

    cor_files = [open(file, 'r') for file in sys.argv[1:]]
    
    for idx, line in enumerate(cor_files[0]):
        for file in cor_files[1:]:
            line = join_txt_lines(line, file.next())
        print line

    for file in cor_files:
        file.close()
        
def join_txt_lines(err_sent, cor_sent):
    err_toks = err_sent.split()
    cor_toks = cor_sent.split()

    matcher = SequenceMatcher(None, err_toks, cor_toks)
    new_toks = []
 
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        err_txt = ' '.join(err_toks[i1:i2])
        cor_txt = ' '.join(cor_toks[j1:j2])
        
        if tag == 'replace':
            new_toks.append(cor_txt)
        elif tag == 'insert':
            new_toks.append(cor_txt)
        elif tag == 'delete':
            pass
        else:
            new_toks.append(err_txt)
            
    return ' '.join(new_toks) 


if __name__ == '__main__':
    main()
