#!/usr/bin/env python3


# Imports
import subprocess
import string
#import config as cfg
import configparser
import numpy as np
import sys
import logging
import time
import os
import matplotlib.pyplot as plt
from scipy.stats import linregress
import math
import json


# set up variables from config file (config.ini)
config = configparser.ConfigParser()
config.read("config.ini")
ndx = config['FILES']['ndx']
topol = config['FILES']['topol']
mdp = config['FILES']['pull_mdp']
eq_mdp = config['FILES']['eq_mdp']
gro = config['FILES']['gro']
maxwarn = config['FILES']['maxwarn']
deltax = float(config['COORD1']['deltax'])
run_multiple = config['COPIES']['run_multiple']
if run_multiple == 'True':
    run_multiple = True
else:
    run_multiple = False
num_of_copies = int(config['COPIES']['num_of_copies'])
eq_range = float(config['COORD1']['eq_range'])


# Logging
# TODO - logging is not implemented completely yet
logging.basicConfig(filename='log_pathfinder.log', level=logging.DEBUG)
logging.info('Starting program')


# A function for running bash commands
def bash_command(cmd):
    subprocess.Popen(cmd, shell=True, executable='/bin/bash', stdin=None, stdout=None, stderr=None)



# Help function for the user
# Prints all commands and their arguments
# Prints the last command that was run
def help():
    print("This is a help message")
    print("\nAll commands start with 'python pathfinder.py' followed by the command and arguments")
    print("Commands:")
    print("\thelp - prints this message")
    print("\tinit 'iter' - initializes the simulation")
    print("\tcontpull 'iter' - continues from the previous pulling simulation")
    print("\tconteq 'iter' - continues from the previous equilibration simulation")
    with open('last_command.json', 'r') as f:
        last_command = json.load(f)
    print("\nThe latest command you ran was: " + last_command['last_command'])



# Error handling for inputs and config file
# Stops the program if there is an error in the inputs or config file
def read_config():

    # check that index file has ndx suffix
    if config['FILES']['ndx'][-4:] != '.ndx':
        print('The index file must have the suffix .ndx')
        logging.error('The index file does not have the suffix .ndx')
        sys.exit()

    # check that gro file has gro suffix
    if config['FILES']['gro'][-4:] != '.gro':
        print('The gro file must have the suffix .gro')
        logging.error('The gro file does not have the suffix .gro')
        sys.exit()

    # check that mdp file has mdp suffix
    if config['FILES']['pull_mdp'][-4:] != '.mdp':
        print('The mdp file must have the suffix .mdp')
        logging.error('The mdp file does not have the suffix .mdp')
        sys.exit()

    # check that the config file has a COORD1 section
    if 'COORD1' not in config:
        print('The config file must have a COORD1 section, at least one coordinate must be specified')
        logging.error('The config file does not have a COORD1 section')
        sys.exit()

    # check that the number of copies is greater than 0
    if config['COPIES']['run_multiple'] == True and config['COPIES']['num_of_copies'] < 1:
        print('The number of copies must be greater than 0')
        logging.error('The number of copies is less than 1')
        sys.exit()

    # check that the number of copies is less than 5
    # this is to avoid running too many simulations at once
    # 5 is completely arbitrary and can be changed
    if config['COPIES']['run_multiple'] == True and config['COPIES']['num_of_copies'] > 5:
        print("That's too many copies, please choose a number between 1 and 5")
        logging.error('The number of copies is greater than 5')
        sys.exit()





# Write gromacs mdrun command to the batch file
def write_batch(file_name: string, sbatch: string):
    command = 'srun gmx_mpi mdrun -deffnm {} -pf {}f.xvg -px {}x.xvg'.format(file_name, file_name, file_name)
    # remove last line from sbatch.sh
    with open(sbatch, 'r') as f:
        lines = f.readlines()
    with open(sbatch, 'w') as f:
        for line in lines[:-1]:
            f.write(line)
    # add command into the end of sbatch.sh
    with open(sbatch, 'a') as f:
        f.write(command)
    


