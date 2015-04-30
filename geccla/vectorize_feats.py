#!/usr/bin/python

import argparse

from vectorization.feature_vectorizer import FeatureVectorizer
from classification import FORMATS


def main():
    args = parse_user_arguments()

    vectorizer = FeatureVectorizer(args.confusion_set, args.feature_vector)
    vectorizer.vectorize_features(args.cnfs_file, args.data_file, args.format,
                                  args.feature_set)
  

def parse_user_arguments():
    parser = argparse.ArgumentParser()
    
    parser.add_argument('cnfs_file', type=str, help=".cnfs file")
    parser.add_argument('data_file', type=str, help="output data file")

    parser.add_argument('-c', '--confusion-set', required=True,
        help="confusion set as comma-separated list of words")
    parser.add_argument('-f', '--format', required=True, choices=FORMATS,
        help="output data format")
    parser.add_argument('-v', '--feature-vector', 
        help="file with extracted features for feature vector")
    parser.add_argument('-s', '--feature-set', default='base',
        help="predefined feature set")
    
    return parser.parse_args()


if __name__ == '__main__':
    main()
