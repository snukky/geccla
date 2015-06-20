import os
import sys
import math
import shutil
import random

sys.path.insert(0, os.path.dirname(__file__))

from logger import log


def impose_error_rate(cnfs_file, error_rate, matrix, 
                      in_place=False, shuffle=False):
    num_rm = __calculate_num_of_AA_cnfs_to_remove(error_rate, matrix)
    if num_rm <= 0:
        return

    AA_edits = []
    with open(cnfs_file) as cnfs_io:
        for idx, line in enumerate(cnfs_io):
            if __is_AA_conf_line(line):
                AA_edits.append(idx)

    if shuffle:
        random.shuffle(AA_edits)
    AA_edits_to_rm = set(AA_edits[:num_rm])

    output = open(cnfs_file + '.mod', 'w+') if in_place else sys.stdout

    with open(cnfs_file) as cnfs_io:
        for idx, line in enumerate(cnfs_io):
            if idx not in AA_edits_to_rm:
                output.write(line)

    if in_place:
        shutil.move(cnfs_file + '.mod', cnfs_file)

# Example: 
# AA: 9 
# AB: 1
# base ER_b = 0.1
# desired ER_d = 0.25
# desired AA edits: AA_d =(AB * (1/ER)) - AB = 3
# AA edits to remove: AA_rm 9-3 = 6
# 
# num_of_AB * (1 - E) / E
#
def __calculate_num_of_AA_cnfs_to_remove(error_rate, matrix):
    log.debug("base error rate: {}, desired error rate: {}" \
        .format(matrix.error_rate(), error_rate))

    if error_rate < matrix.error_rate():
        log.warn("decreasing of error rate is not supported")
        return 0

    num_AB_edits = matrix.num_of_AB_edits()
    new_AA_edits = int(math.floor(num_AB_edits * (1 / error_rate) - num_AB_edits))

    num_rm = max(0, matrix.num_of_AA_edits() - new_AA_edits)
    log.debug("number of AA confusions to remove: {}".format(num_rm))

    return num_rm

def __is_AA_conf_line(line):
    fields = line.strip().split('|||')
    return fields[2].lower() == fields[3].lower()