# Doubles the number of steps in mdp file when equilibration wasn't successful
def longer_time(mdp_file: string):
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




# Set up and run a pulling simulation
# Runs individual simulations for each K
# First runs grompp, and then sbatch
def run_pull(iter: int, K: int, domain: str):
    file_name = 'pull_' + str(domain) + str(iter) + '_' + str(K)
    batch = 'sbatch.sh'
    jobname = str(domain) + str(iter) + '_' + str(K)
    output = 'pull_' + str(domain) + str(iter) + '_' + str(K) + '.out'

    lines = open(mdp, 'r').readlines()
    lines[-1] = "\npull_coord1_k = " + str(K) 
    global start
    lines[-2] = "pull_coord1_init = " + str(start)
    open(mdp, 'w').writelines(lines)

    f = open("gro_file.json", "r")
    gro_dict = json.load(f)
    gro_file = gro_dict['gro_file']

    # If run_multiple in config is True, run multiple copies of the simulation
    if run_multiple == True:
        print("Running multiple copies of the simulation")
        for copy in range(1, num_of_copies + 1):
            file_name = 'pull_' + str(domain) + str(iter) + '_' + str(K) + '_' + str(copy)
            jobname = str(domain) + str(iter) + '_' + str(K) + '_' + str(copy)
            output = 'pull_' + str(domain) + str(iter) + '_' + str(K) + '_' + str(copy) + '.out'
            bash_command("gmx_mpi grompp -f pull.mdp -o {}.tpr -c {} -r {} -p topol.top -n {} -maxwarn {}".format(file_name, gro_file, gro_file, ndx, maxwarn))
            # sleep commands so that grompps are finished before mdruns are submitted
            time.sleep(9)
            write_batch(file_name, batch)
            bash_command("sbatch -J {} -o {} {}".format(jobname, output, batch))
    else:
        bash_command("gmx_mpi grompp -f pull.mdp -o {}.tpr -c {} -r {} -p topol.top -n {} -maxwarn {}".format(file_name, gro_file, gro_file, ndx, maxwarn))
        # sleep commands so that grompps are finished before mdruns are submitted
        time.sleep(7)
        write_batch(file_name, batch)
        bash_command("sbatch -J {} -o {} {}".format(jobname, output, batch))
    print("Running {} with K = {}".format(file_name, K))
    time.sleep(10)

    # Make directory for each K
    if not os.path.exists("K={}".format(K)):
        bash_command("mkdir -p iteration{}/K={}".format(iter, K))




