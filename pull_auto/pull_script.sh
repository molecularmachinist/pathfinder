#!/bin/bash

#User submits (example):
#sbatch pull_script.sh 5 50

#Take K_min and K_max as variables from user input
#or use some default values for example 5 and 100
#Take total of 5 Ks, equally separated for example 5, 25, 50, 75 and 100 and run in parallel
K_min=$1
K_max=$2
K_mid=$((($K_max - $K_min)/2))
K_mid=$(( (($K_mid+2)/5)*5 ))
K2=$((($K_mid - $K_min)/2))
K2=$(( (($K2+2)/5)*5 ))
K4=$((($K_max - $K_mid)/2))
K4=$(( (($K4+2)/5)*5 ))

K_Array=($K_min $K2 $K_mid $K4 $K_max) 
declare -A status_array                           
status_array[K_min]=0
status_array[K2]=0
status_array[K_mid]=0
status_array[K4]=0
status_array[K_max]=0
pbc_TK1=3402
pbc_TK2=9086


#Function for setting up the pull sim (TM or TK) and running it
#Takes index and K as input
#$1=index
#$2=K
#$3=TM/TK
run_pull () {
    if [[ $3 == TK ]]
    then
        sed -i '$d' pull_TK.mdp
        sed -i '$d' pull_TK.mdp
        echo "pull_coord1_k = $2" >> /scratch/project_2006125/vanilja/pull_TK.mdp                                       #set K in mdp
        gmx_mpi distance -f step7.gro -s step7.gro -n index.ndx -oav distance.xvg -select 'com of group "TK1" plus com of group "TK2"'
    else
        sed -i '$d' pull_TM.mdp     
        sed -i '$d' pull_TM.mdp                                                                                         #remove pull_coord1_k line from mdp file
        echo "pull_coord1_k = $2" >> /scratch/project_2006125/vanilja/pull_TM.mdp                                       #set K in mdp
        gmx_mpi distance -f pull_eq_TK.gro -s pull_eq_TK.gro -n index.ndx -oav distance.xvg -select 'com of group "Helix1" plus com of group "Helix2"'
    fi
    get_line=$(sed '25q;d' distance.xvg)                                                                        
    start=${get_line: -5}                                                                                               #get starting distance
    init=$(expr "$start + 1.5" | bc -l)                                                                                 #pull 1nm (+0.5 for margin)
    if [[ $3 == TK ]]
    then
        echo "pull_coord1_init = $init" >> /scratch/project_2006125/vanilja/pull_TK.mdp
        gmx_mpi grompp -f pull_TK.mdp -c step7.gro -p topol.top -r step7.gro -n index_TK.ndx -o pull_TK.tpr -maxwarn 1
        sbatch --output=pull_TK$2.txt --job-name=pull_TK$2 pull_TK.sh
        gro=pull_TK$2
    else
        echo "pull_coord1_init = $init" >> /scratch/project_2006125/vanilja/pull_TM.mdp                                 #set init distance in mdp
        gmx_mpi grompp -f pull_TM.mdp -c step7.gro -p topol.top -r step7.gro -n index.ndx -o pull_TM$2.tpr -maxwarn 1   #grompp
        sbatch --output=pull_TM$2.txt --job-name=pull_TM$2 pull_TM.sh                                                   #run 
        gro=pull_TM$2
    fi                                                                                                                                 
    echo "Pulling $3 domains with K=$2"
}


#Function for determining fail/success for K
#Takes index and K as input
status () {
    get_line=$(sed '18q;d' pull$2x.xvg)             #get first distance (18th line of xvg file)
    first=${get_line: -7}                           
    last=`tail -n 1 pull$2x.xvg | awk '{print $2}'` #get last distance      awk print $2 means print second column and is not referencing to K (second input parameter)
    dx=$(expr "$last - $first" | bc -l)             #difference in x
    if [[ $(echo "$dx>=0.9" | bc -l) ]]             #if distance between the domains is >= 0.9
    then
        status_array[$1]=1                            #1 = successful
        echo "Status for K=$2 is successful"
    else
        status_array[$1]=0                            #0 = unsuccessful
        echo "Status for K=$2 is unsuccessful"
    fi
}

