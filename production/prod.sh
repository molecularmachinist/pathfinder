#!/bin/bash 
#SBATCH --output=prod.txt
#SBATCH --time=02:00:00
#SBATCH --job-name=production
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=128
#SBATCH --mem=1G
#SBATCH --account=project_2006125
#SBATCH --partition=medium

module load gromacs

jid1=$(sbatch prod1.sh | awk '{print $4}')
jid2=$(sbatch --dependency=afterok:$jid1 prod2.sh | awk '{print $4}')
jid3=$(sbatch --dependency=afterok:$jid2 prod3.sh | awk '{print $4}')
jid4=$(sbatch --dependency=afterok:$jid3 prod4.sh | awk '{print $4}')
jid5=$(sbatch --dependency=afterok:$jid4 prod5.sh | awk '{print $4}')

jid6=$(sbatch --dependency=afterok:$jid5 prod6.sh | awk '{print $4}')
jid7=$(sbatch --dependency=afterok:$jid6 prod7.sh | awk '{print $4}')
jid8=$(sbatch --dependency=afterok:$jid7 prod8.sh | awk '{print $4}')
jid9=$(sbatch --dependency=afterok:$jid8 prod9.sh | awk '{print $4}')
sbatch --dependency=afterok:$jid9 prod10.sh