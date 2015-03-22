import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import cmd

from confusions.basic_finder import BasicFinder

from taggers.pos_tagger import StanfordPOSTagger as POSTagger
from taggers.wc_tagger import WordClassTagger as WCTagger

from logger import log

DEBUG_COUNTER = 10000


class NullFinder(BasicFinder):
    
    LEVELS = 'tok pos awc'.split()

    def __init__(self, conf_set, clean=False):
        BasicFinder.__init__(self, conf_set)

        self.left_context = None
        self.right_context = None

        self.pos_tagger = None
        self.wc_tagger = None
        self.ngrams = {}
        self.__clean = clean

    def find_confusion_nulls(self, 
                             corpus, 
                             ngrams_prefix=None, 
                             levels=['tok', 'awc']):
        """
        Finds <null> positions for given lists of n-grams at certain processing
        levels, e.g. tokens, part-of-speech tags and/or automatic word classes.
        """
        self.__load_ngrams(ngrams_prefix, levels)
        files = self.__tag_file(corpus, levels)

        for level in levels:
            files[level] = open(files[level])
        
        with open(corpus) as corpus_io:
            for s, line in enumerate(corpus_io):
                err_toks, edits = self.parse_corpus_line(line)
                all_tags = { level : files[level].next().strip().split()
                             for level in levels }

                confs = self.__find_nulls(err_toks, all_tags, edits)
                for i, j, err, cor in confs:
                    yield (s, i, j, err, cor)
                    
        for level in levels:
            files[level].close()
    
    def __load_ngrams(self, ngrams_prefix, levels):
        if not ngrams_prefix:
            return
            
        for level in levels:
            file = ngrams_prefix + '.' + level
            log.info("loading n-grams from file '{}'".format(file))

            if not os.path.exists(file):
                log.warn("file '{}' for level {} does not exist!" \
                    .format(file, level))
                continue

            self.__read_info_line(file)

            with open(file) as f:
                ngrams = [line.strip() for line in f.readlines()[1:-1]]
                log.info("{} ngrams loaded for '{}' level".format(len(ngrams), level))
                self.ngrams[level] = set(ngrams)

    def __find_nulls(self, tokens, all_tags, edits):
        skip = False

        for i, err in enumerate(tokens):
            if skip:
                skip = False
                continue
            
            if (i,i+1) in edits:
                cor = edits[(i,i+1)][1]
                yield (i, i+1, err, cor)
                skip = True
            elif (i,i) in edits:
                cor = edits[(i,i)][1]
                yield (i, i, '<null>', cor)
                skip = True

            elif self.confusion_set.include(err):
                yield (i, i+1, err, err)
                skip = True

            else:
                j = i + self.left_context

                for level in all_tags.keys():
                    tags = self.__add_boundaries(all_tags[level])
                    if self.__ngram(j, tags, 0) in self.ngrams[level]:
                        yield (i, i, '<null>', '<null>')
                        break


    def train_ngrams(self, corpus, ngrams_prefix, 
                     left_context=1, right_context=3, min_count=5,
                     levels=['tok']):
        """
        Extracts n-grams at various processing levels for further finding of 
        <null> positions.
        """
        self.left_context = left_context
        self.right_context = right_context

        tag_files = self.__tag_file(corpus, levels)
        ngram_lists = self.__extract_lists_of_ngrams(corpus, ngrams_prefix, tag_files)

        for level, file in ngram_lists.iteritems():
            self.__count_frequencies(file, file + '.freq')

            ngram_file = ngrams_prefix + '.' + level
            self.__write_info_line(ngram_file, level)
            self.__save_ngrams(file + '.freq', ngram_file, min_count)

            if self.__clean:
                log.debug("removing temporary files {}/.freq".format(file))
                os.remove(file)
                os.remove(file + '.freq')

    def __tag_file(self, corpus, levels):
        input = cmd.get_source_side_of_file(corpus)

        log.info("tagging file {} at levels: {}".format(input, ', '.join(levels)))

        files = {}

        if 'tok' in levels:
            files['tok'] = input
        if 'pos' in levels:
            pos_tagger = POSTagger()
            pos_tagger.tag_file(input, input + '.pos')
            files['pos'] = input + '.pos'
        if 'awc' in levels:
            awc_tagger = WCTagger()
            awc_tagger.tag_file(input, input + '.awc')
            files['awc'] = input + '.awc'

        return files

    def __extract_lists_of_ngrams(self, corpus, prefix, tag_files):
        files = {}
        levels = tag_files.keys()

        for level in levels:
            files[level] = open(prefix + '.' + level + '.list', 'w+')
            tag_files[level] = open(tag_files[level])
        
        with open(corpus) as corpus_io:
            for i, line in enumerate(corpus_io):
                words = line.strip().split()

                for level in levels:
                    tokens = tag_files[level].next().strip().split()
                    ngrams = self.__extract_ngrams(words, tokens)
                    files[level].write("\n".join(ngrams) + "\n")
                
                if 0 == (i+1) % DEBUG_COUNTER:
                    log.debug("[{}]".format(i+1))

        for level in levels:
            files[level].close()

        return {level:file.name for level, file in files.iteritems()}

    def __count_frequencies(self, list_file, freq_file):
        log.debug("counting n-gram frequencies in file {}...".format(list_file))
        cmd.run("cat {0} | sort | uniq -c | sort -nr > {1}" \
            .format(list_file, freq_file))

    def __save_ngrams(self, freq_file, ngram_file, min_count):
        log.debug("storing n-gram frequencies to file {}...".format(ngram_file))
        line_num = cmd.run("cat {0} | grep -Pn ' +{1} .*' | tr ':' '\\t'" \
            " | cut -f1 | tail -1".format(freq_file, min_count))
        cmd.run("head -n {} {} | sed -r 's/ *[0-9]+ (.*)/\\1/' >> {}" \
            .format(line_num.strip(), freq_file, ngram_file))
        
    def __extract_ngrams(self, tokens, tags):
        tags = self.__add_boundaries(tags)
        ngrams = []
        for i, word in enumerate(tokens):
            j = i + self.left_context
            if self.confusion_set.include_in_non_nulls(word):
                ngrams.append(self.__ngram(j, tags))
        return ngrams
    
    def __add_boundaries(self, tokens):
        return ['<s>'] * self.left_context + tokens \
            + ['</s>'] * self.right_context

    def __ngram(self, i, tokens, length=1):
        return ' '.join(tokens[i-self.left_context:i] \
            + tokens[i+length:i+length+self.right_context])

    def __write_info_line(self, file, level):
        with open(file, 'w+') as f:
            f.write("{} {} {}\n" \
                .format(level, self.left_context, self.right_context))

    def __read_info_line(self, file):
        with open(file, 'r') as f:
            level, lc, rc = f.next().strip().split()
        self.left_context = int(lc)
        self.right_context = int(rc)
        return level
