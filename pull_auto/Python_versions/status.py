#!/usr/bin/env python3

import string
import numpy as np

status_array = np.zeros((5))
# Returns 1 if the K was successful, 0 if not
def status(idx: int, K: int, domain: string, iter: int):
    file_name = 'pull_' + str(domain) + str(iter) + '_' + str(K) + 'x.xvg'
    # file_name = 'pull_TK2_30x.xvg'
    # get 18th line from file
    with open(file_name, 'r') as f:
        for i, line in enumerate(f):
            if i == 17:
                line = line.split()
                # get 2nd column from line
                first = line[1]
                print(first)
    # get last line from file
    with open(file_name, 'r') as f:
        for i, line in enumerate(f):
            pass
        line = line.split()
        # get 2nd column from line
        last = line[1]
        print(last)
    if abs(float(last) - float(first)) >= 0.9:
        print('The pulling of the ' + str(domain) + ' domain with ' + str(K) + ' was successful.')
        status_array[idx] = 1
        return 1
    else:
        print('The pulling of the ' + str(domain) + ' domain with ' + str(K) + ' was not successful.')
        return 0
    
