import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import cmd
import config

from confusion_set import ConfusionSet
from logger import log


class ConfusionMatrix():
    
    def __init__(self, cnfs_file, conf_set=None):
        if not conf_set:
            conf_set = self.__create_confusion_set(cnfs_file)
        self.confusion_set = ConfusionSet(conf_set)
        self.matrix = self.__build_matrix(cnfs_file)
    
    def print_stats(self):
        self.print_matrix()
        
        num_of_edits = self.num_of_edits()
        self.print_matrix(lambda x: "%.2f" % (x / float(num_of_edits) * 100))
    
        print "all      :", num_of_edits
        print "AA edits :", self.num_of_AA_edits()
        print "AB edits :", self.num_of_AB_edits()
        print "ER       : %.2f %%" % (self.error_rate() * 100)
    
    def print_matrix(self, format_func=lambda x: str(x)):
        print "\t |", "\t".join(self.confusion_set.as_list())
        print "-------- |", "-" * (self.confusion_set.size()) * 9
        for err in self.confusion_set:
            print err + "\t |",
            for cor in self.confusion_set:
                print "{: <6} \t".format(format_func(self.matrix[err][cor])),
            print "\n",
        print ''
    
    def num_of_edits(self):
        return sum([ count for _, row in self.matrix.iteritems()
                           for _, count in row.iteritems() ])
    
    def num_of_AA_edits(self):
        return sum(self.matrix[word][word] for word in self.confusion_set)

    def num_of_AB_edits(self):
        return self.num_of_edits() - self.num_of_AA_edits()
    
    def error_rate(self):
        return self.num_of_AB_edits() / float(self.num_of_edits())

    def __build_matrix(self, cnfs_file):
        output = cmd.run("cat {} | tr -s '|||' '\\t' | cut -f3,4" \
            " | sed 's/.*/\\L&/' | sort | uniq -c".format(cnfs_file))
        log.debug("raw edit counts:\n{}".format(output))
    
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

    def __create_confusion_set(self, cnfs_file):
        output = cmd.run("cat {} | tr -s '|||' '\\t' | cut -f3,4 | tr '\\t' '\\n' "  \
            " | sed 's/.*/\\L&/' | sort -u".format(cnfs_file))
        return ','.join(output.strip().split())
