import os
import sys
import re

sys.path.insert(0, os.path.dirname(__file__))

from confusion_set import ConfusionSet


ARTORDET_CONFUSION_SET = ConfusionSet('a,the,')


def normalize_indef_articles(text_file, nrm_file):
    nrm_io = open(nrm_file, 'w+')
    with open(text_file) as text_io:
        for line in text_io:
            nrm_io.write(re.sub(r"\bAn\b", r"A", 
                         re.sub(r"\ban\b", r"a", line)))
    nrm_io.close()
    return nrm_file

def restore_indef_articles(input_file, output_file):
    output_io = open(output_file, 'w+')
    with open(input_file) as input_io:
        for line in input_io:
            sents = [restore_indef_articles(sent) 
                     for sent in line.strip().split("\t")]
            output_io.write("\t".join(sents) + "\n")
    output_io.close()
    return output_file

def restore_indef_articles_in_sent(sent):
    words = sent.split()

    if len(words) < 2:
        return sent

    for i in range(len(words)-1):
        if words[i] == 'a' or words[i] == 'A':
            sec_word_after = words[i+2] if i < len(words)-2 else None
            if 'an' == guess_indef_article(words[i+1], sec_word_after):
                words[i] = 'an' if words[i] == 'a' else 'An'

    return ' '.join(words)

def guess_indef_article(word_after, sec_word_after=None):
    word = word_after or ''
    if sec_word_after and re.match(r'(?:\'|"|&).*', word_after):
        word = sec_word_after

    if re.match(r'(?:uni|use|one|once|usu|eur|hous).*', word):
        return 'a'
    elif re.match(r'(?:18|80|hou|hon|mba|x-r|mp3|mp4|rpg|nba|lcd|xbo|rfid).*|[aeiou].*', word):
        return 'an'
    return 'a'
