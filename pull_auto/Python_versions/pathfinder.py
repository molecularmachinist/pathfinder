#!/usr/bin/env python3
# Basically pull_script.sh but python

# Imports
import subprocess
import string
import config as cfg
import numpy as np
from analyze import *
import sys
from pull_plot import *
import logging


## LOGGING
logging.basicConfig(filename='log_pathfinder.log', level=logging.DEBUG)
logging.info('Starting script')


# Read config
global gro_file
gro_file = cfg.gro
global used_Ks 
used_Ks = []
global route
route = []



def read_config():
    ## error handling for inputs
    ## stop script if input is incorrect

    # check that index file has ndx suffix
    if cfg.ndx[-4:] != '.ndx':
        print('The index file must have the suffix .ndx')
        logging.error('The index file does not have the suffix .ndx')
        sys.exit()

    # check that gro file has gro suffix
    if cfg.gro[-4:] != '.gro':
        print('The gro file must have the suffix .gro')
        logging.error('The gro file does not have the suffix .gro')
        sys.exit()

    # check that mdp file has mdp suffix
    if cfg.mdp[-4:] != '.mdp':
        print('The mdp file must have the suffix .mdp')
        logging.error('The mdp file does not have the suffix .mdp')
        sys.exit()

    # check that the number of domains is greater than 0
    if len(cfg.domains) < 1:
        print('The number of domains must be greater than 0')
        logging.error('The number of domains is less than 1')
        sys.exit()

    # check that the number of domains matches the length of domains array
    if len(cfg.domains) != cfg.num_of_domains:
        print('The number of domains must match the length of the domains array')
        logging.error('The number of domains does not match the length of the domains array')
        sys.exit()



read_config()


# Define variables
status_array = np.zeros((5))
K_array = np.array([5, 10, 15, 20, 25])



def write_batch(file_name: string, sbatch: string):
    # remove last line from sbatch.sh
    command = 'srun gmx_mpi mdrun -v -deffnm {} -pf {}f.xvg -px {}x.xvg'.format(file_name, file_name, file_name)
    # delete last line in sbatch.sh
    with open(sbatch, 'r') as f:
        lines = f.readlines()
    with open(sbatch, 'w') as f:
        for line in lines[:-1]:
            f.write(line)
    # add command into the end of sbatch.sh
    with open(sbatch, 'a') as f:
        f.write(command)
    

# doubles nsteps in mdp file
def wall_time(mdp_file: string):
    # take 6th line from mdp file
    with open(mdp_file, 'r') as f:
        for i, line in enumerate(f):
            if i == 5:
                line = line.split()
                nsteps = line[2]
    nsteps = int(nsteps) * 2
    command = 'nsteps    = {} \n'.format(nsteps)
    # delete 5th line in mdp file and add new command
    with open(mdp_file, 'r') as f:
        lines = f.readlines()
    lines[5] = command
    with open(mdp_file, 'w') as f:
        f.writelines(lines)






def bash_command(cmd):
    subprocess.Popen(cmd, shell=True, executable='/bin/bash', stdin=None, stdout=None, stderr=None)

def run_pull(iter: int, K: int, domain: string, sign: int):
    file_name = 'pull_' + str(domain) + str(iter) + '_' + str(K)
    mdp_file = 'pull_' + str(domain) + '.mdp'
    batch = 'sbatch.sh'

    lines = open(mdp_file, 'r').readlines()
    lines[-1] = "\npull_coord1_k = " + str(K) 
    global init
    init = init + 1.5*sign
    lines[-2] = "pull_coord1_init = " + str(init)
    open(mdp_file, 'w').writelines(lines)

    bash_command("gmx_mpi grompp -f pull_{}.mdp -o pull_{}.tpr -c {} -r {} -p topol.top -n {} -maxwarn 1".format(domain, file_name, cfg.gro, cfg.gro, cfg.ndx))
    write_batch(file_name, batch)
    bash_command("sbatch {}".format(batch))
    print("Running {} with K = {}".format(file_name, K))
    return





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
        logging.info('The pulling of the ' + str(domain) + ' domain with ' + str(K) + ' was successful.')
        status_array[idx] = 1
        return 1
    else:
        print('The pulling of the ' + str(domain) + ' domain with ' + str(K) + ' was not successful.')
        logging.info('The pulling of the ' + str(domain) + ' domain with ' + str(K) + ' was not successful.')
        return 0







def new_K(status_array, K_array):
    # from status_array find the index of the first 1
    for i in range(len(status_array)):
        if status_array[i] == 1:
            idx = i
            break

    # if none of the Ks were successful double K max
    if status_array[4] == 0:
        print('None of the Ks were successful. Lets double K max.')
        logging.info('None of the Ks were successful. Lets double K max.')
        K_array[4] = K_array[4] * 2
    else:
        print('K=' + str(K_array[idx]) + ' was successful.')
        # the successful K will now be K max in the K_array
        K_array[4] = K_array[idx]
    
    # set other K's in K_array equally spaced between 5 and K max
    K_array[2] = (K_array[0] + (K_array[4]-K_array[0])/2)
    # round K's to nearest multiple of 5
    K_array[2] = round(K_array[2]/5)*5
    K_array[1] = (K_array[2] - K_array[0])/2
    K_array[1] = round(K_array[1]/5)*5
    K_array[3] = (K_array[4] - K_array[2])/2
    K_array[3] = round(K_array[3]/5)*5
    K_array[3] = K_array[2] + K_array[3]
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

    # check if the three middle values already exist in used_Ks

    #????

    print('New K_array: ' + str(K_array))
    logging.info('New K_array: ' + str(K_array))





