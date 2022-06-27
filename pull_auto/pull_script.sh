#!/bin/bash

#User submits:
#sbatch pull_script.sh 5 50

#Take K_min and K_max as variables from user input
K_min=$1
K_max=$2
K_mid=$(expr ($K_max - $K_min)/2)
K_Array=($K_min $K_mid $K_max)
PIDs=()

for K in $K_Array
do
    echo "pull_coord1_k = $K" >> cd /scratch/project_2006125/vanilja/pull.mdp                                       #set K in mdp
    gmx_mpi grompp -f pull.mdp -c step7.gro -p topol.top -r step7.gro -n index.ndx -o pull${K}.tpr -maxwarn 1   #grompp
    sbatch --output=pull${K}.txt --job-name=pull${K} --export=K=${K} pull.sh                                        #use K in output and jobname                                                  #run pulling
    PIDs+=($!)
done                                                                                                      #save process ID for later

status=()                             #array for K success/fail
for K in K_Array
do
    wait $PID                                   #wait for sbatch to finish
    first=$(sed '18q;d' pull${K}x.xvg)
    last=$(tail -c 6 pull${K}x.xvg)
    dx=(expr $last - $first)                     #difference in x
    if $dx<1
        status+=(1)
    else
        status+=(0)                              #define if pull was succesful or not
done

if (2 == successful)
    $K_mid = $K_min/2
else if (1 == successful)
    if (3 == successful)
        $K_mid = ($K_max - $K_mid)/2
else if (3 == successful)
    $K_mid = ($K_mid - $K_min)/2

if (K_prev != successful AND K_mid == successful AND (K_mid - K_prev)<=5)
    done
else
    repeat for K_mid


#Relaxation/Equilibration