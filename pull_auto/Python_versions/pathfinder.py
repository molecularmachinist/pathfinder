#!/usr/bin/env python3


# Imports
import subprocess
import string
import config as cfg
import numpy as np
import sys
import logging
import time
import os
import matplotlib.pyplot as plt
from scipy.stats import linregress
import math
import json




## LOGGING
logging.basicConfig(filename='log_pathfinder.log', level=logging.DEBUG)
# clear log file before running
#open('log_pathfinder.log', 'w').close()
logging.info('Starting program')




# Define global variables
#global gro_file
#gro_file = cfg.gro
# global used_Ks
# used_Ks = np.array([])
# global route
# route = []
# global status_array
# status_array = np.zeros((5))
# global K_array





## error handling for inputs
## stop script if input is incorrect
def read_config():

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







def write_batch(file_name: string, sbatch: string):
    # remove last line from sbatch.sh
    command = 'srun gmx_mpi mdrun -deffnm {} -pf {}f.xvg -px {}x.xvg'.format(file_name, file_name, file_name)
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



# Set up and run a pulling simulation
def run_pull(iter: int, K: int, domain: str):
    file_name = 'pull_' + str(domain) + str(iter) + '_' + str(K)
    mdp_file = 'pull_' + str(domain) + '.mdp'
    batch = 'sbatch.sh'
    jobname = str(domain) + str(iter) + '_' + str(K)
    output = 'pull_' + str(domain) + str(iter) + '_' + str(K) + '.out'

    lines = open(mdp_file, 'r').readlines()
    lines[-1] = "\npull_coord1_k = " + str(K) 
    global start
    lines[-2] = "pull_coord1_init = " + str(start)
    open(mdp_file, 'w').writelines(lines)

    f = open("gro_file.json", "r")
    gro_dict = json.load(f)
    gro_file = gro_dict['gro_file']
    bash_command("gmx_mpi grompp -f pull_{}.mdp -o {}.tpr -c {} -r {} -p topol.top -n {} -maxwarn {}".format(domain, file_name, gro_file, gro_file, cfg.ndx, cfg.maxwarn))
    write_batch(file_name, batch)
    bash_command("sbatch -J {} -o {} {}".format(jobname, output, batch))
    print("Running {} with K = {}".format(file_name, K))
    time.sleep(10)
    #bash_command("cd iteration{}".format(iter))
    # if directory doesn't exist, create it
    if not os.path.exists("K={}".format(K)):
        bash_command("mkdir -p iteration{}/K={}".format(iter, K))
    #bash_command("cd ..")
    time.sleep(2)
    #bash_command("mv pull_{}{}_{}* iteration{}/K={}".format(domain,iter,K,iter,K))
    time.sleep(7)




# Determine status (0 or 1) for each K/simulation
# 0 means K wasn't able to pull/push, and 1 means
def status(idx: int, K: int, domain: string, iter: int):
    global status_dict
    file_name = 'iteration' + str(iter) + '/K=' + str(K) + '/pull_' + str(domain) + str(iter) + '_' + str(K) + 'x.xvg'
    #remove whitespace from file_name
    file_name = file_name.replace(" ", "")
    if os.path.exists(file_name):
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
            #status_array[idx] = 1
            status_dict[int(K)]=1
            # status_dict={"status_dict": status_dict}
            # with open("status_dict.json", "w") as f:
            #     json.dump(status_dict, f, indent=4)
            return 1
        else:
            print('The pulling of the ' + str(domain) + ' domain with ' + str(K) + ' was not successful.')
            logging.info('The pulling of the ' + str(domain) + ' domain with ' + str(K) + ' was not successful.')
            status_dict[int(K)]=0
            # status_dict={"status_dict": status_dict}
            # with open("status_dict.json", "w") as f:
            #     json.dump(status_dict, f, indent=4)
            return 0
    else:
        print('The xvg file does not exist')
        logging.error('The xvg file does not exist')







