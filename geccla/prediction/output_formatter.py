import os
import sys
import re

sys.path.insert(0, os.path.dirname(__file__))

from prediction import parse_pred_file
from prediction import iterate_text_confs_and_preds
from prediction import get_best_prediction

from preprocess.letter_case import restore_sentence_case

from confusion_set import ConfusionSet
from logger import log


class OutputFormatter():
    
    def __init__(self, conf_set):
        self.confusion_set = ConfusionSet(conf_set)

    def text_output(self, text_file, cnfs_file, pred_file, format, 
                                 threshold, difference, 
                                 restore_tok=True):
        
        preds = parse_pred_file(pred_file, format, self.confusion_set)

        for n, text, data in iterate_text_confs_and_preds(text_file, cnfs_file, preds):
            log.debug("{n}: {txt}".format(n=n, txt=text))

            yield self.__format_sentence(text.split(), data, 
                                         threshold, difference)

    def __format_sentence(self, sent, data, thr=None, dif=None):
        tokens = sent.split()

        for i, j, err, _, answers in data:
            pred = get_best_prediction(err, answers, thr, dif)
    
            real_err = ' '.join(tokens[i:j])
            if not self.confusion_set.include(real_err):
                log.warn("  shift error ({},{}) {}: {}".format(i, j, real_err,
                    '^'.join(tokens)))

            if err.lower() != pred.lower():
                log.debug("  ({},{}) {} -> {}".format(i, j, err, pred))

                if pred == '<null>':
                    pred = ''

                if i == j:
                    pred += ' ' + tokens[i]
                tokens[i] = pred
    
        new_sent = re.sub(r'\s\s+' , ' ', ' '.join(tokens))
        return restore_sentence_case(sent, new_sent)
