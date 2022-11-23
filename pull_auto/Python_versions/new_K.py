#!/usr/bin/env python3

import numpy as np

status_array = np.array([0, 0, 0, 1, 1])
K_array = np.array([5, 25, 50, 75, 100])
global used_Ks
used_Ks = K_array

def new_K(status_array, K_array):
    # from status_array find the index of the first 1
    for i in range(len(status_array)):
        if status_array[i] == 1:
            idx = i
            break

    # if none of the Ks were successful double K max
    if status_array[4] == 0:
        print('None of the Ks were successful. Lets double K max.')
        K_array[4] = K_array[4] * 2
    else:
        print('K=' + str(K_array[idx]) + ' was successful.')
        # the successful K will now be K max in the K_array
        K_array[4] = K_array[idx]
    
    # set other K's in K_array equally spaced between K_min and K max
    K_array[0] = K_array[idx-1]
    K_array[2] = (K_array[0] + (K_array[4]-K_array[0])/2)
    # round K's to nearest multiple of 5
    K_array[2] = round(K_array[2]/5)*5
    K_array[1] = (K_array[0] + (K_array[2] - K_array[0])/2)
    K_array[1] = round(K_array[1]/5)*5
    K_array[3] = (K_array[4] - K_array[2])/2
    K_array[3] = round(K_array[3]/5)*5
    K_array[3] = K_array[2] + K_array[3]
    print('New K_array: ' + str(K_array))
    global used_Ks
    used_Ks += K_array
    # remove duplicates from used_Ks
    used_Ks = np.unique(used_Ks)

    status_array = np.zeros((5))
    status_array[4] = 1

    # error handling:
    # dont run duplicate K's
    # use an array of K's that have been run to check for duplicates
    # if new K array contains old K duplicates, change them by adding 5
    # check this in pull_script.py


new_K(status_array, K_array)