def new_K(status_array, K_array):
    # from status_array find the index of the first 1
    # for i in range(len(status_array)):
    #     if status_array[i] == 1:
    #         idx = i
    #         break
    index=0
    #status_array = status_array['status_dict']
    status_array = dict(status_array)
    K_array = list(K_array)
    for key, value in status_array.items():
        if value == 1:
            print('key=' + str(key))
            index = K_array.index(key)
            break
    print('index=' + str(index))
    K_array = np.array(K_array)

    # if all elements in status_array are 0, double K max
    if all(v == 0 for v in status_array):
        print('None of the Ks were successful. Lets double K max.')
        logging.info('None of the Ks were successful. Lets double K max.')
        K_array[0] = K_array[4] + 5
        K_array[4] = K_array[4] * 2
    else:
        print('K=' + str(K_array[index]) + ' was successful.')
        # the successful K will now be K max in the K_array
        K_array[4] = K_array[index]
        K_array[0] = K_array[index-1]
    
    # set other K's in K_array equally spaced between 5 and K max
    K_array[2] = (K_array[0] + (K_array[4]-K_array[0])/2)
    # round K's to nearest multiple of 5
    K_array[2] = round(K_array[2]/5)*5
    K_array[1] = (K_array[2] - K_array[0])/2
    K_array[1] = round(K_array[1]/5)*5
    K_array[1] = K_array[0] + K_array[1]
    K_array[3] = (K_array[4] - K_array[2])/2
    K_array[3] = round(K_array[3]/5)*5
    K_array[3] = K_array[2] + K_array[3]
    
    status_array = np.zeros((5))
    status_array[4] = 1


    print('New K_array: ' + str(K_array))
    logging.info('New K_array: ' + str(K_array))
    # if K_array contains duplicates
    if len(K_array) != len(set(K_array)):
        print("K_array contains duplicates, but don't worry, we will only run the simulations once.")
    return K_array





def check_if_done():
    # go through status_dict
    # sort status_dict by key
    #global status_array
    g = open("status_dict.json", "r")
    st_dict = json.load(g)
    #status_dict = st_dict['status_dict']
    status_dict = dict(st_dict)
    status_dict = {int(k):v for k,v in status_dict.items()}
    status_dict = {k: v for k, v in sorted(status_dict.items(), key=lambda item: item[0])}
    #print(status_dict)
    for key, value in status_dict.items():
        # if 5 is the best K
        if value == 1 and (key - 5) <= 0:
            print('The best force constant has been found. The force constant is ' + str(key) + '.')
            logging.info('The best force constant has been found. The force constant is ' + str(key) + '.')
            return 1,key
        elif value == 1:
            if key-5 in status_dict:
                if status_dict[key-5] == 0:
                    print('The best force constant has been found. The force constant is ' + str(key) + '.')
                    logging.info('The best force constant has been found. The force constant is ' + str(key) + '.')
                    return 1,key
    return 0,0


    # if status_array[1] == 1 and K_array[1] - K_array[0] <= 5:
    #     print('The best force constant has been found. The force constant is ' + str(K_array[1]) + '.')
    #     logging.info('The best force constant has been found. The force constant is ' + str(K_array[1]) + '.')
    #     return 1,K_array[1]
    # elif status_array[2] == 1 and K_array[2] - K_array[1] <= 5:
    #     print('The best force constant has been found. The force constant is ' + str(K_array[2]) + '.')
    #     logging.info('The best force constant has been found. The force constant is ' + str(K_array[2]) + '.')
    #     return 1,K_array[2]
    # elif status_array[3] == 1 and K_array[3] - K_array[2] <= 5:
    #     print('The best force constant has been found. The force constant is ' + str(K_array[3]) + '.')
    #     logging.info('The best force constant has been found. The force constant is ' + str(K_array[3]) + '.')
    #     return 1,K_array[3]
    # else:
    #     print('The best force constant has not yet been found.')
    #     return 0,0





