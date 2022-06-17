#!/bin/bash 
#SBATCH --output=prod.txt
#SBATCH --time=00:30:00
#SBATCH --job-name=production
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=128
#SBATCH --mem=24G
#SBATCH --account=project_2006125
#SBATCH --partition=medium

module load gromacs
