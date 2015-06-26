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
    
    OUTPUT_FORMATS = ['txt', 'plf']
    PRECISION = 5

    def __init__(self, conf_set, restore_case=True, debug=False):
        self.confusion_set = ConfusionSet(conf_set)
        self.restore_case = restore_case
        self.debug = debug

    def text_output(self, text_file, cnfs_file, pred_file, 
                          format, 
                          threshold, difference):
        self.format_output(text_file, cnfs_file, pred_file, format, 
            threshold, difference, "txt")

    def format_output(self, text_file, cnfs_file, pred_file, 
                            format, 
                            threshold, difference,
                            output_format="txt"):

        log.info("injecting predictions from file {} with params t={} d={}" \
            .format(pred_file, threshold, difference))
        
        preds = parse_pred_file(pred_file, format, self.confusion_set)
        changes = 0

        for n, text, data in iterate_text_confs_and_preds(text_file, cnfs_file, preds):
            if self.debug:
                self.__show_text_debug(text, n)

            if output_format == "txt":
                format_method = self.__format_txt_sentence
            elif output_format == "plf":
                format_method = self.__format_plf_sentence
            else:
                log.error("output format {} not supported!".format(output_format))

            new_text, c = format_method(text, data, threshold, difference)
            changes += c
            yield new_text

        if self.debug:
            log.debug("number of changes: {}".format(changes))

    def __format_txt_sentence(self, sent, data, thr=None, dif=None):
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

    def __format_plf_sentence(self, sent, data, thr=None, dif=None):
        """ 
        Creates output sentence in Python Lattice Format with all
        alternative answers to which classifier gave non-zero probability.
        Threshold and difference are not taken into account.
        """
        output = ''
        tokens = sent.split()
        changes = 0

        for i, token in enumerate(tokens):
            current_data = filter(lambda d: d[0] == i, data)

            if current_data and i != len(tokens) - 1:
                for i, j, err, _, answers in current_data:

                    alts = self.__plf_alternatives(token, tokens[i+1], answers)
                    if alts:
                        output += "({}),".format(alts)

                    if self.debug:
                        pred = get_best_prediction(err, answers, thr, dif)
                        log.debug("  ({},{}) {} -> {}".format(i, j, err, pred))
                        log.debug("  answers: {}".format(answers))
                        log.debug("  plf: {}".format(alts))

            else:
                output += "(('{}',1.0,1),),".format(token)

        return ('(' + output + ')', changes)
    
    def __plf_alternatives(self, tok, nexttok, answers):
        alternatives = ''
        cln_answers = self.__clean_answers(answers)

        rest = 1.0 - sum(cln_answers.values())
        for i, (tok, prob) in enumerate(cln_answers.iteritems()):
            if i == 0:
                prob += rest
            alternatives += self.__plf_alternative(tok, nexttok, prob)

        if len(cln_answers) == 1 and alternatives.endswith('2),'):
            return ''

        return alternatives

    def __clean_answers(self, answers):
        sum_probs = sum(answers.values())
        cln_answers = {}

        for tok, prob in answers.iteritems():
            round_prob = round(prob / sum_probs, OutputFormatter.PRECISION)
            if round_prob == 0.0:
                continue
            cln_answers[tok] = round_prob

        return cln_answers

    def __plf_alternative(self, tok, nexttok, prob):
        if tok == '':
            text = nexttok
            size = 2
        else: 
            text = tok
            size = 1
        return "('{}',{},{}),".format(text, prob, size)



    def __show_text_debug(self, text, n=0):
        tokens = text.split()
        debug_toks = [str(elem) 
                      for pair in zip(tokens, xrange(len(tokens)))
                      for elem in reversed(pair)]
        log.debug("{}: {}".format(n, '_'.join(debug_toks)))
