#!/usr/bin/env python3


# Imports
import subprocess
import string
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
from itertools import cycle, zip_longest


config = configparser.ConfigParser()
config.read("config.ini")
ndx = config['FILES']['ndx']
topol = config['FILES']['topol']
mdp = config['FILES']['pull_mdp']
eq_mdp = config['FILES']['eq_mdp']
gro = config['FILES']['gro']
maxwarn = config['FILES']['maxwarn']
#num_of_domains = config['DOMAINS']['num_of_domains']
# domains = json.loads(config.get("DOMAINS", "domains"))
# print(domains)
run_multiple = config['COPIES']['run_multiple']
if run_multiple == 'True':
    run_multiple = True
else:
    run_multiple = False
num_of_copies = int(config['COPIES']['num_of_copies'])



## LOGGING
logging.basicConfig(filename='log_pathfinder.log', level=logging.DEBUG)
#logging.info('Starting program')


# Run bash commands
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
    print("\tinit 'iter' 'idx' - initializes the simulation")
    print("\tcontpull 'iter' - continues from the previous pulling simulation")
    print("\tconteq 'iter' - continues from the previous equilibration simulation")
    with open('last_command.json', 'r') as f:
        last_command = json.load(f)
    print("\nThe lates command you ran was: " + last_command['last_command'])



# Error handling for inputs and config file
# Stop script if input is incorrect
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




# Write srun command to batch file
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
    


# Doubles nsteps in mdp file when 
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
def run_pull(iter: int, K: list):
    # create file names
    ncoords = int(config['COORDINATES']['num_of_coords'])
    system = []
    for n in range(1, ncoords+1):
        system.append(config['COORD{}'.format(n)]["name"])
    #domain = " ".join(domain)
    #K_string = "_".join(str(x) for x in K)
    name = ''
    for n in range(ncoords):
        name += str(system[n]) + str(K[n]) + '_'
    file_name = 'pull_' + name + str(iter)
    print(file_name)
    batch = 'sbatch.sh'
    jobname = name + str(iter)
    output = 'pull_' + name + str(iter) + '.out'

    
    #delete the last x lines in mdp file
    x = 2*ncoords
    with open(mdp, 'r') as f:
        lines = f.readlines()
    with open(mdp, 'w') as f:
        for line in lines[:-x]:
            f.write(line)
    
    # for each coordinate, add K and init to mdp file
    for n in range(1, ncoords+1):
        domain_dict = config['COORD{}'.format(n)]
        if domain_dict["direction"] == "pull":
            sign=1.0
        elif domain_dict["direction"] == "push":
            sign=-1.0
        f = open("start{}.json".format(n), "r")
        start_dict = json.load(f)
        start = start_dict['start']
        start = float(start) + float(config['COORD{}'.format(n)]['deltax'])*sign + 0.5
        with open(mdp, 'a') as f:
            f.write("pull_coord{}_k = {}\npull_coord{}_init = {}\n".format(n, K[n-1], n, start))

    f = open("gro_file.json", "r")
    gro_dict = json.load(f)
    gro_file = gro_dict['gro_file']

    # If run_multiple in config is True, run multiple copies of the simulation
    if run_multiple == True:
        print("Running multiple copies of the simulation")
        for copy in range(1, num_of_copies + 1):
            file_name = 'pull_' + name + str(iter) + '_' + str(copy)
            jobname = name + str(iter) + '_' + str(copy)
            output = 'pull_' + name + str(iter) + '_' + str(copy) + '.out'
            bash_command("gmx_mpi grompp -f {} -o {}.tpr -c {} -r {} -p topol.top -n {} -maxwarn {}".format(mdp, file_name, gro_file, gro_file, ndx, maxwarn))
            time.sleep(9)
            write_batch(file_name, batch)
            bash_command("sbatch -J {} -o {} {}".format(jobname, output, batch))
    else:
        bash_command("gmx_mpi grompp -f {} -o {}.tpr -c {} -r {} -p topol.top -n {} -maxwarn {}".format(mdp, file_name, gro_file, gro_file, ndx, maxwarn))
        time.sleep(7)
        write_batch(file_name, batch)
        bash_command("sbatch -J {} -o {} {}".format(jobname, output, batch))
    print("Running {} with K = {}".format(file_name, K))
    time.sleep(10)

    # Make directory for each K
    # Currently only works for 2 coordinates
    pathname1 = str(config['COORD{}'.format(1)]["name"]) + str(K[0])
    if not os.path.exists(pathname1):
        bash_command("mkdir -p iteration{}/{}".format(iter, pathname1))
    pathname2 = str(config['COORD{}'.format(2)]["name"]) + str(K[1])
    path = pathname1 + '/' + pathname2
    if not os.path.exists(path):
        bash_command("mkdir -p iteration{}/{}/{}".format(iter, pathname1, pathname2))