def run_eq(domain: string, iter: int):
    f = open("gro_file.json", "r")
    gro_dict = json.load(f)
    gro_file = gro_dict['gro_file']
    file_name = 'pull_eq_' + str(domain) + str(iter)
    mdp_file = 'pull_eq.mdp'
    jobname = 'eq_' + str(domain)
    output = 'eq_' + str(domain)

    bash_command("cd iteration{}".format(iter))
    bash_command("mkdir -p eq")
    bash_command("cd ..")

    #delete last 2 lines of mdp file
    lines = open(mdp_file, 'r').readlines()
    del lines[-2:]

    f = open("start.json", "r")
    start = json.load(f)
    current_coord = start['start']
    range_high = current_coord + 0.25
    range_low = current_coord - 0.25

    #insert new lines into mdp file
    lines.append("pull_coord1_init = " + str(range_high) + "\n")
    lines.append("pull_coord2_init = " + str(range_low))
    open(mdp_file, 'w').writelines(lines)

    bash_command("gmx_mpi grompp -f pull_eq.mdp -o {}.tpr -c {} -r {} -p topol.top -n {} -maxwarn {}".format(file_name, gro_file, gro_file, cfg.ndx, cfg.maxwarn))
    time.sleep(7)
    write_batch(file_name, 'sbatch.sh')
    bash_command("sbatch -J {} -o {} sbatch.sh".format(jobname, output))
    print("Equilibration {} submitted".format(file_name))
    logging.info("Equilibration {} submitted".format(file_name))
    sys.exit()

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
    



# Ask if the user wants to continue to the next iteration of the simulation
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




# Unnecessary #

# # Ask the user if they want to remove unnecessary files
# def cleanup():
#     print("Removing files from the unsuccessful simulations is recommended.")
#     # ask user if they want to remove files
#     answer = input("Do you want to remove files? (y/n)")
#     if answer == "y":
#         print("Removing files...")
#         logging.info('User chose to remove files.')
#         # remove files
#     if answer == "n":
#         print("Not removing files.")
#         # do not remove files
#     else:    
#         print("Invalid answer. Please try again.")
#         cleanup()




# Make plots for pull COM and pull force
def pull_plot(pullx_file, pullf_file):
    bash_command("mkdir -p outputs ")
    x,y = np.loadtxt(pullx_file,comments=["@","#"],unpack=True)
    n=math.ceil(0.8*len(x))
    x=x[-n:]
    y=y[-n:]
    figure = plt.figure(figsize=(6,3))
    ax = figure.add_subplot(111)
    ax.plot(x, y)
    ax.set_xlim(x[0], x[-1])
    ax.set_xlabel("Time (ps)")
    ax.set_ylabel("COM")
    ax.set_title("Pull COM")
    figure.tight_layout()
    pullx_file = pullx_file[:-4]
    plt.savefig('outputs/{}.png'.format(pullx_file))
    #plt.show()

    x,y = np.loadtxt(pullf_file,comments=["@","#"],unpack=True)
    n=math.ceil(0.8*len(x))
    x=x[-n:]
    y=y[-n:]
    figure = plt.figure(figsize=(6,3))
    ax = figure.add_subplot(111)
    ax.plot(x, y)
    ax.set_xlim(x[0], x[-1])
    ax.set_xlabel("Time (ps)")
    ax.set_ylabel("Pull force")
    ax.set_title("Pull force for COM pulling")
    figure.tight_layout()
    pullf_file = pullf_file[:-4]
    plt.savefig('outputs/{}.png'.format(pullf_file))
    #plt.show()



# Analyze the rmsd plot and determine if the equilibration was successful
def analyze(file, domain):
    x,y = np.loadtxt(file,comments=["@","#"],unpack=True)
    n=math.ceil(0.8*len(x))
    x=x[-n:]
    y=y[-n:]
    slope=linregress(x,y).slope
    slope=float('{:f}'.format(slope))  
    #print("Slope:", slope)         #Write slope into output file
    if slope < 0.25 and slope > -0.25:
        res=1
    else:
        res=0
    figure = plt.figure(figsize=(6,3))
    ax = figure.add_subplot(111)
    ax.plot(x, y)
    ax.set_xlim(x[0], x[-1])
    ax.set_ylim(0, 2)
    ax.set_xlabel("Time (ns)")
    ax.set_ylabel("RMSD (Å)")
    ax.set_title("RMSD: Equilibration of {} domain".format(domain))
    figure.tight_layout()
    plt.savefig('rmsd.png')
    plt.show()
    if res == 0:
        #print("The equilibration wasn't successful. The structure isn't equilibrated enough.")
        return 0
    else:
        #print("The equilibration was successful.")
        return 1


