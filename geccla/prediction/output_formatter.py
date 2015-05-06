import os
import sys
import re

sys.path.insert(0, os.path.dirname(__file__))

from prediction import parse_pred_file
from prediction import iterate_text_confs_and_preds
from prediction import get_best_prediction

from preprocess.letter_case import restore_sentence_case
from preprocess.artordets import restore_indef_articles_in_sent

from confusion_set import ConfusionSet
from logger import log


def inject_predictions(conf_set, format, 
                       text_file, cnfs_file, pred_file,
                       threshold, difference,
                       output_file,
                       restore_articles=False):

    formatter = OutputFormatter(conf_set)
    with open(output_file, 'w+') as output:
        for line in formatter.text_output(text_file, cnfs_file, pred_file, 
                                          format, threshold, difference):
            if restore_articles:
                line = restore_indef_articles_in_sent(line)
            output.write(line + "\n")


class OutputFormatter():
    
    def __init__(self, conf_set, restore_case=True, debug=False):
        self.confusion_set = ConfusionSet(conf_set)
        self.restore_case = restore_case
        self.debug = debug

    def text_output(self, text_file, cnfs_file, pred_file, 
                          format, 
                          threshold, difference):
        
        preds = parse_pred_file(pred_file, format, self.confusion_set)

        log.info("injecting predictions from file {} with params t={} d={}" \
            .format(pred_file, threshold, difference))
        changes = 0

        for n, text, data in iterate_text_confs_and_preds(text_file, cnfs_file, preds):
            if self.debug:
                tokens = text.split()
                debug_toks = [str(elem) 
                              for pair in zip(tokens, xrange(len(tokens)))
                              for elem in reversed(pair)]
                log.debug("{}: {}".format(n, '_'.join(debug_toks)))

            new_text, c = self.__format_sentence(text, data, threshold, difference)
            changes += c
            yield new_text

        if self.debug:
            log.debug("number of changes: {}".format(changes))

    def __format_sentence(self, sent, data, thr=None, dif=None):
        tokens = sent.split()
        changes = 0

        for i, j, err, _, answers in data:
            pred = get_best_prediction(err, answers, thr, dif)
            
            real_err = ' '.join(tokens[i:j])
            if not self.confusion_set.include(real_err):
                log.warn("  shift error: ({},{}) '{}'".format(i, j, real_err))


            if err.lower() != pred.lower():
                changes += 1

                if self.debug:
                    log.debug("  ({},{}) {} -> {}".format(i, j, err, pred))
                    log.debug("  answers: {}".format(answers))

                if pred == '<null>':
                    pred = ''
                if i == j:
                    pred += ' ' + tokens[i]
                tokens[i] = pred
    
        new_sent = re.sub(r'\s\s+' , ' ', ' '.join(tokens))
        if self.restore_case and new_sent != sent:
            new_sent = restore_sentence_case(new_sent, sent, debug=False)

            if self.debug:
                log.debug("  changes: {}".format(changes))

        return (new_sent, changes)
