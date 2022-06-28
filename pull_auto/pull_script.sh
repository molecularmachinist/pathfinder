#!/bin/bash

#User submits:
#sbatch pull_script.sh 5 50

#Take K_min and K_max as variables from user input
K_min=$1
K_max=$2
K_mid=$(expr ($K_max - $K_min)/2)
K_Array=($K_min $K_mid $K_max)
PIDs=()
status_arr=(0 0 0)                                                                                                   #save process ID for later

#Function for setting up the pull sim and running it
#Takes index and K as input
run_pull () {
    echo "pull_coord1_k = $2" >> cd /scratch/project_2006125/vanilja/pull.mdp                                       #set K in mdp
    gmx_mpi grompp -f pull.mdp -c step7.gro -p topol.top -r step7.gro -n index.ndx -o pull$2.tpr -maxwarn 1   #grompp
    sbatch --output=pull$2.txt --job-name=pull$2 --export=K=$2 pull.sh
    $PIDs[$1]=$!
}

#Function for determining fail/success for K
#Takes index and K as input
status () {
    wait $PID[$1]                                   #wait for sbatch to finish
    first=$(sed '18q;d' pull$2x.xvg)          #get 
    last=$(tail -c 6 pull$2x.xvg)
    dx=(expr $last - $first)                     #difference in x
    if [[ $dx>1 ]]                             #if distance between the helices is > 1
    then
        $status_arr[$1]=1                             #1 = successful
    else
        $status_arr[$1]=0                             #0 = unsuccessful
    fi
}

#Function for determining new K (if needed)
new_K () {
    if [[ $status_arr[0]==1 ]]                      #if min K was successful
    then
        done
    elif [[ $status_arr[1]==1 ]]                    #if middle K was successful
    then
        $K_max=$K_mid                           #previous middle value is now max value
        $K_mid=$(expr ($K_mid - $K_min)/2)      #new middle value is between old mid and min
        status_arr=(0 0 1)
    elif [[ $status_arr[2]==1 ]]                    #if max K was successful
    then
        $K_min=$K_mid                           #previous mid value is now min value
        $K_mid=$(expr ($K_max - $K_mid)/2)      #new middle value is between max and old mid
        status_arr=(0 0 1)
    fi
}

#Function for checking if the best force constant is found
#Returns some string if done and the K
check_if_done () {
    if [[ $status_arr[1]==1 && (expr $K_mid - $K_min)<=5 ]]
    then
        local func_result="The optimal force constant has been found"
        echo "$func_result"
        force_constant=$K_mid
        echo "K=$force_constant"
        done
    else
        repeat for K_mid
    fi
}

#call run for 3 K values:
    #run_pull 0 $K_min
    #run_pull 1 $K_mid
    #run_pull 2 $K_max
#determine statuses for each
    #status 0 $K_min      (0 is index for K_min)
    #status 1 $K_mid
    #status 2 $K_max
#new K based on statuses
    #new_K
#call run for new K
    #run_pull 1 $K_mid
#determine status
    #status 1 $K_mid
#check if done

if [[]]