#!/usr/bin/python

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from cmd import run_cmd, wc
from confusion_set import ConfusionSet
from confusions import parse_conf_line
from logger import log

from classification import FORMATS
from features import FEATURE_SETS


class FeatureVectorizer():
    
    def __init__(self, conf_set, 
                       feat_file=None, 
                       min_feat_count=2, 
                       max_vec_size=500000):

        self.confusion_set = ConfusionSet(conf_set)
        self.min_feat_count = min_feat_count
        self.max_vec_size = max_vec_size

        if feat_file:
            self.__read_feature_vector(feat_file)
        else:
            # dict object of features with feature values as keys and
            # feature_indexes as values
            self.feat_map = {}
            # set object with all features
            self.feat_vec = set()

    def vectorize_features(self, cnfs_file, data_file, format, feat_set=None):
        if not self.feat_vec or not self.feat_map:
            self.__build_feature_vector(cnfs_file, feat_set)
        
        if format == 'snow':
            self.__format_snow_data(cnfs_file, data_file)
        elif format == 'vw':
            self.__format_vw_data(cnfs_file, data_file)
        elif format == 'libsvm':
            self.__format_libsvm_data(cnfs_file, data_file)
        elif format == 'maxent':
            self.__format_maxent_data(cnfs_file, data_file, feat_set)
        else:
            log.error("format '{}' not recognized!".format(format))
            

    def __build_feature_vector(self, cnfs_file, feat_set):
        freq_file = cnfs_file + '.freq'
        feat_file = cnfs_file + '.feat'
    
        self.create_freq_file(cnfs_file, freq_file)
        self.create_feat_file(freq_file, feat_set, feat_file)
        self.__read_feature_vector(feat_file)
        
    def __read_feature_vector(self, feat_file):
        log.info("loading feature vector: {}".format(feat_file))

        with open(feat_file) as feat_io:
            for i, feat in enumerate(feat_io):
                if i >= self.max_vec_size:
                    break
                self.feat_map[feat.strip()] = i

        log.info("loaded number of features: {}".format(len(self.feat_map)))
        self.feat_vec = set(self.feat_map.keys())

    def __format_snow_data(self, cnfs_file, data_file, feat_set=None):
        """
        0,4,5,101,102,...:
        1,4,101,102,...:
        """
        log.info("creating SNoW data...")

        data = open(data_file, 'w+')
        with open(cnfs_file) as cnfs:
            for line in cnfs:
                _, _, _, err, cor, feats = parse_conf_line(line)
                
                label = self.confusion_set.word_to_num_label(cor)
                num_of_labels = self.confusion_set.size()
                feat_vector = [ self.feat_map[feat] + num_of_labels 
                                for feat in feats if feat in self.feat_vec ]
                vector = [str(val) for val in [label] + sorted(feat_vector)]
    
                data.write("{}:\n".format(','.join(vector)))
        data.close()

    def __format_vw_data(self, cnfs_file, data_file, feat_set=None):
        """
        1 | feat_01:value_01 feat_02=value_02 ...
        2 | feat_04:value_04 feat_05=value_05 ...
        """
        log.info("creating VW data...")

        data = open(data_file, 'w+')
        with open(cnfs_file) as cnfs:
            for line in cnfs:
                _, _, _, err, cor, feats = parse_conf_line(line)
                
                label = self.confusion_set.word_to_num_label(cor, 1)
                vector = [ "{}:1.0".format(self.__escape_vw_chars(feat)) 
                           for feat in feats if feat in self.feat_vec ]
                data.write("{0} | {1}\n".format(label, ' '.join(vector)))
        data.close()
    
    def __escape_vw_chars(self, text):
        return text.replace(':', '<col>').replace('|', '<bar>')

    def __format_libsvm_data(self, cnfs_file, data_file, feat_set=None):
        """
        1 1:1 2:1 ...
        2 4:1 5:1 ...
        """
        log.info("creating sparse LIBSVM data...")

        data = open(data_file, 'w+')
        with open(cnfs_file) as cnfs:
            for line in cnfs:
                _, _, _, err, cor, feats = parse_conf_line(line)
                
                label = self.confusion_set.word_to_num_label(cor, 1)
                idx_vector = [ self.feat_map[feat] + 1 
                               for feat in feats if feat in self.feat_vec ]
                vector = ["%i:1" % val for val in sorted(idx_vector)]
    
                data.write("{0} {1}\n".format(label, ' '.join(vector)))
        data.close()
        
    def __format_maxent_data(self, cnfs_file, data_file, feat_set):
        log.info("creating Stanford Maximum Entropy Classifier data...")
    
        data = open(data_file, 'w+')
        with open(cnfs_file) as cnfs:
            for line in cnfs:
                _, _, _, err, cor, feats = parse_conf_line(line, True)

                label = self.confusion_set.word_to_num_label(cor, 1)
                vector = [ feats.get(column, '_') 
                           for column in FEATURE_SETS[feat_set] ]
    
                data.write("{0}\t{1}\n".format(label, "\t".join(vector)))
        data.close()

        self.__create_maxent_prop_file(data_file + '.prop', feat_set)
   
    def __create_maxent_prop_file(self, prop_file, feat_set):
        with open(prop_file, 'w+') as prop:
            # Print features
            prop.write("useClassFeature=false\n")
            for idx in range(len(FEATURE_SETS[feat_set])):
                prop.write("{0}.useString=true\n".format(idx+1))
            #prop.write("printClassifier=HighWeight\n")
            #prop.write("printClassifierParam=200\n")
            # Mapping
            prop.write("displayedColumn=-1\n")
            prop.write("displayAllAnswers=true\n")
            prop.write("goldAnswerColumn=0\n")
            # Optimization
            prop.write("intern=true\n")
            prop.write("sigma=3\n")
            prop.write("prior=quadratic\n")
            prop.write("useQN=true\n")
            prop.write("QNsize=15\n")
            prop.write("tolerance=1e-4\n")


    def create_freq_file(self, cnfs_file, freq_file):
        if os.path.exists(freq_file):
            log.info("file with frequencies exists: {}".format(freq_file))
            return
            
        log.info("counting frequencies...")
        run_cmd("cat {} | sed 's/|||/\\t/g' | cut -f5 | tr ' ' '\\n' "
            "| sort | uniq -c | sort -nr > {}".format(cnfs_file, freq_file))
    
    def create_feat_file(self, freq_file, feat_set, feat_file):
        if os.path.exists(feat_file):
            log.info("file with features exists: {}".format(feat_file))
            return
    
        log.info("truncating features...")
        log.info("minimum count for single feature: {}" \
            .format(self.min_feat_count))
    
        line_num = run_cmd("cat {} | grep -Pn ' +{} .*' | tr ':' '\\t' | cut -f1 | tail -1" \
            .format(freq_file, self.min_feat_count)).strip()
    
        log.info("building feature vector...")
        log.info("selected feature set: {}".format(feat_set))
        log.info("total number of predicates: {}".format(len(FEATURE_SETS[feat_set])))
    
        regex = '^(' + '|'.join(FEATURE_SETS[feat_set]) + ')='
        run_cmd("head -n {} {} | sed -r 's/ *[0-9]+ (.*)/\\1/' | grep -P '{}' > {}" \
            .format(line_num, freq_file, regex, feat_file))

        log.info("limit for features: {}".format(self.max_vec_size))
        log.info("active features: {}".format(wc(feat_file)))
    
        feat_count = run_cmd("cat {} | sed -r 's/(.*)=.*/\\1/' | sort -u | wc -l" \
            .format(feat_file)).strip()
        log.info("active predicates: {}".format(feat_count))