# Not in use
# def main():
#     for domain in cfg.domains:
#         domain_dict = cfg.domains[domain]
#         for i in cfg.imports:
#             bash_command("{}".format(i))
#         global start
#         start = domain_dict['start']
#         global used_Ks
#         iterations is the difference in the start and end values
#         iterations = abs(domain_dict['target'] - domain_dict['start'])
#         for i in range(int(iterations)):
#             set 5 different K's
#             global K_array
#             K_array = np.array([5, 20, 30, 40, 50])
#             global status_array
#             res = 0
#             while res == 0:
#                 for j in range(5):
#                     if K_array[j] is not in used_Ks, run simulation
#                     if K_array[j] not in used_Ks and K_array[j]>0:
#                         if domain_dict["direction"] == "pull":
#                             sign=1
#                         elif domain_dict["direction"] == "push":
#                             sign=-1
#                         run_pull(i, K_array[j], domain_dict["name"], sign)
#                 print("Running simulations for domain " + domain_dict["name"] + " iteration " + str(i))
#                 logging.info("Running simulations for domain " + domain_dict["name"] + " iteration " + str(i))
#                 np.append(used_Ks, K_array)
#                 remove duplicates from used_Ks
#                 used_Ks = np.unique(used_Ks)

#                 # wait for jobs in mahti to finish
#                 time.sleep(20)
#                 print("The simulations should now be running. Wait for them to finish.")
#                 print("The program will now stop running.")
#                 sys.exit()

#                 for j in range(5):
#                     status(j, K_array[j], domain_dict["name"], i)

#                 res, best_K = check_if_done()
#                 if res == 1:
#                     global gro_file
#                     gro_file = 'pull_' + domain_dict["name"] + str(i) + '_' + str(best_K) + '.gro'
#                     global route
#                     route += domain_dict["name"] + "/iteration_" + str(i) + "/K_" + str(best_K)
#                     pullf = "pull_" + domain_dict["name"] + str(i) + "_" + str(best_K) + "f.xvg"
#                     pullx = "pull_" + domain_dict["name"] + str(i) + "_" + str(best_K) + "x.xvg"
#                     pull_plot(pullx, pullf)
#                     print("The best force constant has been found.")
#                     logging.info("The best force constant has been found.")
#                 else:
#                     new_K(status_array, K_array)
                    

#             gro_file = "pull_" + domain_dict["name"] + str(i) + ".gro"
#             run_eq(domain_dict["name"], i)

#             if i != int(iterations):
#                 cleanup()
#                 ask_continue()
#             else:
#                 print("That was the last iteration. The program will stop now.")
#                 logging.info("That was the last iteration. The program will stop now.")

#             gro_file = "pull_eq_" + domain_dict["name"] + str(i) + ".gro"




# Start a new iteration
def init(iter: int, idx: int):
    iter = int(iter)
    read_config()
    # for first iteration
    if iter == 0:
        gro_dict = {"gro_file": cfg.gro}
        with open("gro_file.json", "w") as f:
            json.dump(gro_dict, f, indent=4)
        start_dict = {"start": cfg.domains[0]["start"]}
        with open("start.json", "w") as f:
            json.dump(start_dict, f, indent=4)
    K_array = np.array([5, 0, 0, 0, 0])
    K_array[4] = cfg.domains[int(idx)]["K_max"]
    K_array[2] = (K_array[0] + (K_array[4]-K_array[0])/2)
    # round K's to nearest multiple of 5
    K_array[2] = round(K_array[2]/5)*5
    K_array[1] = (K_array[2] - K_array[0])/2
    K_array[1] = round(K_array[1]/5)*5
    K_array[1] = K_array[0] + K_array[1]
    K_array[3] = (K_array[4] - K_array[2])/2
    K_array[3] = round(K_array[3]/5)*5
    K_array[3] = K_array[2] + K_array[3]
    print("K_array: ", K_array)
    K_dict = {"K_array": K_array.tolist()}
    status_dict = {}
    used_Ks = {"used_Ks": []}
    with open("used_Ks.json", "w") as f:
       json.dump(used_Ks, f, indent=4)
    with open("K_array.json", "w") as f:
       json.dump(K_dict, f, indent=4)
    with open("status_dict.json", "w") as f:
       json.dump(status_dict, f, indent=4)
    run_simulation(iter, cfg.domains[int(idx)], K_array)
    
    
    