# Determine status (0 or 1) for each K separately
# 0 means K wasn't able to pull/push, and 1 means
def status(K: int, domain: string, iter: int):
    # status_dict is a dictionary that stores the status (success) of each K
    global status_dict
    # Check status of copies
    if run_multiple == True:
        for copy in range(1, num_of_copies + 1):
            file_name = 'iteration' + str(iter) + '/K=' + str(K) + '/pull_' + str(domain) + str(iter) + '_' + str(K) + '_' + str(copy) + 'x.xvg'
            file_name = file_name.replace(" ", "")
            file_name = file_name.strip()

            # Check if the difference between the first and last distance in xvg file is greater than deltax nm (status=1)
            if os.path.exists(file_name):
                # get first distance
                with open(file_name, 'r') as f:
                    for i, line in enumerate(f):
                        if i == 17:
                            line = line.split()
                            first_dist = line[1]
                # get last distance
                with open(file_name, 'r') as f:
                    for i, line in enumerate(f):
                        pass
                    line = line.split()
                    try:
                        last_dist = line[1]
                    except IndexError:
                        print("The last line in the distance xvg file is odd. Please check the xvg file. Did the simulation finish correctly?")
                        logging.error("The last line in the distance xvg file is not complete")
                        sys.exit()

                # check if the difference between the first and last distance is greater than deltax-0.1
                # delta-0.1 to give some leeway for pulling, e.g. for deltax=1, 0.9nm is usually acceptable
                if abs(float(last_dist) - float(first_dist)) >= deltax-0.1 and config["COORD1"]["direction"] == "pull":
                    print('The pulling of the ' + str(domain) + ' domain with ' + str(K) + '(copy: ' + str(copy) + ') was successful.')
                    logging.info('The pulling of the ' + str(domain) + ' domain with ' + str(K) + '(copy: ' + str(copy) + ') was successful.')
                    # set status of this K to 1
                    status_dict[int(K)]=1
                    bash_command("cd ../..")
                elif abs(float(first_dist) - float(last_dist)) >= deltax-0.1 and config["COORD1"]["direction"] == "push":
                    print('The pulling of the ' + str(domain) + ' domain with ' + str(K) + '(copy: ' + str(copy) + ') was successful.')
                    logging.info('The pulling of the ' + str(domain) + ' domain with ' + str(K) + '(copy: ' + str(copy) + ') was successful.')
                    # set status of this K to 1
                    status_dict[int(K)]=1
                    bash_command("cd ../..")
                else:
                    print('The pulling of the ' + str(domain) + ' domain with ' + str(K) + '(copy: ' + str(copy) + ') was not successful.')
                    logging.info('The pulling of the ' + str(domain) + ' domain with ' + str(K) + '(copy: ' + str(copy) + ') was not successful.')
                    # set status of this K to 0, unless it has already been set to 1
                    if int(K) in status_dict:
                        if status_dict[int(K)] != 1:
                            status_dict[int(K)]=0 
                    else:
                        status_dict[int(K)]=0
                    bash_command("cd ../..")
            else:
                print('The xvg file does not exist')
                logging.error('The xvg file does not exist')

    # Check status of a single copy
    else:
        file_name = 'iteration' + str(iter) + '/K=' + str(K) + '/pull_' + str(domain) + str(iter) + '_' + str(K) + 'x.xvg'
        file_name = file_name.replace(" ", "")

        # Check if the difference between the first and last distance in xvg file is greater than 0.9 nm (status=1)
        if os.path.exists(file_name):
            # get first distance
            with open(file_name, 'r') as f:
                for i, line in enumerate(f):
                    if i == 17:
                        line = line.split()
                        first_dist = line[1]
            # get last distance
            with open(file_name, 'r') as f:
                for i, line in enumerate(f):
                    pass
                line = line.split()
                try:
                    last_dist = line[1]
                except IndexError:
                    print("The last line in the distance xvg file is odd. Please check the xvg file. Did the simulation finish correctly?")
                    logging.error("The last line in the distance xvg file is not complete")
                    sys.exit()

            # check if the difference between the first and last distance is greater than deltax-0.1
            # delta-0.1 to give some leeway for pulling, e.g. for deltax=1, 0.9nm is usually acceptable
            if abs(float(last_dist) - float(first_dist)) >= deltax-0.1 and config["COORD1"]["direction"] == "pull":
                print('The pulling of the ' + str(domain) + ' domain with ' + str(K) + ' was successful.')
                logging.info('The pulling of the ' + str(domain) + ' domain with ' + str(K) + ' was successful.')
                # set status of this K to 1
                status_dict[int(K)]=1
                bash_command("cd ../..")
            elif abs(float(first_dist) - float(last_dist)) >= deltax-0.1 and config["COORD1"]["direction"] == "push":
                print('The pulling of the ' + str(domain) + ' domain with ' + str(K) + ' was successful.')
                logging.info('The pulling of the ' + str(domain) + ' domain with ' + str(K) + ' was successful.')
                # set status of this K to 1
                status_dict[int(K)]=1
                bash_command("cd ../..")
            else:
                print('The pulling of the ' + str(domain) + ' domain with ' + str(K) + ' was not successful.')
                logging.info('The pulling of the ' + str(domain) + ' domain with ' + str(K) + ' was not successful.')
                # set status of this K to 0
                status_dict[int(K)]=0
                bash_command("cd ../..")
        else:
            print('The xvg file does not exist')
            logging.error('The xvg file does not exist')