#Function for determining new K
#Assumes the status_array has 3 values
new_K_3 () {
    if [[ status_array[0] -eq 1 ]]             #if min K was successful
    then
        done
    elif [[ status_array[1] -eq 1 ]]           #if middle K was successful
    then
        K_max=$K_mid                           #previous middle value is now max value
        K_mid=$(( ($K_mid - $K_min)/2 ))       #new middle value is between old mid and min
        K_mid=$(( (($K_mid+2)/5)*5 ))          #rounded to the nearest multiple of 5
        status_array=(0 0 1)
    elif [[ status_array[2] -eq 1 ]]           #if max K was successful
    then
        K_min=$K_mid                           #previous mid value is now min value
        K_mid=$(expr ($K_max - $K_mid)/2)      #new middle value is between max and old mid
        K_mid=$(( (($K_mid+2)/5)*5 ))          #roundend to the nearest multiple of 5
        status_array=(0 0 1)
    fi
    echo "New K is $K_mid"
}

#New function for parallel version
#Assumes the status_array has 5 values
new_K_5 () {
    for i in "${K_array[@]}"
    do
        if [[ ${status_array[$i]} -eq 1 ]]
        then
            K_max=$i
            K_min=$i-1
            K_mid=$(expr ($K_max - $K_min)/2)
            K_mid=$(( (($K_mid+2)/5)*5 ))
            status_array=(0 0 1)
            break
        fi
    done        
}

#Function for checking if the best force constant is found
check_if_done () {
    if [[ status_array[1] -eq 1 && $(expr $K_mid - $K_min) -le 5 ]]         #best force constant is found if K_mid is successful and the difference to K_min is < 5
    then
        res=1                                                             #1=success
    else
        res=0                                                             #0=fail
    fi
}

#Function for running equilibrations
#Equilibrations require 2 coordinates, one flat bottom and one flat bottom high
#Function needs to insert a range (+-0.25nm) into pull coord init parameters
#K is large value 1000 
#$1 = name of mdp file as input to determine whether equilibrating TK or TM domains
run_eq () {
    sed -i '$d' pull_$1.mdp             #delete last two lines of mdp file (pull_coord_init lines)
    sed -i '$d' pull_$1.mdp
    range_high=$(($init + 0.25))
    range_low=$(($init - 0.25))
    echo "pull_coord1_init = $range_high" >> /scratch/project_2006125/vanilja/pull_$1.mdp
    echo "pull_coord2_init = $range_low" >> /scratch/project_2006125/vanilja/pull_$1.mdp
    gmx_mpi grompp -f pull_$1.mdp -o pull_$1.tpr -c $gro.gro -r $gro.gro -p topol.top -n index.ndx -maxwarn 1
    sbatch --output=pull_$1.txt --job-name=pull_$1 pull_eq.sh
    echo "Running pull_$1 with range: $range_low-$range_high"
                                               

    #check if equilibration was successful
        #check avg force, potential, temp, pressure, volume etc
    #what to do if not successful?
        #run again?
}


#(Not sure if this is necessary, because this tool should be universal)
#First we need to pull the TK domains 5Å apart (every atom is 5Å apart) 
#Which is x-direction distance 4.9nm
#Determining  the K is the same for TK domains as TM domains


for ((i=0; i<=8; i++))
do

    run_pull 0 $K_min TK
    run_pull 1 $K2 TK
    run_pull 2 $K_mid TK
    run_pull 3 $K2 TK
    run_pull 4 $K_max TK

    sleep 15h                           #wait for batch jobs to finish (should take about 14h)

    status 0 $K_min
    status 1 $K2      
    status 2 $K_mid
    status 3 $K4
    status 4 $K_max

    new_K_5

    while [[ $func_result==0 ]]         #while K isn't found yet
    do
        run_pull 1 $K_mid
        status 1 $K_mid
        if [[ $res -eq 1 ]]
        then
            local final_text="The optimal force constant has been found"
            echo "$final_text"
            force_constant=$K_mid
            echo "K=$force_constant"
            done
        else
            new_K_3                                   #continue searching for best K
        fi
    done

    #The best K for TK pulling is now found

    #Continue with equilibration

    run_eq eq_TK                            #equilibrate TK domains

    K_min=$1
    K_max=$2
    K_mid=$((($K_max - $K_min)/2))
    K_mid=$(( (($K_mid+2)/5)*5 ))

    run_pull 0 $K_min TM
    run_pull 1 $K_mid TM
    run_pull 2 $K_max TM

    status 0 $K_min      
    status 1 $K_mid
    status 2 $K_max

    new_K

    while [[ $res -eq 0 ]]         #while K isn't found yet
    do
        run_pull 1 $K_mid
        status 1 $K_mid
        if [[ $res -eq 1 ]]
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

    run_eq eq_TM            #equilibrate TM domains

done