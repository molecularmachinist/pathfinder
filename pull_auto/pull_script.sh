#!/bin/bash

#User submits (example):
#sbatch pull_script.sh 5 50

#Take K_min and K_max as variables from user input
#or use some default values for example 5 and 1000
K_min=$1
K_max=$2
K_mid=$((($K_max - $K_min)/2))
K_mid=$(( (($K_mid+2)/5)*5 ))
K_Array=($K_min $K_mid $K_max)
PIDs=()                             
status_arr=(0 0 0)
target_distance=???                           #previous distance + 1nm


#Function for setting up the pull sim (helices) and running it
#Takes index and K as input
#$1=index
#$2=K
run_pull () {
    sed -i '$d' pull.mdp                        #remove pull_coord1_k line from mdp file
    echo "pull_coord1_k = $2" >> cd /scratch/project_2006125/vanilja/pull.mdp                                       #set K in mdp
    echo "pull_coord1_init = ???" >> cd /scratch/project_2006125/vanilja/pull.mdp                                   #set init distance in mdp
    gmx_mpi grompp -f pull.mdp -c step7.gro -p topol.top -r step7.gro -n index.ndx -o pull$2.tpr -maxwarn 1         #grompp
    sbatch --output=pull$2.txt --job-name=pull$2 --export=K=$2 pull.sh                                              #run 
    $PIDs[$1]=$!                                                                                                    #save process ID                      
    echo "pull.sh running with K=$2"
}

#Function for pulling the TK domains
#Takes index and K as input
#$1=index
#$2=K
run_pull_TK () {
    sed -i '$d' pull_TK.mdp
    echo "pull_coord1_k = $2" >> cd /scratch/project_2006125/vanilja/pull_TK.mdp                                       #set K in mdp
    echo "pull_coord1_init = ???" >> cd /scratch/project_2006125/vanilja/pull_TK.mdp
    gmx_mpi grompp -f pull_TK.mdp -c step7.gro -p topol.top -r step7.gro -n index_TK.ndx -o pull_TK.tpr -maxwarn 1
    sbatch --output=pull_TK$2.txt --job-name=pull_TK$2 --export=K=$2 pull_TK.sh
    $PIDs[$1]=$!
    echo "pull_TK.sh running with K=$2"
}

#Function for determining fail/success for K
#Takes index and K as input
status () {
    wait $PID[$1]                                   #wait for sbatch to finish
    get_line=$(sed '18q;d' pull$2x.xvg)             #get first distance (18th line of xvg file)
    first=${get_line: -7}                           
    last=`tail -n 1 pull$2x.xvg | awk '{print $2}'` #get last distance
    dx=(expr $last - $first)                        #difference in x
    if [[ $dx>1 ]]                                  #if distance between the domains is > 1
    then
        $status_arr[$1]=1                           #1 = successful
        echo "Status for $1 is successful"
    else
        $status_arr[$1]=0                           #0 = unsuccessful
        echo "Status for $1 is unsuccessful"
    fi
}

#Function for determining new K
new_K () {
    if [[ $status_arr[0]==1 ]]                  #if min K was successful
    then
        done
    elif [[ $status_arr[1]==1 ]]                #if middle K was successful
    then
        $K_max=$K_mid                           #previous middle value is now max value
        $K_mid=$(expr ($K_mid - $K_min)/2)      #new middle value is between old mid and min
        status_arr=(0 0 1)
    elif [[ $status_arr[2]==1 ]]                #if max K was successful
    then
        $K_min=$K_mid                           #previous mid value is now min value
        $K_mid=$(expr ($K_max - $K_mid)/2)      #new middle value is between max and old mid
        status_arr=(0 0 1)
    fi
    echo "New K is $K_mid"
}

#Function for checking if the best force constant is found
#Returns some string if done and the K
check_if_done () {
    if [[ $status_arr[1]==1 && (expr $K_mid - $K_min)<=5 ]]         #best force constant is found if K_mid is successful and the difference to K_min is < 5
    then
        local func_result=1                                         #1=success
    else
        local func_result=0                                         #0=fail
    fi
}

#Function for running equilibrations
#Equilibrations require 2 coordinates, one flat bottom and one flat bottom high
#Function needs to insert a range (+-0.25nm) into pull coord init parameters
#K is large value 1000 
run_eq () {
    range_high=$(($target_distance + 0.25))
    range_low=$(($target_distance - 0.25))
    echo "pull_coord1_init = $range_high" >> cd /scratch/project_2006125/vanilja/pull_eq.mdp
    echo "pull_coord2_init = $range_low" >> cd /scratch/project_2006125/vanilja/pull_eq.mdp
    gmx_mpi grompp -f pull_eq.mdp -o pull_eq.tpr -c ??? -r ??? -p topol.top -n index.ndx -maxwarn 1
    sbatch pull_eq.sh
    $PIDs[$1]=$!
    echo "Equilibration running with range $range_low-$range_high"

    wait $PID[$1]                                               

    #check if equilibration was successful
        #check avg force, potential, temp, pressure, volume etc
    #what to do if not successful?
        #run again?
}



#For 10nm pulling, we need 9 different Ks (1nm -> 2nm, 2nm -> 3nm, etc.)
#So some kind of a loop here, where first pull sims and finding K, and then equilibration
#after every 1nm of pulling

#(Not sure if this is necessary, because this tool should be universal)
#First we need to pull the TK domains 5Å apart (every atom is 5Å apart) 
#Which is x-direction distance 4.9nm
#Determining  the K is the same for TK domains as TM domains


for ((i=0; i<=8; i++))
do

    run_pull_TK 0 $K_min
    run_pull_TK 1 $K_mid
    run_pull_TK 2 $K_max

    status 0 $K_min      
    status 1 $K_mid
    status 2 $K_max

    func_result=$(check_if_done)

    new_K

    while [[ $func_result==0 ]]         #while K isn't found yet
    do
        run_pull 1 $K_mid
        status 1 $K_mid
        func_result=$(check_if_done)
        if [[ $func_result==1 ]]
        then
            local final_text="The optimal force constant has been found"
            echo "$final_text"
            force_constant=$K_mid
            echo "K=$force_constant"
            done
        else
            new_K                                   #continue searching
        fi
    done

    #The best K for TK pulling is now found
    #Continue with equilibration

    run_eq_TK

    run_pull 0 $K_min
    run_pull 1 $K_mid
    run_pull 2 $K_max

    status 0 $K_min      
    status 1 $K_mid
    status 2 $K_max

    func_result=$(check_if_done)

    new_K

    while [[ $func_result==0 ]]         #while K isn't found yet
    do
        run_pull 1 $K_mid
        status 1 $K_mid
        func_result=$(check_if_done)
        if [[ $func_result==1 ]]
        then
            local final_text="The optimal force constant has been found"
            echo "$final_text"
            force_constant=$K_mid
            echo "K=$force_constant"
            done
        else
            new_K                                   #continue searching
        fi
    done
    
    #The best K for TM pulling is now found
    #Now time to equilibrate and then repeat the steps above

    run_eq

done