def run_simulation(iter: int, dom: str, K_array: np.array):
    domain_dict = dom
    global start
    # if directory doesnt exist, create it
    if not os.path.exists("iteration{}".format(iter)):
        bash_command("mkdir -p iteration{}".format(iter))
    for j in range(len(K_array)):
        if K_array[j]>0:
            if domain_dict["direction"] == "pull":
                sign=1.0
            elif domain_dict["direction"] == "push":
                sign=-1.0
            f = open("start.json", "r")
            start_dict = json.load(f)
            start = start_dict['start']
            start = float(start) + float(iter)*1.0*sign + 1.5*sign
            run_pull(iter, K_array[j], domain_dict["name"])
    print("Running simulations for domain " + domain_dict["name"] + " iteration " + str(iter) + " with K= " + str(K_array))
    logging.info("Running simulations for domain " + domain_dict["name"] + " iteration " + str(iter))
    f = open("used_Ks.json", "r")
    used_dict = json.load(f)
    used_Ks = used_dict['used_Ks']
    # convert used_Ks elements to int
    used_Ks = [int(i) for i in used_Ks]
    used_Ks = np.append(used_Ks, K_array)
    # remove duplicates from used_Ks
    used_Ks = np.unique(used_Ks)
    used_dict = {"used_Ks": used_Ks.tolist()}
    with open("used_Ks.json", "w") as f:
        json.dump(used_dict, f, indent=4)

    ## wait for jobs in mahti to finish
    time.sleep(10)
    print("The simulations should now be running. Check that the simulations look correct. Wait for them to finish.")
    print("The program will now stop running.")
    sys.exit()