# Determine/calculate new K values for next set of simulations
def new_K(status_array, K_array):
    # Check which K was successful
    # This will determine the new K max and the rest of the Ks
    index=0
    status_array = dict(status_array)
    K_array = list(K_array)
    for key, value in status_array.items():
        if value == 1:
            index = K_array.index(key)
            break
    K_array = np.array(K_array)

    # if all elements in status_array are 0, double K max
    if all(v == 0 for v in status_array.values()):
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
    
    # reset status_array
    status_array = np.zeros((5))
    status_array[4] = 1

    print('New K_array: ' + str(K_array))
    logging.info('New K_array: ' + str(K_array))
    # if K_array contains duplicates
    if len(K_array) != len(set(K_array)):
        print("K_array contains duplicates, but don't worry, we will only run simulations for each K once.")
    return K_array



# Check if the best K has been found
def check_if_done():
    # go through status_dict and sort it by K (ascending)
    g = open("status_dict.json", "r")
    st_dict = json.load(g)
    status_dict = dict(st_dict)
    status_dict = {int(k):v for k,v in status_dict.items()}
    status_dict = {k: v for k, v in sorted(status_dict.items(), key=lambda item: item[0])}

    for key, value in status_dict.items():
        # if the smallest K is the best K
        if value == 1 and list(status_dict).index(key) == 0:
            print('The best force constant has been found. The force constant is ' + str(key) + '. This is the K_min. ')
            print('It is possible there exists and even smaller force constant, but Pathfinder will not check for it, because this was K_min in the config file.')
            logging.info('The best force constant has been found. The force constant is ' + str(key) + '.')
            return 1,key
        elif value == 1:
            if key-5 in status_dict:
                if status_dict[key-5] == 0:
                    print('The best force constant has been found. The force constant is ' + str(key) + '.')
                    logging.info('The best force constant has been found. The force constant is ' + str(key) + '.')
                    return 1,key
    return 0,0




# Run equilibration simulations for a domain
def run_eq(domain: string, iter: int):
    # set up variables and file names
    f = open("gro_file.json", "r")
    gro_dict = json.load(f)
    gro_file = gro_dict['gro_file']
    file_name = 'pull_eq_' + str(domain) + str(iter)
    jobname = 'eq_' + str(domain)
    output = 'eq_' + str(domain) + '.out'

    # make directory for equilibration
    bash_command("cd iteration{}".format(iter))
    bash_command("mkdir -p iteration{}/eq".format(iter))
    bash_command("cd ..")

    #delete last 2 lines of mdp file
    lines = open(eq_mdp, 'r').readlines()
    del lines[-2:]

    # set up equilibration range
    f = open("start.json", "r")
    start = json.load(f)
    current_coord = start['start']
    range_high = float(current_coord) + eq_range
    range_low = float(current_coord) - eq_range

    #insert new lines with equilibration range into mdp file
    lines.append("pull_coord1_init = " + str(range_high) + "\n")
    lines.append("pull_coord2_init = " + str(range_low))
    open(eq_mdp, 'w').writelines(lines)

    # run grompp and mdrun for equilibration
    bash_command("gmx_mpi grompp -f eq.mdp -o {}.tpr -c {} -r {} -p topol.top -n {} -maxwarn {}".format(file_name, gro_file, gro_file, ndx, maxwarn))
    time.sleep(7)
    write_batch(file_name, 'sbatch.sh')
    bash_command("sbatch -J {} -o {} sbatch.sh".format(jobname, output))
    print("Equilibration {} submitted".format(file_name))
    logging.info("Equilibration {} submitted".format(file_name))
    sys.exit()
    



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



