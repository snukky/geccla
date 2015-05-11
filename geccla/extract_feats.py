#!/usr/bin/python

import argparse

from features.feature_extractor import FeatureExtractor
from features.artordet_features import ArtOrDetFeatures
from confusions import format_conf


def main():
    args = parse_user_arguments()
    
    if args.artordet:
        extractor = ArtOrDetFeatures()
    else:
        extractor = FeatureExtractor(feat_set=args.feature_set,
                                     awc_dict=args.word_clusters)
    
    for conf in extractor.extract_features(args.input_file, args.cnfs_file):
        print format_conf(conf)
  

def parse_user_arguments():
    parser = argparse.ArgumentParser()
    
    parser.add_argument('input_file', type=str, help="input text file")
    parser.add_argument('cnfs_file', type=str, help=".cnfs file")

    parser.add_argument('--artordet', action='store_true',
        help="enable enhanced features for articles and determiners")
    parser.add_argument('-s', '--feature-set', type=str,
        help="set of predefined features")
    parser.add_argument('-w', '--word-clusters', type=str,
        help="path to file with word clusters")
    
    return parser.parse_args()


if __name__ == '__main__':
    main()