# Determine status (0 or 1) for each K/simulation
# 0 means K wasn't able to pull/push, and 1 means
def status(num: int, iter: int):
    global K_arrays
    ncoords = int(config['COORDINATES']['num_of_coords'])

    global status_dicts

    # Check status of copies
    if run_multiple == True:
        for n in range(0, 5):
            for copy in range(1, num_of_copies + 1):
                system = []
                for m in range(1, ncoords+1):
                    system.append(config['COORD{}'.format(m)]["name"])
                name = ''
                path = 'iteration' + str(iter) + '/'
                K_arrays_zipped = zipKs()
                for coord in range(ncoords):
                    name += str(system[n]) + str(K_arrays_zipped[n][coord]) + '_'
                    path += str(system[coord]) + str(K_arrays_zipped[n][coord]) + '/'
                #file_name = 'pull_' + name + str(iter)
                k = K_arrays_zipped[n][num]
                # K_string = []
                # for m in range(0, ncoords):
                #     K_string.append(str(K_arrays[m][n]))
                # K_string = "_".join(K_string)
                #file_name = 'iteration' + str(iter) + '/K=' + str(k) + '/pull_' + str(system) + str(iter) + '_' + str(K_string) + '_' + str(copy) + 'x.xvg'
                file_name = 'pull_' + name + str(iter) + str(copy) + 'x.xvg'
                file_name = file_name.replace(" ", "")
                file_name = file_name.strip()
                path += file_name
                #print(path)
                # Check if the difference between the first and last distance in xvg file is greater than deltax nm (status=1)
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        for i, line in enumerate(f):
                            if line[0] != '#' and line[0] != '@':
                                line = line.split()
                                first = line[num+1]
                                #print("First: " + str(first))
                                break
                    with open(path, 'r') as f:
                        for i, line in enumerate(f):
                            pass
                        line = line.split()
                        last = line[num+1]
                        #print("Last: " + str(last))
                    deltax = float(config['COORD{}'.format(num+1)]["deltax"]) - 0.1
                    if abs(float(last) - float(first)) >= deltax:
                        print('The pulling of the system coordinate ' + str(config['COORD{}'.format(num+1)]["name"]) + ' with ' + str(k) + '(copy: ' + str(copy) + ') was successful.')
                        logging.info('The pulling of the system coordinate ' + str(config['COORD{}'.format(num+1)]["name"]) + ' with ' + str(k) + '(copy: ' + str(copy) + ') was successful.')
                        status_dicts[num][int(k)]=1
                        bash_command("cd ../..")
                        #return 1
                    else:
                        print('The pulling of the system coordinate ' + str(config['COORD{}'.format(num+1)]["name"]) + ' with ' + str(k) + ' was not successful.')
                        logging.info('The pulling of the system coordinate ' + str(config['COORD{}'.format(num+1)]["name"]) + ' with ' + str(k) + ' was not successful.')
                        if int(k) in status_dicts[num]:
                            if status_dicts[num][int(k)] != 1:
                                status_dicts[num][int(k)]=0 
                        else:
                            status_dicts[num][int(k)]=0
                        bash_command("cd ../..")
                        #return 0
                else:
                    print('The xvg file does not exist')
                    logging.error('The xvg file does not exist')

    # Check status of single copy
    else:
        for n in range(5):
            system = []
            for m in range(1, ncoords+1):
                system.append(config['COORD{}'.format(m)]["name"])
            #print("System: ", system)
            #print("K_arrays: ", K_arrays)
            K_arrays_zipped = zipKs()
            name = ''
            path = 'iteration' + str(iter) + '/'
            for coord in range(ncoords):
                name += str(system[coord]) + str(K_arrays_zipped[n][coord]) + '_'
                path += str(system[coord]) + str(K_arrays_zipped[n][coord]) + '/'
            file_name = 'pull_' + name + str(iter) + 'x.xvg'
            file_name = file_name.replace(" ", "")
            path += file_name
            #print(path)
            k = K_arrays_zipped[n][num]

            # Check if the difference between the first and last distance in xvg file is greater than deltax (status=1)
            if os.path.exists(path):
                with open(path, 'r') as f:
                    for i, line in enumerate(f):
                        # get first line that doesnt start with # or @
                        if line[0] != '#' and line[0] != '@':
                            line = line.split()
                            first = line[num+1]
                            #print("First: " + str(first))
                            break
                with open(path, 'r') as f:
                    for i, line in enumerate(f):
                        pass
                    line = line.split()
                    last = line[num+1]
                    #print("Last: " + str(last))
                deltax = float(config['COORD{}'.format(num+1)]["deltax"]) - 0.1
                if abs(float(last) - float(first)) >= deltax:
                    print('The pulling of the system coordinate ' + str(config['COORD{}'.format(num+1)]["name"]) + ' with ' + str(k) + ' was successful.')
                    logging.info('The pulling of the system coordinate ' + str(config['COORD{}'.format(num+1)]["name"]) + ' with ' + str(k) + ' was successful.')
                    status_dicts[num][int(k)]=1
                    bash_command("cd ../..")
                    #print(status_dicts)
                else:
                    print('The pulling of the system coordinate ' + str(config['COORD{}'.format(num+1)]["name"]) + ' with ' + str(k) + ' was not successful.')
                    logging.info('The pulling of the system coordinate ' + str(config['COORD{}'.format(num+1)]["name"]) + ' with ' + str(k) + ' was not successful.')
                    #print("K:", k)
                    #print("status_dict", status_dicts[num])
                    if int(k) not in status_dicts[num]:
                        status_dicts[num][int(k)]=0
                    bash_command("cd ../..")
                    #print(status_dicts)
            else:
                print('The xvg file does not exist')
                logging.error('The xvg file does not exist')




