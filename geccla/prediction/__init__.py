import os
import sys
import math

sys.path.insert(0, os.path.dirname(__file__))

import cmd

from confusion_set import ConfusionSet
from confusions import parse_conf_line

from logger import log


FORMATS_NEEDED_NORMALIZATION = ['vw', 'vwldf']


def iterate_text_confs_and_preds(text_file, cnfs_file, preds):
    text_io = open(text_file)
    cnfs_io = open(cnfs_file)

    n = 0
    m = 0
    cnfs_n, i, j, err, cor, _ = parse_conf_line(cnfs_io.readline())

    for line in text_io:
        tokens = line.strip().split()
        pred_data = []

        while cnfs_n == n:
            pred_data.append( (i, j, err, cor, preds[m]) )
            cnfs_n, i, j, err, cor, _ = parse_conf_line(cnfs_io.readline())
            m += 1
        
        yield (n, line.strip(), pred_data)
        n += 1

    text_io.close()
    cnfs_io.close()
    

def iterate_confs_and_preds(cnfs_file, preds, thr=None, dif=None, 
                            lowercase=False):
    with open(cnfs_file) as cnfs_io:
        for i, line in enumerate(cnfs_io):
            _, _, _, err, cor, _ = parse_conf_line(line)
            pred = get_best_prediction(err, preds[i], thr, dif)

            if lowercase:
                yield (err.lower(), cor.lower(), pred.lower())
            else:
                yield (err, cor, pred)

def get_best_prediction(err, answers, threshold=None, difference=None):
    pred, confidence = find_best_answer(answers)

    if threshold and confidence:
        if confidence < threshold:
            pred = err

    if difference and len(answers) > 1:
        values = sorted(answers.values())
        if values[-1] - values[-2] < difference:
            pred = err
    
    return pred 


def parse_pred_file(pred_file, format, conf_set):
    log.debug("parsing prediction file: {} ({})".format(pred_file, format))

    conf_set = ConfusionSet(conf_set)
    predictions = []

    if 'snow' == format:
        output = cmd.run("cat {0} | grep -a '^  Ex.*' | "
            "sed -r 's/.*Prediction - ([0-9]).*\\(([.0-9]+).*/\\1 \\2/'" \
            .format(pred_file))

        for row in output.strip().split('\n'):
            if not row:
                continue
            label, value = row.split()
            answers = { conf_set.num_label_to_word(label): float(value) }
            predictions.append(answers)

    elif 'vw' == format:
        with open(pred_file) as file:
            for line in file:
                answers = {}
                for elem in line.strip().split():
                    label, value = elem.split(':')
                    answers[conf_set.num_label_to_word(label, 1)] = float(value)
                predictions.append(answers)

    elif 'vwldf' == format:
        labels = conf_set.as_list()
        #log.warn(pred_file)

        with open(pred_file) as file:
            answers = {}
            idx = 0
            for line in file:
                #log.warn(line.strip())

                if line.strip():
                    label = labels[idx]
                    answers[label] = -1 * float(line.strip().split(':')[-1])
                    idx += 1
                else:
                    #log.warn("raw: {}".format(answers))
                    #nrm_answers = { word: __softmax(value, answers.values())
                                    #for word, value in answers.iteritems() }
                    #log.warn("nrm: {}".format(nrm_answers))
                    predictions.append(answers)
                    answers = {}
                    idx = 0

    elif 'libsvm' == format:
        with open(pred_file) as file:
            labels = None
            for i, line in enumerate(file):
                if i == 0:
                    labels = line.strip().split()[1:]
                    log.debug("LIBSVM labels: {}".format(' '.join(labels)))
                    continue
                fields = line.strip().split()
                values = fields[1:]
                answers = { conf_set.num_label_to_word(label, 1): float(value)
                            for label, value in zip(labels, values) }
                predictions.append(answers)

    elif 'maxent' == format:
        with open(pred_file) as file:
            for line in file:
                fields = line.strip().split()
                label = conf_set.num_label_to_word(fields[1], 1)
                value = float(fields[2].replace(',', '.'))
                predictions.append( {label: value} )
    
    elif 'bsvm' == format:
        with open(pred_file) as file:
            for line in file:
                label = int(line.strip())
                answers = { conf_set.num_label_to_word(label, 1): 1.0 }
                predictions.append(answers)

    else:
        log.error("format {} is not supported!".format(format))
    
    pred_length = len(predictions)
    pred_file_length = __number_of_predictions(pred_file, format)

    if pred_length == 0 or pred_length != pred_file_length:
        log.error("extraction of predictions failed! ({} != {})" \
            .format(pred_length, pred_file_length))

    if format in FORMATS_NEEDED_NORMALIZATION:
        return normalize_predictions(predictions)

    return predictions

def __number_of_predictions(pred_file, format):
    num_of_lines = cmd.wc(pred_file)
    if format == 'libsvm':
        return num_of_lines - 1
    return num_of_lines


def find_best_answer(answers):
    word = max(answers.iterkeys(), key=(lambda key: answers[key]))
    return (word, answers[word])

def sort_answers(answers):
    return [ (word, answers[word]) 
             for word in sorted(answers, key=answers.get, reverse=True) ]


def normalize_predictions(preds):
    log.info("sigmoid normalization of predictions")
    nrm_preds = []
    for answers in preds:
        nrm_preds.append({ word: __softmax(value, answers.values())
                           for word, value in answers.iteritems() })
        #nrm_preds.append({ word: __sigmoid(value) 
                           #for word, value in answers.iteritems() })
    return nrm_preds

def __sigmoid(x):
    if x >= 0:
        return 1 / (1 + math.exp(-x))
    else:
        # if x is less than zero then z will be small, denom can't be
        # zero because it's 1+z.
        z = math.exp(x)
        return z / (1 + z)

def __softmax(x, xs):
    return math.exp(x) / sum(math.exp(xx) for xx in xs)
