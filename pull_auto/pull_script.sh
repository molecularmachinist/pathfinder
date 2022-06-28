#!/bin/bash

#User submits:
#sbatch pull_script.sh 5 50

#Take K_min and K_max as variables from user input
K_min=$1
K_max=$2
K_mid=$((($K_max - $K_min)/2))
K_mid=$(( (($K_mid+2)/5)*5 ))
K_Array=($K_min $K_mid $K_max)
PIDs=()                             
status_arr=(0 0 0)              

#Function for setting up the pull sim and running it
#Takes index and K as input
run_pull () {
    sed -i '$ d' pull.mdp                        #remove pull_coord1_k line from mdp file
    echo "pull_coord1_k = $2" >> cd /scratch/project_2006125/vanilja/pull.mdp                                       #set K in mdp
    gmx_mpi grompp -f pull.mdp -c step7.gro -p topol.top -r step7.gro -n index.ndx -o pull$2.tpr -maxwarn 1         #grompp
    sbatch --output=pull$2.txt --job-name=pull$2 --export=K=$2 pull.sh                                              #run 
    $PIDs[$1]=$!                                                                                                    #save process ID                      
    echo "pull.sh running with K=$2"
}

#Function for determining fail/success for K
#Takes index and K as input
status () {
    wait $PID[$1]                                   #wait for sbatch to finish
    get_line=$(sed '18q;d' pull$2x.xvg)             #get first distance (18th line of xvg file)
    first=${get_line: -7}                           
    last=`tail -n 1 pull$2x.xvg | awk '{print $2}'` #get last distance
    dx=(expr $last - $first)                        #difference in x
    if [[ $dx>1 ]]                                  #if distance between the helices is > 1
    then
        $status_arr[$1]=1                           #1 = successful
    else
        $status_arr[$1]=0                           #0 = unsuccessful
    fi
    echo "Status for $1 is $status_arr[$1]"
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
#call run for new K     --> (while) loop starting point
    #run_pull 1 $K_mid
#determine status
    #status 1 $K_mid
#check if done

run_pull 0 $K_min
run_pull 1 $K_mid
run_pull 2 $K_max

status 0 $K_min      
status 1 $K_mid
status 2 $K_max

func_result=$(check_if_done)

new_K

while [[ $func_result==0 ]]
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