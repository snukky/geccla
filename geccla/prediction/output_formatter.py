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


def inject_predictions(conf_set, format, 
                       text_file, cnfs_file, pred_file,
                       threshold, difference,
                       output_file):

    formatter = OutputFormatter(conf_set)
    with open(output_file, 'w+') as output:
        for line in formatter.text_output(text_file, cnfs_file, pred_file, 
                                          format, threshold, difference):
            output.write(line + "\n")


class OutputFormatter():
    
    def __init__(self, conf_set, restore_case=True):
        self.confusion_set = ConfusionSet(conf_set)
        self.restore_case = restore_case

    def text_output(self, text_file, cnfs_file, pred_file, 
                          format, 
                          threshold, difference,
                          debug=False):
        
        preds = parse_pred_file(pred_file, format, self.confusion_set)

        for n, text, data in iterate_text_confs_and_preds(text_file, cnfs_file, preds):
            if debug:
                log.debug("{n}: {txt}".format(n=n, txt=text))

            yield self.__format_sentence(text, data, threshold, difference, 
                                         n=n, debug=debug)

    def __format_sentence(self, sent, data, 
                                thr=None, dif=None, 
                                n=None, debug=False):
        tokens = sent.split()

        for i, j, err, _, answers in data:
            pred = get_best_prediction(err, answers, thr, dif)
    
            real_err = ' '.join(tokens[i:j])
            if not self.confusion_set.include(real_err):
                debug_toks = [str(elem) 
                              for pair in zip(tokens, xrange(len(tokens)))
                              for elem in reversed(pair)]
                log.warn("shift error {} ({},{}) {}: {}".format(n, i, j, 
                    real_err, '_'.join(debug_toks)))

            if err.lower() != pred.lower():
                if debug:
                    log.debug("  ({},{}) {} -> {}".format(i, j, err, pred))

                if pred == '<null>':
                    pred = ''

                if i == j:
                    pred += ' ' + tokens[i]
                tokens[i] = pred
    
        new_sent = re.sub(r'\s\s+' , ' ', ' '.join(tokens))

        if self.restore_case:
            return restore_sentence_case(new_sent, sent, debug=False)
        return new_sent
