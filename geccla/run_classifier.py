#!/usr/bin/python

import argparse

from classification.multi_classifier import MultiClassifier
from classification import ALGORITHMS


def main():
    args = parse_user_arguments()

    classifier = MultiClassifier(args.confusion_set)
    if args.train:
        classifier.train(args.algorithm, 
                         args.model_file, args.data_file,
                         args.options)
    else:
        classifier.run(args.algorithm, 
                       args.model_file, args.data_file, args.pred_file,
                       args.options)
        

def parse_user_arguments():
    parser = argparse.ArgumentParser()
    
    parser.add_argument('model_file', type=str, help="model file")
    parser.add_argument('data_file', type=str, help="data file")

    req = parser.add_argument_group("required arguments")
    req.add_argument('-a', '--algorithm', required=True, choices=ALGORITHMS,
        help="classification algorithm")
    req.add_argument('-c', '--confusion-set', required=True,
        help="confusion set as comma-separated list of words")

    parser.add_argument('-t', '--train', action='store_true', 
        help="train classifier")
    parser.add_argument('-p', '--pred-file', type=str,
        help="output file with classifier predictions")
    parser.add_argument('-o', '--options', type=str,
        help="custom options for classifier")
    
    args = parser.parse_args()
    if not args.train and not args.pred_file:
        raise ArgumentError("argument --pred-file is required while running "
            "a classifier")
    return args


if __name__ == '__main__':
    main()