# Determine new K values for next set of simulations
def new_K(status_array, K_array):
    # Check which K was successful
    # This will determine the new K max and the rest of the Ks
    index=0
    status_array = dict(status_array)
    K_array = list(K_array)
    for key, value in status_array.items():
        if value == 1:
            #index = status_array.index(key)
            break
    K_array = np.array(K_array)

    # if all elements in status_array are 0, double K max
    if all(v == 0 for v in status_array.values()):
        print('None of the Ks were successful. Lets double K max.')
        logging.info('None of the Ks were successful. Lets double K max.')
        K_array[0] = K_array[4] + 5
        K_array[4] = K_array[4] * 2
    else:
        print('K=' + str(key) + ' was successful.')
        # the successful K will now be K max in the K_array
        K_array = np.zeros(5)
        K_array[4] = key
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
        print("K_array contains duplicates, but don't worry, we will only run the simulations once.")
    return K_array



# Check if the best K has been found
def check_if_done():
    global status_dicts
    # go through status_dict and sort
    for sdict in status_dicts:
        status_dict = dict(sdict)
        status_dict = {int(k):v for k,v in status_dict.items()}
        status_dict = {k: v for k, v in sorted(status_dict.items(), key=lambda item: item[0])}
    #print(status_dicts)
    best_Ks = []
    for sdict in status_dicts:
        for key, value in sdict.items():
            # if 5 is the best K
            if value == 1 and (key - 5) <= 0:
                #print('The best force constant has been found. The force constant is ' + str(key) + '.')
                #logging.info('The best force constant has been found. The force constant is ' + str(key) + '.')
                best_Ks.append(key)
                pass
            elif value == 1:
                if key-5 in sdict:
                    if sdict[key-5] == 0:
                        #print('The best force constant has been found. The force constant is ' + str(key) + '.')
                        #logging.info('The best force constant has been found. The force constant is ' + str(key) + '.')
                        best_Ks.append(key)
                        pass
    if len(best_Ks) == len(status_dicts):
        return 1, best_Ks
    else:
        return 0,0





