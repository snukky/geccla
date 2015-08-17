import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from logger import log


class ConfusionSet:

    def __init__(self, conf_set):
        if isinstance(conf_set, ConfusionSet):
            self.cs = conf_set.cs
            self.non_nulls = conf_set.non_nulls
        else:
            self.cs = self.__prepare_confusion_set(conf_set)
            self.non_nulls = [cw for cw in self.cs if cw != '<null>']
            log.debug("init " + self.__str__())


    def include(self, word):
        cw = '<null>' if word == '' else word
        cw = ',' if word == '<comma>' else word
        return cw.lower() in self.cs

    def include_in_non_nulls(self, word):
        return word.lower() in self.non_nulls

    def include_null(self):
        return self.include('')

    def as_list(self):
        return list(self.cs)

    def size(self):
        """Returns the number of confused words."""
        return len(self.cs)

    
    def word_to_num_label(self, word, start_from=0):
        if self.include(word):
            return self.cs.index(word.lower()) + start_from
        return None
    
    def num_label_to_word(self, num_label, start_from=0):
        num_label = int(num_label)
        if num_label - start_from < len(self.cs) and num_label >= 0:
            return self.cs[num_label - start_from]
        return None

    def num_labels(self, start_from=0):
        return {self.word_to_num_label(word, start_from):word 
                for word in self.cs}

    def __prepare_confusion_set(self, words):
        cs = ['<null>' if w.strip() == '' else w.strip().lower() 
              for w in words.split(',')]
        cs = [',' if w == '<comma>' else w for w in cs]
        return sorted(list(set(cs)))

    def __iter__(self):
        for cw in self.cs:
            yield cw

    def __str__(self):
        return "cs= %s" % self.num_labels()

    def __repr__(self):
        return """<ConfusionSet %s>""" % self.cs
