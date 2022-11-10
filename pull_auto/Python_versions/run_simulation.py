#!/usr/bin/env python3

import numpy as np
from pull_plot import *

def run_simulation(domain_dict):
    for i in domain_dict["iterations"]:
        # set 5 different K's
        K_array = np.array([5, 20, 30, 40, 50])

        res = 0
        while res == 0:
            for j in range(5):
                run_pull(i, K_array[j], domain_dict["name"], domain_dict["sign"])
            print("Running 5 simulations for domain " + domain_dict["name"] + " iteration " + str(i))

            # wait for simulations to finish

            for j in range(5):
                status(j, K_array[j], domain_dict["name"], i)

            res, best_K = check_if_done()
            if res == 1:
                route = domain_dict["name"] + "/iteration_" + str(i) + "/K_" + str(best_K)
                pullf = "pull_" + domain_dict["name"] + str(i) + "_" + str(best_K) + "f.xvg"
                pullx = "pull_" + domain_dict["name"] + str(i) + "_" + str(best_K) + "x.xvg"
                pull_plot(pullx, pullf)
                print("The best force constant has been found.")
            else:
                new_K(status_array, K_array)

            run_eq(i, domain_dict["name"], i)

            if i != domain_dict["iterations"]:
                ask_continue()
            else:
                print("That was the last iteration. The program will stop now.")
 