# Analyze the rmsd plot slope and determine if the equilibration was successful
def analyze(file, domain, iter):
    x,y = np.loadtxt(file,comments=["@","#"],unpack=True)
    n=math.ceil(0.8*len(x))
    x=x[-n:]
    y=y[-n:]
    slope=linregress(x,y).slope
    slope=float('{:f}'.format(slope))  
    # if slope is less than 0.25 and greater than -0.25, equilibration was successful
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
    ax.set_title("RMSD: Equilibration of {} domain iteration {}".format(domain, iter))
    figure.tight_layout()
    plt.savefig('{}{}_rmsd.png'.format(domain, iter))
    plt.show()
    return res





# Start a new iteration
def init(iter: int):
    iter = int(iter)
    read_config()
    # for first iteration
    # create json files to store variables for later use

    if iter == 0:
        # gro_file has the name of the current gro file, will change with each iteration
        gro_dict = {"gro_file": gro}
        with open("gro_file.json", "w") as f:
            json.dump(gro_dict, f, indent=4)
        # start has the starting coordinate for the next iteration, will increase/decrease with deltax with each iteration
        start_dict = {"start": config['COORD1']["start"]}
        with open("start.json", "w") as f:
            json.dump(start_dict, f, indent=4)
        # last_command has the last command that was executed, can help with debugging and the user
        last_command = {"last_command": "init " + str(iter)}
        with open("last_command.json", "w") as f:
            json.dump(last_command, f, indent=4)
    
    # create starting K_array, where K_min and K_max come from config file
    K_min = config['COORD1']["K_min"]
    K_max = config['COORD1']["K_max"]
    K_array = np.array([int(K_min), 0, 0, 0, int(K_max)])
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
    # if K_array contains duplicates
    if len(K_array) != len(set(K_array)):
        print("K_array contains duplicates, but don't worry, we will only run simulations for each K once.")

    K_dict = {"K_array": K_array.tolist()}
    status_dict = {}
    used_Ks = {"used_Ks": []}
    # used_Ks is a list of K values that have already been used in the simulation of this iteration
    with open("used_Ks.json", "w") as f:
       json.dump(used_Ks, f, indent=4)
    # K_array is an array of the current K values 
    with open("K_array.json", "w") as f:
       json.dump(K_dict, f, indent=4)
    # status_dict is a dictionary of the status of each K value, currently full of zeros
    with open("status_dict.json", "w") as f:
       json.dump(status_dict, f, indent=4)

    run_simulation(iter, K_array)
    
    
    

# Run simulations for a coordinate with an array of K values (1-5 values)
def run_simulation(iter: int, K_array: np.array):
    domain_dict = config['COORD1']
    global start

    # if directory for this iteration doesnt exist, create it
    if not os.path.exists("iteration{}".format(iter)):
        bash_command("mkdir -p iteration{}".format(iter))
    for j in range(len(K_array)):
        if K_array[j]>0:
            # pull together
            if domain_dict["direction"] == "pull":
                sign=1.0
            # or push apart
            elif domain_dict["direction"] == "push":
                sign=-1.0
            f = open("start.json", "r")
            start_dict = json.load(f)
            start = start_dict['start']
            start = float(start) + float(config['COORD1']['deltax'])*sign + 0.1*sign
            # run simulation for this K value
            run_pull(iter, K_array[j], domain_dict["name"])

    print("Running simulations for system " + domain_dict["name"] + " iteration " + str(iter) + " with K= " + str(K_array))
    logging.info("Running simulations for system " + domain_dict["name"] + " iteration " + str(iter))

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


