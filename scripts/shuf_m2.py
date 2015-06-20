#!/usr/bin/python

import fileinput
import random

data = []

for line in fileinput.input():
    if line.startswith("S "):
        data.append(line)
    elif line.startswith("A "):
        data[-1] += line
    elif not line.strip():
        pass
    else:
        print >> sys.stderr, "unrecognized line:", line.strip()

random.shuffle(data)

for sent in data:
    print sent
