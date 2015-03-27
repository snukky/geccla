import os
import sys
import codecs
import difflib

sys.path.insert(0, os.path.dirname(__file__))

import cmd
import config

from logger import log


TOK_CONVERTERS = {
    'moses-nltk': 
        '{moses}/tokenizer/detokenizer.perl -l en | {tok}' \
        .format(moses=config.TOOLS.MOSES_DIR, tok=config.TOOLS.NLTK_TOKENIZER),
    'nltk-moses': 
        '{detok} | {moses}/tokenizer/tokenizer.perl' \
        .format(moses=config.TOOLS.MOSES_DIR, detok=config.TOOLS.NLTK_DETOKENIZER),
    'moses': 
        '{moses}/tokenizer/tokenizer.perl -l en' \
        .format(moses=config.TOOLS.MOSES_DIR)
}

QUOTES = ('"', '``', "''")


def restore_file_tok(text_file, orig_file, 
                     quotes=False, convert=None, clean=False):
    if convert:
        pretok_file = text_file + '.' + convert + '.' + str(os.getpid())
        cmd.run("cat {0} | {1} > {2}".format(
            text_file, TOK_CONVERTERS[convert], pretok_file))
        text_io = codecs.open(pretok_file, 'r', encoding='utf8')
    else:
        text_io = codecs.open(text_file, 'r', encoding='utf8')

    orig_io = codecs.open(orig_file, 'r', encoding='utf8')

    for line in text_io:
        orig_line = orig_file.next()

        result = restore_sentence_tok(line.strip(), orig_line.strip(), quotes)
        yield result.encode('utf8', 'replace')
        
    text_io.close()
    orig_io.close()

    if convert and clean:
        os.remove(pretok_file)

def restore_sentence_tok(sent, orig_sent, quotes=False):
    log.debug(u'toks: {}'.format(sent).encode('utf8', 'replace'))
    log.debug(u'orig: {}'.format(orig_sent).encode('utf8', 'replace'))

    toks = sent.split()
    orig_toks = orig_sent.split()

    matcher = difflib.SequenceMatcher(None, toks, orig_toks)
    new_toks = []
     
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag != 'equal':
            log.debug(u"  {}: ({},{}) '{}' -> ({},{}) '{}'" \
                .format(tag, 
                        i1, i2, ' '.join(toks[i1:i2]), 
                        j1, j2, ' '.join(orig_toks[j1:j2])) \
                .encode('utf8', 'replace'))

        if tag == 'equal':
            new_toks += orig_toks[j1:j2]

        elif tag == 'replace':
            ctok = ''.join(toks[i1:i2])
            orig_ctok = ''.join(orig_toks[j1:j2])

            if quotes:
                if ctok in QUOTES and orig_ctok in QUOTES:
                    new_toks += orig_toks[j1:j2]
                    continue
                elif toks[i1:i2][0] in QUOTES and orig_toks[j1:j2][0] in QUOTES:
                    toks[i1] = orig_toks[j1]
                elif i2-i1 > 1 and toks[i1:i2][1] in QUOTES and orig_toks[j1:j2][0] in QUOTES:
                    toks[i1+1] = orig_toks[j1]
                elif j2-j1 > 1 and toks[i1:i2][0] in QUOTES and orig_toks[j1:j2][1] in QUOTES:
                    toks[i1] = orig_toks[j1+1]
                elif i2-i1 > 1 and j2-j1 > 1 and toks[i1:i2][1] in QUOTES and orig_toks[j1:j2][1] in QUOTES:
                    toks[i1+1] = orig_toks[j1+1]

            if ctok == orig_ctok :
                new_toks += orig_toks[j1:j2]
            else:
                new_toks += toks[i1:i2]

        elif tag == 'delete':
            new_toks += toks[i1:i2]

        elif tag == 'insert':
            pass
    
    new_sent = ' '.join(new_toks)
    log.debug('    : {}'.format(new_sent))
    return new_sent