# Continue from a pulling simulation
# Check which simulations were successful and continue from there
# Either run new simulations with new Ks or continue to equilibration
def contpull(iter: int):
    # open json files and read variables
    domain_dict = config['COORD1']['name']
    dom = config['COORD1']['name']
    global status_dict
    last_command = {"last_command": "contpull " + str(iter)}
    with open("last_command.json", "w") as f:
        json.dump(last_command, f, indent=4)

    f = open("K_array.json", "r")
    K_dict = json.load(f)
    K_array = K_dict['K_array']
    K_array = np.array(K_array)

    g = open("status_dict.json", "r")
    st_dict = json.load(g)
    status_dict = dict(st_dict)

    h = open("used_Ks.json", "r")
    used_dict = json.load(h)
    used_Ks = used_dict['used_Ks']

    # convert used_Ks elements to int
    used_Ks = [int(i) for i in used_Ks]
    K_array_unique = np.unique(K_array)
    # print("K_array_unique: ", K_array_unique)
    # K_filtered = []
    # for i in K_array_unique:
    #     if i not in used_Ks:
    #         K_filtered.append(i)
    # K_filtered = np.array(K_filtered)
    # print("K_filtered: ", K_filtered)
    global K_filtered
    K_filtered = K_array_unique

    for j in range(len(K_filtered)):
        if run_multiple == True:
            for copy in range(1, num_of_copies + 1):
                # move files to their folders
                bash_command("if compgen -G pull_{}{}_{}_{}.* > /dev/null; then\nmv pull_{}{}_{}_{}.* iteration{}/K={}\nfi".format(dom,iter,K_filtered[j],copy,dom,iter,K_filtered[j],copy,iter,K_filtered[j]))
                bash_command("[[ -f pull_{}{}_{}_{}x.xvg ]] && mv pull_{}{}_{}_{}x.xvg iteration{}/K={}".format(dom,iter,K_filtered[j],copy,dom,iter,K_filtered[j],copy,iter,K_filtered[j]))
                bash_command("[[ -f pull_{}{}_{}_{}f.xvg ]] && mv pull_{}{}_{}_{}f.xvg iteration{}/K={}".format(dom,iter,K_filtered[j],copy,dom,iter,K_filtered[j],copy,iter,K_filtered[j]))
                bash_command("[[ -f pull_{}{}_{}_{}_prev.cpt ]] && mv pull_{}{}_{}_{}_prev.cpt iteration{}/K={}".format(dom,iter,K_filtered[j],copy,dom,iter,K_filtered[j],copy,iter,K_filtered[j]))
        else:
            # move files to their folders
            bash_command("if compgen -G pull_{}{}_{}.* > /dev/null; then\nmv pull_{}{}_{}.* iteration{}/K={}\nfi".format(dom,iter,K_filtered[j],dom,iter,K_filtered[j],iter,K_filtered[j]))
            bash_command("[[ -f pull_{}{}_{}x.xvg ]] && mv pull_{}{}_{}x.xvg iteration{}/K={}".format(dom,iter,K_filtered[j],dom,iter,K_filtered[j],iter,K_filtered[j]))
            bash_command("[[ -f pull_{}{}_{}f.xvg ]] && mv pull_{}{}_{}f.xvg iteration{}/K={}".format(dom,iter,K_filtered[j],dom,iter,K_filtered[j],iter,K_filtered[j]))
            bash_command("[[ -f pull_{}{}_{}_prev.cpt ]] && mv pull_{}{}_{}_prev.cpt iteration{}/K={}".format(dom,iter,K_filtered[j],dom,iter,K_filtered[j],iter,K_filtered[j]))
        # let the file moving finish
        time.sleep(3)
        # check the status of the simulations
        status(K_filtered[j], domain_dict, iter)

    status_dict = {int(k):v for k,v in status_dict.items()}
    status_dict = {k:status_dict[k] for k in sorted(status_dict)}
    print("status_dict: ", status_dict)
    with open("status_dict.json", "w") as f:
        json.dump(status_dict, f, indent=4)

    # Check if the best K has been found
    res, best_K = check_if_done()
    if res == 1:
        # make plots of the distance (x) and force (f) during the simulation
        pullf = "pull_" + domain_dict + str(iter) + "_" + str(best_K) + "f.xvg"
        pullx = "pull_" + domain_dict + str(iter) + "_" + str(best_K) + "x.xvg"
        bash_command("cp iteration{}/K={}/{} .".format(iter, best_K, pullf))
        bash_command("cp iteration{}/K={}/{} .".format(iter, best_K, pullx))
        # there is some error with the plotting, so for now it is commented out
        #pull_plot(pullx, pullf)

        logging.info("The best force constant has been found.")
        gro_file = 'pull_' + domain_dict + str(iter) + '_' + str(best_K) + '.gro'
        bash_command("cp iteration{}/K={}/{} .".format(iter, best_K, gro_file))
    else:
        print("The best force constant has not been found yet.")
        prev_Ks = {"prev_Ks": K_array.tolist()}
        with open("prev_Ks.json", "w") as f:
            json.dump(prev_Ks, f, indent=4)
        
        # get new Ks
        K_array = new_K(status_dict, K_array)
        K_dict = {"K_array": K_array.tolist()}
        # remove duplicates from K_array
        K_array_unique = np.unique(K_array)
        K_filtered = []
        for i in K_array_unique:
            if i not in used_Ks:
                K_filtered.append(i)
        K_filtered = np.array(K_filtered)
        print("K_filtered: {}".format(K_filtered))

        # function for asking if the user wants to continue to simulations with new Ks
        def ask_cont():
            answer = input("Do you wish to run simulations with these new force constants? (y/n)")
            if answer == "y":
                print("You answered yes. Continuing to simulations...")
                logging.info('User chose to continue to simulations.')
                global K_filtered
                K_array = {"K_array": K_filtered.tolist()}
                with open("K_array.json", "w") as f:
                    json.dump(K_array, f, indent=4)
                with open("status_dict.json", "w") as f:
                    json.dump(status_dict, f, indent=4)
                run_simulation(iter, K_filtered)
            elif answer == "n":
                print("You answered no. Exiting...")
                logging.info('User chose not to continue. Exiting program.')
                sys.exit()
            else:
                print("Invalid answer. Please try again.")
                ask_cont()
        ask_cont()



    # Assume that the sim was successful for some K
    # Ask if the user wants to run equilibration
    def ask_eq():
        answer = input("Do you want to run equilibration? (y/n)")
        if answer == "y":
            print("You answered yes. Continuing to equilibration...")
            logging.info('User chose to continue to equilibration.')

            file_name = 'iteration' + str(iter) + '/K=' + str(best_K) + '/pull_' + str(domain_dict) + str(iter) + '_' + str(best_K) + 'x.xvg'
            file_name = file_name.replace(" ", "")

            if os.path.exists(file_name):
                # get last distance
                with open(file_name, 'r') as f:
                    for i, line in enumerate(f):
                        pass
                    line = line.split()
                    last_dist = line[1]
                
            start_dict = {"start": last_dist}
            with open("start.json", "w") as f:
                json.dump(start_dict, f, indent=4)
            gro_file = 'pull_' + domain_dict + str(iter) + '_' + str(best_K) + '.gro'
            gro_dict = {"gro_file": gro_file}
            with open("gro_file.json", "w") as f:
                json.dump(gro_dict, f, indent=4)

            # equilibrate the system
            run_eq(domain_dict, iter)

        elif answer == "n":
            print("You answered no. Exiting...")
            logging.info('User chose not to continue. Exiting program.')
            sys.exit()
        else:
            print("Invalid answer. Please try again.")
            ask_eq()
    ask_eq()



