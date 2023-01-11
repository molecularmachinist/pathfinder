#!/bin/bash
#SBATCH --nodes=4
#SBATCH --ntasks-per-node=128
#SBATCH --cpus-per-task=1
#SBATCH --time=36:00:00
#SBATCH --partition=medium
#SBATCH --account=project_2006125                  
##SBATCH --mail-type=END
##SBATCH --mail-user=<erkki.esimerkki@domain.com>     


srun gmx_mpi mdrun -deffnm pull_TM1_30 -pf pull_TM1_30f.xvg -px pull_TM1_30x.xvg