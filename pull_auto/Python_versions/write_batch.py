#!/usr/bin/env python3

## input srun command into sbatch.sh with file name

sbatch = 'sbatch.sh'

def write_sbatch(file_name):
    # remove last line from sbatch.sh
    command = 'srun gmx_mpi mdrun -v -deffnm {} -pf {}f.xvg -px {}x.xvg'.format(file_name, file_name, file_name)
    with open(sbatch, "w") as f:
        f.write(command)
        f.close()
    
def wall_time():
    # double wall time (7th line in sbatch.sh)
    lines = open(sbatch, 'r').readlines()
    lines[6] = "#SBATCH --time=24:00:00"
    open(sbatch, 'w').writelines(lines)
    

file = 'TM'

write_sbatch(file)