# Continue simulations from the equilibration
# First check status and check if done
def conteq(iter: int):
    dom = config['COORD1']['name']
    last_command = {"last_command": "conteq " + str(iter)}
    with open("last_command.json", "w") as f:
        json.dump(last_command, f, indent=4)

    # check if the equilibration is done by computing the root mean square deviation (RMSD)
    file_name = 'pull_eq_' + str(dom) + str(iter)
    command="gmx_mpi rms -s {}.tpr -f {}.xtc -o {}_rmsd.xvg -tu ns".format(file_name, file_name, file_name)
    subprocess.run([command], input="4 4", text=True, shell=True, executable='/bin/bash')

    rmsd_xvg_file = file_name + '_rmsd.xvg'
    # analyze the slope of the RMSD with analyze function
    result=analyze(rmsd_xvg_file, dom, iter)
    print("Result: ", result)

    if result == 0:
        answer = input("Equilibration was not successful. Do you want to run it again with longer time? (y/n)")
        if answer == "y":
            print("Running equilibration again with longer time")
            logging.info("Running equilibration again with longer time")

            # double the time of the equilibration
            longer_time(eq_mdp)
            run_eq(dom, iter)

        elif answer == "n":
            print("You answered no. Exiting...")
            logging.info('User chose not to continue. Exiting program.')
            sys.exit()
    else:
        print("Equilibration was successful")
        logging.info("Equilibration was successful")

        # move the files from the equilibration simulation to the eq folder
        if not os.path.exists("iteration{}/eq".format(iter)):
            bash_command("mkdir -p iteration{}/eq".format(iter))
        bash_command("if compgen -G pull_eq_{}{}* > /dev/null; then\nmv pull_eq_{}{}* iteration{}/eq\nfi".format(dom,iter,dom,iter,iter))
        time.sleep(1)

        gro_file = 'pull_eq_' + dom + str(iter) + '.gro'
        gro_dict = {"gro_file": gro_file}
        with open("gro_file.json", "w") as f:
            json.dump(gro_dict, f, indent=4)
        # copy the gro file to the main folder
        bash_command("cp iteration{}/eq/{} .".format(iter, gro_file))

        # use the last distance in the equilibration as the starting coordinate for the next iteration
        file_name = 'iteration' + str(iter) + '/eq/pull_eq_' + dom + str(iter) + 'x.xvg'
        file_name = file_name.replace(" ", "")

        if os.path.exists(file_name):
            # get last distance
            with open(file_name, 'r') as f:
                for i, line in enumerate(f):
                    pass
                line = line.split()
                last_dist = line[1]
            
        start_dict = {"start": last_dist}
        with open("start.json", "w") as f:
            json.dump(start_dict, f, indent=4)


