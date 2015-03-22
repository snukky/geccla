import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from confusion_set import ConfusionSet
from confusions import parse_conf_line
from cmd import run_cmd, wc

from logger import log


FORMATS_NEEDED_NORMALIZATION = ['vw']


def iterate_confusions_with_predictions(cnfs_file, predictions, 
                                        threshold=None, difference=None,
                                        with_skipped=False):
    skip_by_thr, skip_by_dif, skip_by_both = 0, 0, 0

    with open(cnfs_file) as cnfs_io:
        for i, line in enumerate(cnfs_io):
            _, _, _, err, cor, _ = parse_conf_line(line)
            pred, confidence = find_best_answer(predictions[i])
            err, cor, pred = err.lower(), cor.lower(), pred.lower()

            skip = False

            if threshold and confidence:
                if confidence < threshold:
                    pred = err
                    skip_by_thr += 1
                    skip_by_both += 1
                    skip = True

            if difference and len(predictions[i]) > 1:
                values = sorted(predictions[i].values())
                if values[-1] - values[-2] < difference:
                    pred = err
                    skip_by_dif += 1
                    if not skip:
                        skip_by_both += 1

            if with_skipped:
                yield (err, cor, pred, (skip_by_thr, skip_by_dif, skip_by_both))
            else:
                yield (err, cor, pred)

def parse_pred_file(pred_file, format, conf_set, normalize=True):
    conf_set = ConfusionSet(conf_set)
    predictions = []

    if 'snow' == format:
        output = run_cmd("cat {0} | grep -a '^  Ex.*' | "
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

    elif 'libsvm' == format:
        with open(pred_file) as file:
            labels = None
            for i, line in enumerate(file):
                if i == 0:
                    labels = line.strip().split()[1:]
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
                answers = { fields[1]: float(fields[2].replace(',', '.')) }
                predictions.append(answers) 
    
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

    if normalize and format in FORMATS_NEEDED_NORMALIZATION:
        return normalize_predictions(predictions)
    return predictions

def __number_of_predictions(pred_file, format):
    num_of_lines = wc(pred_file)
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
    nrm_preds = []
    for answers in preds:
        nrm_preds.append({ word: __sigmoid(value) 
                           for word, value in answers.iteritems() })
    return nrm_preds

def __sigmoid(x):
    if x >= 0:
        return 1 / (1 + exp(-x))
    else:
        # if x is less than zero then z will be small, denom can't be
        # zero because it's 1+z.
        z = exp(x)
        return z / (1 + z)
