import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from logger import log

from confusions.basic_finder import BasicFinder
from taggers.lbj_chunker import LBJChunker

import taggers.pos_helper as tags
import cmd


class ArtOrDetFinder(BasicFinder):

    LEVELS = [1, 2, 3, '1', '2', '3']

    def __init__(self):
        BasicFinder.__init__(self, 'a,the,')
        self.chunker = LBJChunker()

    def find_confusion_artordets(self, corpus, level=2):
        err_text = cmd.source_side_of_file(corpus)
        all_chunks = self.chunker.chunks_and_pos_tags(err_text)

        with open(corpus) as corpus_io:
            for s, line in enumerate(corpus_io):
                err_toks, edits = self.parse_corpus_line(line)

                confs = self.__find_artordets(err_toks, 
                                              edits, 
                                              all_chunks.next(),
                                              level)
                for i, j, err, cor in confs:
                    yield (s, i, j, err, cor)

    # Data are composed of two types of events:
    #
    # 1. All articles in the data
    # 2. Spaces in front of a noun phrase if that noun phrase does not start 
    #    with an article. To identify the beginning of a noun phrase, we ran 
    #    a part-of-speech tagger and a phrase chunker and excluded all noun 
    #    phrases not headed by a personal or demonstrative pronoun.
    #
    def __find_artordets(self, tokens, edits, chunks, level=2):
        """
        Data are composed of three types of events:
        1) All articles in the data
        2) Spaces in front of a noun phrase if that noun phrase does not start 
           with an article. To identify the beginning of a noun phrase, we ran
           a part-of-speech tagger and a phrase chunker and excluded all noun
           phrases not headed by a personal or demonstrative pronoun.
        3) Spaces in front of a noun phrase if that noun phrase does not start
           with an article.
        """
        for i, err in enumerate(tokens):
            # FIXME: is some skip required?

            # all edited articles (including insertions and deletions) if data
            # has corrected version
            if (i,i+1) in edits:
                cor = edits[(i,i+1)][1]
                yield (i, i+1, err, cor)
                continue
            if (i,i) in edits:
                cor = edits[(i,i)][1]
                yield (i, i, '<null>', cor)
                continue

            # all articles in the data
            if self.confusion_set.include(err):
                yield (i, i+1, err, err)
                continue

            if level < 2:
                continue
            
            # spaces in front of a noun phrase if that noun phrase does not
            # start with an article
            if chunks.is_NP_starting_at(i):
                chunk = chunks.get_chunk_by_word_idx(i)

                # exclude all noun phrases not headed by a personal or
                # demonstrative pronoun
                if not tags.is_pronoun(chunk['pos'][-1]):
                    yield (i, i, '<null>', '<null>')
                continue

            if level < 3:
                continue

            # spaces that follow a preposition or a verb
            if i > 0 and (tags.is_prep(chunks.pos[i-1]) \
                    or tags.is_verb(chunks.pos[i-1])):
                yield (i, i, '<null>', '<null>')
                continue