# If there are errors when running the simulations (e.g. contpull)
# and the user wants to revert to the previous K_array
def revert():
    # remove current Ks from used_Ks
    f = open("used_Ks.json", "r")
    used_Ks = json.load(f)
    used_Ks = used_Ks['used_Ks']
    f.close()

    f = open("K_array.json", "r")
    K_array = json.load(f)
    K_array = K_array['K_array']
    f.close()

    f = open("status_dict.json", "r")
    status_dict = json.load(f)
    f.close()

    for i in K_array:
        if i in used_Ks:
            used_Ks.remove(i)
        if i in status_dict:
            del status_dict[i]

    used_Ks_dict = {"used_Ks": used_Ks}
    with open("used_Ks.json", "w") as f:
        json.dump(used_Ks_dict, f, indent=4)

    f = open("prev_Ks.json", "r")
    prev_Ks = json.load(f)
    K_array = np.array(prev_Ks['prev_Ks'])
    K_dict = {"K_array": K_array.tolist()}
    with open("K_array.json", "w") as f:
        json.dump(K_dict, f, indent=4)

    with open("status_dict.json", "w") as f:
        json.dump(status_dict, f, indent=4)
        
    print("K_array has been reverted to previous K_array. K_array: ", K_array)
    print("used_Ks has been reverted to previous used_Ks. used_Ks: ", used_Ks)
    print("status_dict has been reverted to previous status_dict. status_dict: ", status_dict)


if __name__ == '__main__':
    args = sys.argv
    globals()[args[1]](*args[2:])