import os
import sys
import re

sys.path.insert(0, os.path.dirname(__file__))

import cmd
import config

from confusion_set import ConfusionSet
from logger import log

from classification.naive_classifiers import MajorityClassClassifier
from classification.naive_classifiers import PerfectClassifier


class MultiClassifier():
    def __init__(self, conf_set):
        self.confusion_set = ConfusionSet(conf_set)
        self.num_classes = self.confusion_set.size()

    def run(self, algorithm, model_file, data_file, pred_file, options=''):
        log.info("running model: {}".format(model_file))

        if options is None or not options.strip():
            options = self.__default_options(algorithm)

        if not os.path.exists(model_file):
            log.error("model file does not exist: {}".format(model_file))
        if not os.path.exists(data_file):
            log.error("data file does not exists: {}".format(data_file))

        if 'snow' == algorithm:
            cmd.run("{bin} -test -I {data} -F {model} -v max -R {pred} {opts}" \
                .format(bin=config.CLASSIFIERS.SNOW_BIN, 
                        data=data_file, model=model_file, pred=pred_file, 
                        opts=options))

        elif 'vw' == algorithm:
            reduced_options = re.sub(r'--(oaa|ect|wap)\s+\d+ ', '', options)

            cmd.run("{bin} -t -d {data} -i {model} -c -r {pred} {opts}" \
                .format(bin=config.CLASSIFIERS.VW_BIN, 
                        data=data_file, model=model_file, pred=pred_file, 
                        opts=reduced_options))

        elif 'liblinear' == algorithm:
            cmd.run("{dir}/predict -b 1 {data} {model} {pred}" \
                .format(dir=config.CLASSIFIERS.LIBLINEAR_DIR, 
                        data=data_file, model=model_file, pred=pred_file))

        elif 'maxent' == algorithm:
            cmd.run("{bin} -testFile {data} -loadClassifier {model} {opts} > {pred}" \
                .format(bin=config.CLASSIFIERS.MAXENT_BIN, 
                        data=data_file, model=model_file, pred=pred_file, 
                        opts=options))

        elif 'majority' == algorithm:
            MajorityClassClassifier(self.confusion_set) \
                .predict(model_file, data_file, pred_file)

        elif 'perfect' == algorithm:
            PerfectClassifier(self.confusion_set) \
                .predict(model_file, data_file, pred_file)

        else:
            log.error("not supported algorithm: {}".format(algorithm))

    def train(self, algorithm, model_file, data_file, options=''):
        log.info("training model: {}".format(model_file))

        if not options or not options.strip():
            options = self.__default_options(algorithm)

        if not os.path.exists(data_file):
            log.error("data file does not exists: {}".format(data_file))

        if 'snow' == algorithm:
            cmd.run("{bin} -train -I {data} -F {model} {opts}" \
                .format(bin=config.CLASSIFIERS.SNOW_BIN, 
                        data=data_file, model=model_file,
                        opts=options))
            
        elif 'vw' == algorithm:
            cmd.run("{bin} -d {data} -f {model} -c {opts}" \
                .format(bin=config.CLASSIFIERS.VW_BIN, 
                        data=data_file, model=model_file,
                        opts=options))

        elif 'liblinear' == algorithm:
            cmd.run("{bin}/train {opts} {data} {model}" \
                .format(bin=config.CLASSIFIERS.LIBLINEAR_DIR, 
                        data=data_file, model=model_file,
                        opts=options))

        elif 'maxent' == algorithm:
            cmd.run("{bin} -trainFile {data} -serializeTo {model} -prop {data}.prop {opts}" \
                .format(bin=config.CLASSIFIERS.MAXENT_BIN, 
                        data=data_file, model=model_file,
                        opts=options))

        elif 'majority' == algorithm:
            MajorityClassClassifier(self.confusion_set).train(model_file, data_file)

        elif 'perfect' == algorithm:
            PerfectClassifier(self.confusion_set).train(model_file, data_file)

        else:
            log.error("not supported algorithm: {}".format(algorithm))

    def __default_options(self, algorithm):
        if 'snow' == algorithm:
            return " -P 0.001,2.0:0-{}".format(self.num_classes)
        elif 'vw' == algorithm:
            return " --oaa {} --loss_function quantile".format(self.num_classes)
        elif 'liblinear' == algorithm:
            return " -M 0 -s 7 -c 1"
        return ""