def check_if_done():
    if status_array[1] == 1 and K_array[1] - K_array[0] <= 5:
        print('The best force constant has been found. The force constant is ' + str(K_array[1]) + '.')
        logging.info('The best force constant has been found. The force constant is ' + str(K_array[1]) + '.')
        return 1,K_array[1]
    elif status_array[2] == 1 and K_array[2] - K_array[1] <= 5:
        print('The best force constant has been found. The force constant is ' + str(K_array[2]) + '.')
        logging.info('The best force constant has been found. The force constant is ' + str(K_array[2]) + '.')
        return 1,K_array[2]
    elif status_array[3] == 1 and K_array[3] - K_array[2] <= 5:
        print('The best force constant has been found. The force constant is ' + str(K_array[3]) + '.')
        logging.info('The best force constant has been found. The force constant is ' + str(K_array[3]) + '.')
        return 1,K_array[3]
    else:
        print('The best force constant has not yet been found.')
        return 0




def run_eq(domain: string, iter: int):
    file_name = 'pull_eq_' + str(domain) + str(iter)
    mdp_file = 'pull_eq.mdp'

    #delete last 2 lines of mdp file
    lines = open(mdp_file, 'r').readlines()
    del lines[-2:]

    global init
    current_coord = init
    range_high = current_coord + 0.25
    range_low = current_coord - 0.25

    #insert new lines into mdp file
    lines.append("pull_coord1_init = " + str(range_high))
    lines.append("pull_coord2_init = " + str(range_low))
    open(mdp_file, 'w').writelines(lines)

    bash_command("gmx_mpi grompp -f pull_eq_{}.mdp -o pull_eq_{}.tpr -c {} -r {} -p topol.top -n {} -maxwarn 1".format(domain, file_name, gro_file, gro_file, cfg.ndx))
    write_batch(file_name)
    bash_command("sbatch {}".format(file_name))
    print("Equilibration {} submitted".format(file_name))
    logging.info("Equilibration {} submitted".format(file_name))

    #############
    ## WAITING ##
    #############

    command="gmx_mpi rms -s {}.tpr -f {}.xtc -o {}_rmsd.xvg -tu ns".format(file_name, file_name, file_name)
    subprocess.run([command], input="4 4", text=True, shell=True, executable='/bin/bash')

    rmsd_xvg_file = file_name + '_rmsd.xvg'
    # from analyze.py use function analyze
    result=analyze(rmsd_xvg_file, domain)
    print("Result: ", result)
    if result == 0:
        print("Running equilibration again with longer wall time")
        logging.info("Running equilibration again with longer wall time")
        wall_time()
        run_eq(domain, iter)
    else:
        print("Equilibration was successful")
        logging.info("Equilibration was successful")
    




def ask_continue():
    print("The first iteration of pulling and equilibration has finished.")
    print("Please check the pullf and pullx files, aswell as the trajectory files and make sure everything looks correct.")
    answer = input("Do you want to continue to the next iteration? (y/n)")
    if answer == "y":
        print("Tou answered yes. Continuing simulations...")
    elif answer == "n":
        print("You answered no. Exiting...")
        logging.info('User chose not to continue. Exiting program.')
        sys.exit()
    else:
        print("Invalid answer. Please try again.")
        ask_continue()




def cleanup():
    print("Removing files from the unsuccessful simulations is recommended.")
    # ask user if they want to remove files
    answer = input("Do you want to remove files? (y/n)")
    if answer == "y":
        print("Removing files...")
        logging.info('User chose to remove files.')
        # remove files
    if answer == "n":
        print("Not removing files.")
        # do not remove files
    else:    
        print("Invalid answer. Please try again.")
        cleanup()




def run_simulation(domain_dict):
    global init 
    init = domain_dict['start']
    for i in domain_dict["iterations"]:
        # set 5 different K's
        K_array = np.array([5, 20, 30, 40, 50])

        res = 0
        while res == 0:
            for j in range(5):
                # if K_array[j] is not in used_Ks, run simulation
                if K_array[j] not in used_Ks and K_array[j]>0:
                    run_pull(i, K_array[j], domain_dict["name"], domain_dict["sign"])
            print("Running simulations for domain " + domain_dict["name"] + " iteration " + str(i))
            used_Ks += K_array
            # remove duplicates from used_Ks
            used_Ks = np.unique(used_Ks)

            ## wait for jobs in mahti to finish

            for j in range(5):
                status(j, K_array[j], domain_dict["name"], i)

            res, best_K = check_if_done()
            if res == 1:
                global gro_file
                gro_file = 'pull_' + domain_dict["name"] + str(i) + '_' + str(best_K) + '.gro'
                global route
                route += domain_dict["name"] + "/iteration_" + str(i) + "/K_" + str(best_K)
                pullf = "pull_" + domain_dict["name"] + str(i) + "_" + str(best_K) + "f.xvg"
                pullx = "pull_" + domain_dict["name"] + str(i) + "_" + str(best_K) + "x.xvg"
                pull_plot(pullx, pullf)
                print("The best force constant has been found.")
            else:
                new_K(status_array, K_array)

            run_eq(domain_dict["name"])

            if i != domain_dict["iterations"]:
                cleanup()
                ask_continue()
            else:
                print("That was the last iteration. The program will stop now.")

            gro_file = "pull_eq_" + domain_dict["name"] + str(i) + ".gro"


def main():
    for domain in cfg.domains:
        run_simulation(domain)