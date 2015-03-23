import os
import sys

sys.path.insert(0, os.path.dirname(__file__))


class OutputFormatter():
    
    def __init__(self, threshold=None, difference=None):
        self.threshold = threshold
        self.difference = difference