def contpull(iter: int, dom: str, idx: int):
    domain_dict = dom
    global status_dict
    f = open("K_array.json", "r")
    K_dict = json.load(f)
    K_array = K_dict['K_array']
    K_array = np.array(K_array)
    g = open("status_dict.json", "r")
    st_dict = json.load(g)
    #print(st_dict)
    #status_dict = st_dict['status_dict']
    status_dict = dict(st_dict)
    h = open("used_Ks.json", "r")
    used_dict = json.load(h)
    used_Ks = used_dict['used_Ks']
    # convert used_Ks elements to int
    used_Ks = [int(i) for i in used_Ks]
    K_array_unique = np.unique(K_array)
    K_filtered = []
    for i in K_array_unique:
        if i not in used_Ks:
            K_filtered.append(i)
    K_filtered = np.array(K_filtered)
    for j in K_filtered:
        bash_command("[ -e pull_{}{}_{}.* ] && mv pull_{}{}_{}.* iteration{}/K={}".format(dom,iter,K_filtered[j],dom,iter,K_filtered[j],iter,K_filtered[j]))
        bash_command("[ -e pull_{}{}_{}x.xvg ] && mv pull_{}{}_{}x.xvg iteration{}/K={}".format(dom,iter,K_filtered[j],dom,iter,K_filtered[j],iter,K_filtered[j]))
        bash_command("[ -e pull_{}{}_{}f* ] && mv pull_{}{}_{}f* iteration{}/K={}".format(dom,iter,K_filtered[j],dom,iter,K_filtered[j],iter,K_filtered[j]))
        bash_command("[ -e pull_{}{}_{}_prev.cpt ] && mv pull_{}{}_{}_prev.cpt iteration{}/K={}".format(dom,iter,K_filtered[j],dom,iter,K_filtered[j],iter,K_filtered[j]))
        status(j, K_filtered[j], domain_dict, iter)
    #print(status_dict)
    #print(status_dict['status_dict'])
    status_dict = {int(k):v for k,v in status_dict.items()}
    status_dict = {k:status_dict[k] for k in sorted(status_dict)}
    print("status_dict: ", status_dict)
    #status_dict={"status_dict": status_dict}
    with open("status_dict.json", "w") as f:
        json.dump(status_dict, f, indent=4)

    res, best_K = check_if_done()
    if res == 1:
        gro_file = 'pull_' + domain_dict + str(iter) + '_' + str(best_K) + '.gro'
        gro_dict = {"gro_file": gro_file}
        with open("gro_file.json", "w") as f:
            json.dump(gro_dict, f, indent=4)
        #global route
        #route += domain_dict + "/iteration_" + str(iter) + "/K_" + str(best_K)
        pullf = "pull_" + domain_dict + str(iter) + "_" + str(best_K) + "f.xvg"
        pullx = "pull_" + domain_dict + str(iter) + "_" + str(best_K) + "x.xvg"
        bash_command("cp iteration{}/K={}/{} .".format(iter, best_K, pullf))
        bash_command("cp iteration{}/K={}/{} .".format(iter, best_K, pullx))
        pull_plot(pullx, pullf)
        #print("The best force constant has been found.")
        logging.info("The best force constant has been found.")
        bash_command("cp iteration{}/K={}/{} .".format(iter, best_K, gro_file))
    else:
        print("The best force constant has not been found yet.")
        K_array = new_K(status_dict, K_array)
        K_dict = {"K_array": K_array.tolist()}
        #st_dict = {"status_dict": status_dict}
        print("Used Ks: {}".format(used_Ks))
        # remove duplicates from K_array
        K_array_unique = np.unique(K_array)
        print("K_array_unique: {}".format(K_array_unique))
        K_filtered = []
        for i in K_array_unique:
            if i not in used_Ks:
                K_filtered.append(i)
        K_filtered = np.array(K_filtered)
        print("K_filtered: {}".format(K_filtered))
        def ask_cont():
            answer = input("Do you wish to run simulations with these new force constants? (y/n)")
            if answer == "y":
                print("You answered yes. Continuing to simulations...")
                logging.info('User chose to continue to simulations.')
                with open("K_array.json", "w") as f:
                    json.dump(K_dict, f, indent=4)
                with open("status_dict.json", "w") as f:
                    json.dump(status_dict, f, indent=4)
                run_simulation(iter, cfg.domains[int(idx)], K_filtered)
            elif answer == "n":
                print("You answered no. Exiting...")
                logging.info('User chose not to continue. Exiting program.')
                sys.exit()
            else:
                print("Invalid answer. Please try again.")
                ask_cont()
        ask_cont()

    # assume that the sim was successful for some K
    # ask if the user wants to run equilibration
    #print("The best force constant has been found.")
    def ask_eq():
        answer = input("Do you want to run equilibration? (y/n)")
        if answer == "y":
            print("You answered yes. Continuing to equilibration...")
            logging.info('User chose to continue to equilibration.')
            f = open("start.json", "r")
            start = json.load(f)
            current_coord = start['start'] + 1.0
            start_dict = {"start": current_coord}
            with open("start.json", "w") as f:
                json.dump(start_dict, f, indent=4)
            run_eq(domain_dict, iter)
        elif answer == "n":
            print("You answered no. Exiting...")
            logging.info('User chose not to continue. Exiting program.')
            sys.exit()
        else:
            print("Invalid answer. Please try again.")
            ask_eq()
    ask_eq()


# Continue simulations
# First check status and check if done
def conteq(iter: int, dom: string):
    # check if the equilibration is done
    file_name = 'pull_eq_' + str(dom) + str(iter)
    command="gmx_mpi rms -s {}.tpr -f {}.xtc -o {}_rmsd.xvg -tu ns".format(file_name, file_name, file_name)
    subprocess.run([command], input="4 4", text=True, shell=True, executable='/bin/bash')

    rmsd_xvg_file = file_name + '_rmsd.xvg'
    # from analyze.py use function analyze
    result=analyze(rmsd_xvg_file, dom)
    print("Result: ", result)
    if result == 0:
        print("Running equilibration again with longer wall time")
        logging.info("Running equilibration again with longer wall time")
        wall_time()
        run_eq(dom, iter)
    else:
        print("Equilibration was successful")
        logging.info("Equilibration was successful")
        gro_file = 'pull_eq_' + dom + str(iter) + '.gro'
        gro_dict = {"gro_file": gro_file}
        with open("gro_file.json", "w") as f:
            json.dump(gro_dict, f, indent=4)


if __name__ == '__main__':
    args = sys.argv
    globals()[args[1]](*args[2:])