# Run equilibration simulations for a domain
def run_eq(domain: string, iter: int):
    f = open("gro_file.json", "r")
    gro_dict = json.load(f)
    gro_file = gro_dict['gro_file']
    file_name = 'pull_eq_' + str(domain) + str(iter)
    jobname = 'eq_' + str(domain)
    output = 'eq_' + str(domain) + '.out'

    bash_command("cd iteration{}".format(iter))
    bash_command("mkdir -p eq")
    bash_command("cd ..")

    #delete last 2 lines of mdp file
    lines = open(eq_mdp, 'r').readlines()
    del lines[-2:]

    f = open("start.json", "r")
    start = json.load(f)
    current_coord = start['start']
    eq_range = float(config['SYSTEM']['eq_range'])
    range_high = current_coord + eq_range
    range_low = current_coord - eq_range

    #insert new lines into mdp file
    lines.append("pull_coord1_init = " + str(range_high) + "\n")
    lines.append("pull_coord2_init = " + str(range_low))
    open(eq_mdp, 'w').writelines(lines)

    bash_command("gmx_mpi grompp -f {} -o {}.tpr -c {} -r {} -p topol.top -n {} -maxwarn {}".format(eq_mdp, file_name, gro_file, gro_file, ndx, maxwarn))
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

def zipKs():
    ncoords = int(config['COORDINATES']['num_of_coords'])
    # zip_cycle from https://stackoverflow.com/questions/19686533/how-to-zip-two-differently-sized-lists-repeating-the-shorter-list
    def zip_cycle(*iterables, empty_default=None):
        cycles = [cycle(i) for i in iterables]
        for _ in zip_longest(*iterables):
            yield tuple(next(i, empty_default) for i in cycles)
    # make a list of the K arrays
    K_arrays = []
    for n in range(1, 1+ncoords):
        h = open("K_array{}.json".format(n), "r")
        K_dict = json.load(h)
        K_array = K_dict['K_array']
        K_arrays.append(K_array)
    # zip the Ks
    zipped_Ks = zip_cycle(*K_arrays)
    #print(zipped_Ks)
    return list(zipped_Ks)





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




# Start a new iteration
def init(iter: int):
    iter = int(iter)
    read_config()
    # for first iteration
    # create json files to store variables for later use
    ncoords = int(config['COORDINATES']['num_of_coords'])
    for n in range(1, ncoords+1):
        if iter == 0:
            gro_dict = {"gro_file": gro}
            with open("gro_file.json", "w") as f:
                json.dump(gro_dict, f, indent=4)
            start_dict = {"start": config['COORD{}'.format(n)]["start"]}
            with open("start{}.json".format(n), "w") as f:
                json.dump(start_dict, f, indent=4)
            last_command = {"last_command": "init " + str(iter)}
            with open("last_command.json", "w") as f:
                json.dump(last_command, f, indent=4)
        K_array = np.array([5, 0, 0, 0, 0])
        K_array[4] = config['COORD{}'.format(n)]["K_max"]
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
        with open("used_Ks{}.json".format(n), "w") as f:
            json.dump(used_Ks, f, indent=4)
        with open("K_array{}.json".format(n), "w") as f:
            json.dump(K_dict, f, indent=4)
        with open("status_dict{}.json".format(n), "w") as f:
            json.dump(status_dict, f, indent=4)
    run_simulation(iter)
    
    
    

