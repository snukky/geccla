#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import codecs
import difflib

sys.path.insert(0, os.path.dirname(__file__))

from logger import log


def restore_file_case(text_file, orig_file, debug=False):
    text_io = codecs.open(text_file, 'r', encoding='utf8')
    orig_io = codecs.open(orig_file, 'r', encoding='utf8')

    for line in text_io:
        orig_line = orig_io.next()

        result = restore_sentence_case(line.strip(), orig_line.strip(), debug)

        assert result.lower() == line.strip().lower(), \
            "Case restoration changed a sentence!\n{}\n{}" \
            .format(line.strip(), result)

        yield result.encode('utf8', 'replace')
        
    text_io.close()
    orig_io.close()

def restore_sentence_case(sent, orig_sent, debug=False):
    if debug and sent != orig_sent:
        log.debug(u'toks: {}'.format(sent).encode('utf8', 'replace'))
        log.debug(u'orig: {}'.format(orig_sent).encode('utf8', 'replace'))

    toks = sent.split()
    orig_toks = orig_sent.split()

    lc_toks = [tok.lower() for tok in toks]
    lc_orig_toks = [tok.lower() for tok in orig_toks]

    matcher = difflib.SequenceMatcher(None, lc_toks, lc_orig_toks)
    new_toks = []
     
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if debug and tag != 'equal' and sent != orig_sent:
            log.debug(u"  {}: ({},{}) '{}' -> ({},{}) '{}'" \
                .format(tag, 
                        i1, i2, ' '.join(toks[i1:i2]), 
                        j1, j2, ' '.join(orig_toks[j1:j2])) \
                .encode('utf8', 'replace'))

        if tag == 'equal':
            new_toks += orig_toks[j1:j2]

        elif tag == 'replace':
            word = ' '.join(toks[i1:i2])
            orig_word = ' '.join(orig_toks[j1:j2])
            new_toks += [restore_word_case(word, orig_word)]

        elif tag == 'delete':
            if i1 == 0:
                tmp = toks[i1:i2]
                if is_capitalized(orig_toks[0]):
                    orig_toks[0] = orig_toks[0].lower()
                    tmp[0] = tmp[0].capitalize()
                elif is_uppercased(orig_toks[0]):
                    tmp[0] = tmp[0].capitalize()
                new_toks += tmp
            else:
                new_toks += toks[i1:i2]

        elif tag == 'insert':
            if i1 == 0 and is_capitalized(orig_toks[j1]) and \
                    is_lowercased(orig_toks[j2]):
                orig_toks[j2] = orig_toks[j2].capitalize()

        #log.debug('    : {}'.format(' '.join(new_toks)))

    new_sent = ' '.join(new_toks)
    
    if debug and sent != orig_sent:
        log.debug("sent: {}".format(new_sent))

    return new_sent

def restore_word_case(tok, orig_tok):
    if tok.lower() == orig_tok.lower():
        return orig_tok

    if is_lowercased(orig_tok):
        return tok.lower()
    elif is_uppercased(orig_tok):
        return tok.upper()
    elif is_capitalized(orig_tok):
        return tok.capitalize()
    else:
        return tok

def is_lowercased(tok):
    return tok == tok.lower()

def is_uppercased(tok):
    return tok == tok.upper()

def is_capitalized(tok):
    return tok == tok.capitalize()

