#!/usr/bin/env python3

import string
import numpy as np
import config as cfg

status_array = np.zeros((5))
status_array[4] = 1
# Returns 1 if the K was successful, 0 if not
def status(idx: int, K: int, domain: string, iter: int):
    file_name = 'files/pull_' + str(domain) + str(iter) + '_' + str(K) + 'x.xvg'
    # file_name = 'pull_TK2_30x.xvg'
    # get 18th line from file
    with open(file_name, 'r') as f:
        for i, line in enumerate(f):
            if i == 17:
                line = line.split()
                # get 2nd column from line
                first = line[1]
                #print(first)
    # get last line from file
    with open(file_name, 'r') as f:
        for i, line in enumerate(f):
            pass
        line = line.split()
        # get 2nd column from line
        last = line[1]
        #print(last)
    if abs(float(last) - float(first)) >= 0.9:
        print('The pulling of the ' + str(domain) + ' domain with ' + str(K) + ' was successful.')
        status_array[idx] = 1
        return 1
    else:
        print('The pulling of the ' + str(domain) + ' domain with ' + str(K) + ' was not successful.')
        return 0


## Testing
K_array = np.array([25, 30, 35, 45, 50])
domain_dict=cfg.domains[0]
i=1
for j in range(4):
    status(j, K_array[j], domain_dict["name"], i)
print(status_array)