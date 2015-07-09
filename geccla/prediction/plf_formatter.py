import os
import sys
import re

sys.path.insert(0, os.path.dirname(__file__))

from logger import log

PRECISION = 5


class PLFFormatter():
    
    def __init__(self, debug=False):
        self.debug = debug
        self.with_comma = True

        self.PLF_FORMAT_METHODS = {
            'plf':      self.format_all_alternatives,
            'plf-best': self.format_best_alternatives,
        }

    def format_plf_sentence(self, sent, data, 
                                  thr=None, dif=None, 
                                  format='plf'):
        """ 
        Creates output sentence in Python Lattice Format with all alternative
        answers for which the classifier gives non-zero probability. 
        Threshold and difference values are not taken into account.
        """
        edges = []
        tokens = sent.split()
        changes = 0

        for i, token in enumerate(tokens):
            current_data = filter(lambda d: d[0] == i, data)

            if current_data and i != len(tokens) - 1:
                for i, j, err, _, answers in current_data:

                    if self.debug:
                        log.debug("  ({},{}) {} -> ???".format(i, j, err))
                        log.debug("  answers: {}".format(answers))

                    plf_method = self.PLF_FORMAT_METHODS[format]
                    alts = plf_method(err, tokens[j], answers, thr, dif)

                    if alts:
                        log.debug("  plf: {}".format(alts))
                        edges.append(alts)
                        changes += 1
                        if i == j:
                            edges.append("('{}',1.0,1)".format(token))
                    else:
                        edges.append("('{}',1.0,1)".format(token))

            else:
                edges.append("('{}',1.0,1)".format(token))

        output = ''
        if self.with_comma:
            output = ''.join(["({},),".format(e) for e in edges])
        else:
            output = ','.join(["({})".format(e) for e in edges])

        if self.debug:
            log.debug("output: {}".format(output))

        return '(' + output + ')', changes
    
    def format_all_alternatives(self, tok, nexttok, answers,
                                      thr=None, dif=None):
        alternatives = []
        cln_answers = self.__clean_answers(tok, answers, thr)

        for i, (tok, prob) in enumerate(cln_answers.iteritems()):
            alternatives.append(self.__plf_alternative(tok, nexttok, prob))

        if len(cln_answers) == 1 and alternatives[-1].endswith(',2)'):
            return '' 

        return ','.join(alternatives)

    def format_best_alternatives(self, tok, nexttok, answers,
                                       thr=None, dif=None):
        alternatives = []
        best_pred = max(answers.iterkeys(), key=(lambda k: answers[k]))
        best_prob = round(answers[best_pred], PRECISION)
    
        if thr and best_prob and best_prob < thr:
            best_pred = tok

            if self.debug:
                log.debug("  threshold too low for '{}' -> '{}'" \
                    .format(tok, best_pred))

        if best_pred.lower() != tok.lower():
            alternatives.append(self.__plf_alternative(tok, nexttok, 1.0 - best_prob))
            alternatives.append(self.__plf_alternative(best_pred, nexttok, best_prob))
        
        return ','.join(alternatives)

    def __clean_answers(self, tok, answers, thr=0.0):
        sum_probs = sum(answers.values())
        cln_answers = {}

        for tok, prob in answers.iteritems():
            round_prob = round(prob / sum_probs, PRECISION)
            if round_prob <= thr:
                continue
            cln_answers[tok] = round_prob

        rest = 1.0 - sum(cln_answers.values())
        if tok.lower() in cln_answers:
            cln_answers[tok.lower()] += rest
        else:
            for ans in cln_answers:
                cln_answers[ans] += rest / float(len(cln_answers))

        return cln_answers

    def __plf_alternative(self, tok, nexttok, prob):
        if tok == '' or tok == '<null>':
            text = nexttok
            size = 2
        else: 
            text = tok
            size = 1
        if prob == 1.0:
            return "('{}',1.0,{})".format(text, size)
        return "('{}',{:.5f},{})".format(text, prob, size)


