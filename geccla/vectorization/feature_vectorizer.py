import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import cmd
from confusion_set import ConfusionSet
from confusions import parse_conf_line
from logger import log

from classification import FORMATS

from features import FEATURE_SETS
from vectorization import create_freq_file
from vectorization import create_feat_file


class FeatureVectorizer():
    
    def __init__(self, conf_set, 
                       feat_file=None, 
                       min_feat_count=5, 
                       max_vec_size=2000000):

        self.confusion_set = ConfusionSet(conf_set)
        self.min_feat_count = min_feat_count
        self.max_vec_size = max_vec_size

        # dict object of features with feature values as keys and
        # feature_indexes as values
        self.feat_map = {}
        # set object with all features
        self.feat_vec = set()

        if feat_file:
            self.__read_feature_vector(feat_file)

    def vectorize_features(self, cnfs_file, data_file, format, feat_set=None):
        if not self.feat_vec or not self.feat_map:
            self.__build_feature_vector(cnfs_file, feat_set)
        
        if format == 'snow':
            self.__format_snow_data(cnfs_file, data_file)
        elif format == 'vw':
            self.__format_vw_data(cnfs_file, data_file)
        elif format == 'vwldf':
            self.__format_vwldf_data(cnfs_file, data_file)
        elif format == 'libsvm':
            self.__format_libsvm_data(cnfs_file, data_file)
        elif format == 'maxent':
            self.__format_maxent_data(cnfs_file, data_file, feat_set)
        else:
            log.error("format '{}' not recognized!".format(format))
            

    def __build_feature_vector(self, cnfs_file, feat_set):
        freq_file = cnfs_file + '.freq'
        feat_file = cnfs_file + '.feat'
    
        if os.path.exists(freq_file):
            log.info("file with frequencies exists: {}".format(freq_file))
        else:
            create_freq_file(cnfs_file, freq_file)

        if os.path.exists(feat_file):
            log.info("file with features exists: {}".format(feat_file))
        else:
            create_feat_file(freq_file, feat_set, feat_file, 
                             self.min_feat_count, self.max_vec_size)

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
    
    def __format_vwldf_data(self, cnfs_file, data_file, feat_set=None):
        """
        shared |s feats ...
        1111:0 |w <null>
        1111:0 |w a
        1111:0 |w the

        """
        log.info("creating VW LDF data...")

        data = open(data_file, 'w+')
        with open(cnfs_file) as cnfs:
            for line in cnfs:
                _, _, _, err, cor, feats = parse_conf_line(line)
                
                vector = [ "{}".format(self.__escape_vw_chars(feat)) 
                           for feat in feats if feat in self.feat_vec ]
                data.write("shared |s {0} {1}\n".format(err, ' '.join(vector)))

                for word in self.confusion_set.as_list():
                    label = 0 if word.lower() == cor.lower() else 1
                    if word.lower() == err.lower() and label == 1:
                        label = 2

                    data.write("1111:{0} |t {1}\n".format(label, word.lower()))
                data.write("\n")

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
