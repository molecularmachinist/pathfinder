#!/bin/bash
#SBATCH --output=eq_end.txt
#SBATCH --account=project_2006125
#SBATCH --time=02:00:00
#SBATCH --mem=1G
#SBATCH --job-name=eq
#SBATCH --partition=medium

#jid1=$(sbatch eq1.sh | awk '{print $4}')
#jid2=$(sbatch --dependency=afterok:$jid1 eq2.sh | awk '{print $4}')
#jid3=$(sbatch --dependency=afterok:$jid2 eq3.sh | awk '{print $4}')
jid4=$(sbatch eq4.sh | awk '{print $4}')
jid5=$(sbatch --dependency=afterok:$jid4 eq5.sh | awk '{print $4}')
sbatch --dependency=afterok:$jid5 eq6.sh
