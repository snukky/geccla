import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import cmd
import config

from confusion_set import ConfusionSet
from logger import log



class ConfusionMatrix():
    
    def __init__(self, conf_set, cnfs_file):
        self.confusion_set = ConfusionSet(conf_set)
        self.matrix = self.__build_matrix(cnfs_file)
    
    def print_stats(self):
        self.print_matrix()
        
        num_of_confs = self.num_of_confs()
        self.print_matrix(lambda x: "%.2f" % (x / float(num_of_confs) * 100))
    
        print "all      :", num_of_confs
        print "AA edits :", self.num_of_AA_confs()
        print "AB edits :", self.num_of_AB_confs()
        print "ER       : %.3f %%" % self.error_rate()
    
    def print_matrix(self, format_function=lambda x: str(x)):
        print "\t |", "\t".join(self.confusion_set.as_list())
        print "-------- |", "-" * (self.confusion_set.size())*9
        for err in self.confusion_set:
            print err + "\t |",
            for cor in self.confusion_set:
                print format_function(self.matrix[err][cor]), "\t",
            print "\n",
        print ''
    
    def num_of_confs(self):
        return sum([ count for _, row in self.matrix.iteritems()
                           for _, count in row.iteritems() ])
    
    def num_of_AA_confs(self):
        return sum(self.matrix[word][word] for word in self.confusion_set)

    def num_of_AB_confs(self):
        return self.num_of_confs() - self.num_of_AA_confs()
    
    def error_rate(self):
        return self.num_of_AB_confs() / float(self.num_of_confs()) * 100

    def __build_matrix(self, cnfs_file):
        output = cmd.run("cat {0} | tr -s '|||' '\t' | cut -f3,4 | "
            "sort | uniq -c".format(cnfs_file))
        #log.debug("raw edit counts:\n{}".format(output))
    
        matrix = {}
        for err in self.confusion_set:
            matrix[err] = {}
            for cor in self.confusion_set:
                matrix[err][cor] = 0
    
        for line in output.strip().split("\n"):
            count, err, cor = line.lower().split()
            if err not in matrix:
                matrix[err] = {cor: 0}
            matrix[err][cor] += int(count)
    
        return matrix
