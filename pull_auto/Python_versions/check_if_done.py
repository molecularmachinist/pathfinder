#!/usr/bin/env python3

import numpy as np

status_array = np.zeros((5))
status_array[1] = 1
K_array = np.array([5, 10, 15, 40, 50])

#Check if the best force constant has been found
# best means the smallest possible successful force constant K
def check_if_done():
    if status_array[1] == 1 and K_array[1] - K_array[0] <= 5:
        print('The best force constant has been found. The force constant is ' + str(K_array[1]) + '.')
        return 1,K_array[1]
    elif status_array[2] == 1 and K_array[2] - K_array[1] <= 5:
        print('The best force constant has been found. The force constant is ' + str(K_array[2]) + '.')
        return 1,K_array[2]
    elif status_array[3] == 1 and K_array[3] - K_array[2] <= 5:
        print('The best force constant has been found. The force constant is ' + str(K_array[3]) + '.')
        return 1,K_array[3]
    else:
        print('The best force constant has not yet been found.')
        return 0

check_if_done()
