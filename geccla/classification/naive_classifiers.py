import os
import sys
import re

sys.path.insert(0, os.path.dirname(__file__))

import cmd
import config

from confusion_set import ConfusionSet
from logger import log


class MajorityClassClassifier():
    def __init__(self, conf_set):
        self.conf_set = ConfusionSet(conf_set)

    def train(self, model_file, data_file):
        counts = {num:0 for num in xrange(1, self.conf_set.size() + 1)}
        with open(data_file) as data_io:
            for line in data_io:
                label = int(line.split()[0])
                counts[label] += 1

        majority_label = max(counts, key=counts.get)
        log.info("majority label: {}".format(majority_label))

        with open(model_file, 'w+') as model_io:
            model_io.write("{}\n".format(majority_label))

    def predict(self, model_file, data_file, pred_file):
        with open(model_file) as model_io:
            pred = int(model_io.readline().strip())

        with open(pred_file, 'w+') as pred_io:
            nums = map(str, xrange(1, self.conf_set.size() + 1))
            pred_io.write("labels {}".format(' '.join(nums)))
            
            answers = ['0.0'] * self.conf_set.size()
            answers[pred-1] = '1.0'

            pred_line = "\n{} {}".format(pred, ' '.join(answers))
            for i in xrange(cmd.wc(data_file)):
                pred_io.write(pred_line)


class PerfectClassifier():
    def __init__(self, conf_set):
        self.conf_set = ConfusionSet(conf_set)

    def train(self, model_file, data_file=None):
        with open(model_file, 'w+') as model_io:
            model_io.write("fake")

    def predict(self, model_file, data_file, pred_file):
        with open(pred_file, 'w+') as pred_io:
            nums = map(str, xrange(1, self.conf_set.size() + 1))
            pred_io.write("labels {}".format(' '.join(nums)))
           
            with open(data_file) as data_io:
                for line in data_io:
                    pred = int(line.split()[0])
                    answers = ['0.0'] * self.conf_set.size()
                    answers[pred-1] = '1.0'

                    pred_line = "\n{} {}".format(pred, ' '.join(answers))
                    pred_io.write(pred_line)
