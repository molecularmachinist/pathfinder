#!/usr/bin/env python3

## input srun command into sbatch.sh with file name

sbatch = '/Users/vanil/Documents/HY/pull_script.sh/pathfinder/pull_auto/Python_versions/sbatch.sh'
mdp_file = '/Users/vanil/Documents/HY/pull_script.sh/pathfinder/files/pull_eq.mdp'

def write_batch(file_name):
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

# increase nsteps in mdp file
def wall_time():
    # take 6th line from mdp file
    with open(mdp_file, 'r') as f:
        for i, line in enumerate(f):
            if i == 5:
                line = line.split()
                nsteps = line[2]
                print('Nsteps: ', nsteps)
    nsteps = int(nsteps) * 2
    print('New nsteps: ', nsteps)
    command = 'nsteps    = {} \n'.format(nsteps)
    # delete 5th line in mdp file and add new command
    with open(mdp_file, 'r') as f:
        lines = f.readlines()
    lines[5] = command
    with open(mdp_file, 'w') as f:
        f.writelines(lines)
        

    

#file_name = 'pull_TM1_30'

#write_sbatch(file)

#wall_time()
