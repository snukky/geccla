import os
import sys
import math
import shutil

sys.path.insert(0, os.path.dirname(__file__))

from logger import log


# cat test2013.cnfs.empty | tr -s '| ' '\t' | sort -n -k1,1 -k2,2 -k3,3 | sed -r 's/^([0-9]+)\t([0-9]+)\t([0-9]+.*)/\1\t\2 \3/' | sed -r 's/\t/|||/g' > test2013.cnfs.empty.sort
def impose_error_rate(cnfs_file, error_rate, matrix, in_place=False):
    num_rm = __calculate_num_of_AA_cnfs_to_remove(error_rate, matrix)

    if num_rm <= 0:
        return

    if in_place:
        output = open(cnfs_file + '.moderrrate', 'w+')
    else:
        output = sys.stdout

    with open(cnfs_file) as cnfs:
        for line in cnfs:
            if num_rm > 0 and __is_AA_conf_line(line):
                num_rm -= 1
            else:
                output.write(line)

    if in_place:
        shutil.move(cnfs_file + '.moderrrate', cnfs_file)

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