# Run simulations for a domain with an array of K values
def run_simulation(iter: int):
    # if directory doesnt exist, create it
    if not os.path.exists("iteration{}".format(iter)):
        bash_command("mkdir -p iteration{}".format(iter))
    ncoords = int(config['COORDINATES']['num_of_coords'])
    # K_arrays = []
    # for n in range(1, ncoords+1):
    h = open("K_array{}.json".format(n), "r")
    K_dict = json.load(h)
    K_array = K_dict['K_array']
    #     K_arrays.append(K_array)
    #K_arrays = list(zip(*K_arrays))
    #K_arrays_zipped = zipKs()
    #print(K_arrays)
    domain_dict = []
    for n in range(1, ncoords+1):
        domain_dict.append(config['COORD{}'.format(n)]["name"])
    domain_dict = " ".join(domain_dict)
    for j in range(0, len(K_array)):
        run_pull(iter, K_array[j])
    print("Running simulations for system " + domain_dict + " iteration " + str(iter) + " with K= " + str(K_array))
    logging.info("Running simulations for system " + domain_dict + " iteration " + str(iter))
    for n in range(1, ncoords+1):
        h = open("K_array{}.json".format(n), "r")
        K_dict = json.load(h)
        K_array = K_dict['K_array']
        f = open("used_Ks{}.json".format(n), "r")
        used_dict = json.load(f)
        used_Ks = used_dict['used_Ks']
        # convert used_Ks elements to int
        used_Ks = [int(i) for i in used_Ks]
        used_Ks = np.append(used_Ks, K_array)
        # remove duplicates from used_Ks
        used_Ks = np.unique(used_Ks)
        used_dict = {"used_Ks": used_Ks.tolist()}
        with open("used_Ks{}.json".format(n), "w") as f:
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
    domain_dict = config['COORD1']['name']
    #dom = config['COORD1']['name']
    global status_dict
    global K_arrays
    global status_dicts
    last_command = {"last_command": "contpull " + str(iter)}
    ncoords = int(config['COORDINATES']['num_of_coords'])
    with open("last_command.json", "w") as f:
        json.dump(last_command, f, indent=4)

    K_arrays = []
    status_dicts = []
    used_Kss = [] 
    for n in range(1, ncoords+1):
        g = open("status_dict{}.json".format(n), "r")
        st_dict = json.load(g)
        status_dict = dict(st_dict)
        status_dicts.append(status_dict)

        h = open("used_Ks{}.json".format(n), "r")
        used_dict = json.load(h)
        used_Ks = used_dict['used_Ks']
        # convert used_Ks elements to int
        used_Ks = [int(i) for i in used_Ks]
        used_Kss.append(used_Ks)

        h = open("K_array{}.json".format(n), "r")
        K_dict = json.load(h)
        K_array = K_dict['K_array']
        K_arrays.append(K_array)
    system = []
    for n in range(1, ncoords+1):
        system.append(config['COORD{}'.format(n)]["name"])
    for j in range(5):
        if run_multiple == True:
            #pull_TK5_TM5_0.gro
            #path1=TK5 path2=TM5
            for copy in range(1, num_of_copies + 1):
                name = ''
                for coord in range(ncoords):
                    name += str(system[coord]) + str(K_arrays[coord][j]) + '_'
                pathname1 = system[0] + str(K_arrays[0][j])
                pathname2 = system[1] + str(K_arrays[1][j])
                bash_command("if compgen -G pull_{}{}_{}.* > /dev/null; then\nmv pull_{}{}_{}.* iteration{}/{}/{}\nfi".format(name,iter,copy,name,iter,copy,iter,pathname1,pathname2))
                bash_command("[[ -f pull_{}{}_{}x.xvg ]] && mv pull_{}{}_{}x.xvg iteration{}/{}/{}".format(name,iter,copy,name,iter,copy,iter,pathname1,pathname2))
                bash_command("[[ -f pull_{}{}_{}f.xvg ]] && mv pull_{}{}_{}_{}f.xvg iteration{}/{}/{}".format(name,iter,copy,name,iter,copy,iter,pathname1,pathname2))
                bash_command("[[ -f pull_{}{}_{}_prev.cpt ]] && mv pull_{}{}_{}_{}_prev.cpt iteration{}/{}/{}".format(name,iter,copy,name,iter,copy,iter,pathname1,pathname2))
        else:
            K_arrays_zipped = zipKs()
            name = ''
            for coord in range(ncoords):
                name += str(system[coord]) + str(K_arrays_zipped[j][coord]) + '_'
            pathname1 = system[0] + str(K_arrays_zipped[j][0])
            pathname2 = system[1] + str(K_arrays_zipped[j][1])
            bash_command("if compgen -G pull_{}{}.* > /dev/null; then\nmv pull_{}{}.* iteration{}/{}/{}\nfi".format(name,iter,name,iter,iter,pathname1,pathname2))
            bash_command("[[ -f pull_{}{}x.xvg ]] && mv pull_{}{}x.xvg iteration{}/{}/{}".format(name,iter,name,iter,iter,pathname1,pathname2))
            bash_command("[[ -f pull_{}{}f.xvg ]] && mv pull_{}{}f.xvg iteration{}/{}/{}".format(name,iter,name,iter,iter,pathname1,pathname2))
            bash_command("[[ -f pull_{}{}_prev.cpt ]] && mv pull_{}{}_prev.cpt iteration{}/{}/{}".format(name,iter,name,iter,iter,pathname1,pathname2))
    for j in range(0, ncoords):
        status(j, iter)
        time.sleep(3)
    for i in range(len(status_dicts)):
        sdict = {int(k):v for k,v in dict(status_dicts[i]).items()}
        sdict = {k:sdict[k] for k in sorted(sdict)}
        status_dicts[i] = sdict
    print("status_dicts: ", status_dicts)
    #status_dict={"status_dict": status_dict}
    for n in range(1, ncoords+1):
        with open("status_dict{}.json".format(n), "w") as f:
            json.dump(status_dicts[n-1], f, indent=4)

    # Check if the best K has been found
    res, best_Ks = check_if_done()
    if res == 1:
        system = []
        name = ''
        for coord in range(ncoords):
            name += str(system[n]) + str(K_arrays[coord][n]) + '_'
        gro_file = 'pull_' + name + str(iter) + '.gro'
        gro_dict = {"gro_file": gro_file}
        with open("gro_file.json", "w") as f:
            json.dump(gro_dict, f, indent=4)
        #global route
        #route += domain_dict + "/iteration_" + str(iter) + "/K_" + str(best_K)
        pullf = "pull_" + name + str(iter) + "f.xvg"
        pullx = "pull_" + name + str(iter) + "x.xvg"
        pathname1 = str(config['COORD{}'.format(1)]["name"]) + str(best_Ks[0])
        pathname2 = str(config['COORD{}'.format(2)]["name"]) + str(best_Ks[1])
        bash_command("cp iteration{}/{}/{}/{} .".format(iter, pathname1, pathname2, pullf))
        bash_command("cp iteration{}/{}/{}/{} .".format(iter, pathname1, pathname2, pullx))
        pull_plot(pullx, pullf)
        #print("The best force constant has been found.")
        logging.info("The best force constants have been found.")
        bash_command("cp iteration{}/{}/{}/{} .".format(iter, pathname1, pathname2, gro_file))
    else:
        print("The best force constants have not been found yet.")
        for n in range(1, ncoords+1):
            prev_Ks = {"prev_Ks{}".format(n): K_arrays[n-1]}
            with open("prev_Ks{}.json".format(n), "w") as f:
                json.dump(prev_Ks, f, indent=4)

        K_arrays_new = []
        for n in range(ncoords):
            K_array_new = new_K(status_dicts[n], K_arrays[n])
            K_array_unique = np.unique(K_array_new)
            K_filtered = []
            for K_val in K_array_unique:
                #print(used_Kss[n])
                if K_val not in used_Kss[n]:
                    K_filtered.append(K_val)
            K_filtered = np.array(K_filtered)
            print("K_filtered: {}".format(K_filtered))
            K_arrays_new.append(K_filtered)
        print("K_arrays_new: {}".format(K_arrays_new))


        def ask_cont():
            answer = input("Do you wish to run simulations with these new force constants? (y/n)")
            if answer == "y":
                print("You answered yes. Continuing to simulations...")
                logging.info('User chose to continue to simulations.')
                for n in range(1, ncoords+1):
                    with open("status_dict{}.json".format(n), "w") as f:
                        json.dump(status_dicts[n-1], f, indent=4)
                    K_dict = {"K_array": K_arrays_new[n-1].tolist()}
                    with open("K_array{}.json".format(n), "w") as f:
                        json.dump(K_dict, f, indent=4)
                run_simulation(iter)
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
            f = open("start.json", "r")
            start = json.load(f)
            current_coord = start['start'] + float(config['SYSTEM']['deltax'])
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
def conteq(iter: int):
    dom = config['SYSTEM']['name']
    last_command = {"last_command": "conteq " + str(iter)}
    with open("last_command.json", "w") as f:
        json.dump(last_command, f, indent=4)

    # check if the equilibration is done
    file_name = 'pull_eq_' + str(dom) + str(iter)
    command="gmx_mpi rms -s {}.tpr -f {}.xtc -o {}_rmsd.xvg -tu ns".format(file_name, file_name, file_name)
    subprocess.run([command], input="4 4", text=True, shell=True, executable='/bin/bash')

    rmsd_xvg_file = file_name + '_rmsd.xvg'
    # from analyze.py use function analyze
    result=analyze(rmsd_xvg_file, dom)
    print("Result: ", result)
    if result == 0:
        answer = input("Equilibration was not successful. Do you want to run it again with longer time? (y/n)")
        if answer == "y":
            print("Running equilibration again with longer time")
            logging.info("Running equilibration again with longer time")
            longer_time(eq_mdp)
            run_eq(dom, iter)
        elif answer == "n":
            print("You answered no. Exiting...")
            logging.info('User chose not to continue. Exiting program.')
            sys.exit()
    else:
        print("Equilibration was successful")
        logging.info("Equilibration was successful")
        bash_command("if compgen -G pull_eq_{}{}* > /dev/null; then\nmv pull_eq_{}{}* eq\nfi".format(dom,iter,dom,iter))
        gro_file = 'pull_eq_' + dom + str(iter) + '.gro'
        gro_dict = {"gro_file": gro_file}
        with open("gro_file.json", "w") as f:
            json.dump(gro_dict, f, indent=4)


def revert():
    f = open("prev_Ks.json", "r")
    prev_Ks = json.load(f)
    K_array = np.array(prev_Ks['prev_Ks'])
    K_dict = {"K_array": K_array.tolist()}
    with open("K_array.json", "w") as f:
        json.dump(K_dict, f, indent=4)
    print("K_array has been reverted to previous K_array")



def multiple_coords():
    print("Running multiple_coords")
    ncoords = int(config['COORDINATES']['num_of_coords'])
    for n in range(1, ncoords + 1):
        status_dict = {"status_dict": {}}
        new_K
    


if __name__ == '__main__':
    args = sys.argv
    globals()[args[1]](*args[2:])