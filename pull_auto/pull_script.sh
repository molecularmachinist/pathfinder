#!/bin/bash


#Take K_MIN and K_MAX as variables from user input
#or use some default values for example 5 and 100
#Take total of 5 Ks, equally separated for example 5, 25, 50, 75 and 100 and run in parallel


#Array for domain/molecule names that the user wants to be pulled/pushed
declare -A DOMAIN_NAMES

#Ask the user for the index file, the first gro file (gro file of the first domain/molecule to be pulled) 
#and how many domains/molecules are we working with
read -p "Enter the name of the index file with filename extension (e.g. index.ndx): " INDEX_FILE
read -p "Enter the name of the gro file to start simulations with, with filename extensions: " GRO_FILE
read -p "How many domains?" NUM_OF_DOMAINS

for ((  ))
do
    echo "Enter domains in the order you want them to be pushed/pulled"
    read -p "Enter domain name (uppercase abbreviation, for example TK, JM): " DOMAIN_NAME
    $DOMAIN_NAMES+=$DOMAIN_NAME
    read -p "Push or pull? " DIRECTION
    read -p "What is the target distance? Enter in nm " DISTANCE
done

K_MIN_ORIG=5                            #some starting values for K
K_MAX_ORIG=100
K_MIN=5
K_MAX=100
K_MID=$((($K_MAX - $K_MIN)/2))
K_MID=$(( (($K_MID+2)/5)*5 ))
K2=$((($K_MID - $K_MIN)/2))
K2=$(( (($K2+2)/5)*5 ))
K4=$((($K_MAX - $K_MID)/2))
K4=$(( (($K4+2)/5)*5 ))

K_ARRAY=($K_MIN $K2 $K_MID $K4 $K_MAX) 
declare -A STATUS_ARRAY                           
STATUS_ARRAY[K_MIN]=0
STATUS_ARRAY[K2]=0
STATUS_ARRAY[K_MID]=0
STATUS_ARRAY[K4]=0
STATUS_ARRAY[K_MAX]=0


#Function for setting up the pull sim (TK, JM or TM) and running it
#Takes index and K as input
#$1=iteration
#$2=K
#$3=DOMAIN
run_pull () {
    ITERATION=$1
    K=$2
    DOMAIN=$3
    if [[ $DOMAIN == TK ]]
    then
        sed -i '$d' pull_TK.mdp
        sed -i '$d' pull_TK.mdp
        echo "pull_coord1_k = $K" >> /scratch/project_2006125/vanilja/pull_TK.mdp                                       #set K in mdp
        gmx_mpi distance -f step7.gro -s step7.gro -n index.ndx -oav distance.xvg -select 'com of group "TK1" plus com of group "TK2"'
    elif [[ $DOMAIN == JM ]]
    then
        sed -i '$d' pull_JM.mdp
        sed -i '$d' pull_JM.mdp
        echo "pull_coord1_k = $K" >> /scratch/project_2006125/vanilja/pull_JM.mdp                                       #set K in mdp
        gmx_mpi distance -f pull_eq_TK${ITERATION}.gro -s pull_eq_TK${ITERATION}.gro -n index.ndx -oav distance.xvg -select 'com of group "JM1" plus com of group "JM2"'
    else
        sed -i '$d' pull_TM.mdp     
        sed -i '$d' pull_TM.mdp                                                                                         #remove pull_coord1_k line from mdp file
        echo "pull_coord1_k = $K" >> /scratch/project_2006125/vanilja/pull_TM.mdp                                       #set K in mdp
        gmx_mpi distance -f pull_eq_JM${ITERATION}.gro -s pull_eq_JM${ITERATION}.gro -n index.ndx -oav distance.xvg -select 'com of group "Helix1" plus com of group "Helix2"'
    fi
    GET_LINE=$(sed '25q;d' distance.xvg)                                                                        
    START=${GET_LINE: -5}                                                                                               #get starting distance
    INIT=$(expr "$START + 1.5" | bc -l)                                                                                 #pull 1nm (+0.5 for margin)
    if [[ $DOMAIN == TK ]]
    then
        echo "pull_coord1_init = $INIT" >> /scratch/project_2006125/vanilja/pull_TK.mdp                                 #set init distance in mdp
        gmx_mpi grompp -f pull_TK.mdp -c step7.gro -p topol.top -r step7.gro -n index.ndx -o pull_TK${ITERATION}_$K.tpr -maxwarn 1
        sbatch --output=pull_TK${ITERATION}_$K.txt --job-name=pull_TK${ITERATION}_$K pull_TK.sh
        GRO=pull_TK${ITERATION}_$K
    elif [[ $DOMAIN == JM ]]
    then
        echo "pull_coord1_init = $INIT" >> /scratch/project_2006125/vanilja/pull_JM.mdp                                 #set init distance in mdp
        gmx_mpi grompp -f pull_JM.mdp -c pull_eq_TK.gro -p topol.top -r pull_eq_TK.gro -n index.ndx -o pull_JM${ITERATION}_$K.tpr -maxwarn 1
        sbatch --output=pull_JM${ITERATION}_$K.txt --job-name=pull_JM${ITERATION}_$K pull_JM.sh
        GRO=pull_JM${ITERATION}_$K
    else
        echo "pull_coord1_init = $INIT" >> /scratch/project_2006125/vanilja/pull_TM.mdp                                 #set init distance in mdp
        gmx_mpi grompp -f pull_TM.mdp -c pull_eq_JM.gro -p topol.top -r pull_eq_JM.gro -n index.ndx -o pull_TM${ITERATION}_$K.tpr -maxwarn 1   #grompp
        sbatch --output=pull_TM${ITERATION}_$K.txt --job-name=pull_TM${ITERATION}_$K pull_TM.sh                                                   #run 
        GRO=pull_TM${ITERATION}_$K
    fi                                                                                                                                 
    echo "Pulling $DOMAIN domains (iteration $ITERATION) with K=$K"
}


#Function for determining fail/success for K
#Takes index, domain name (TK, JM or TM) and K as input
#$1 = index for status array
#$2 = domain
#$3 = K
status () {
    GET_LINE=$(sed '18q;d' pull_$2_$3x.xvg)             #get first distance (18th line of xvg file)
    FIRST=${GET_LINE: -7}                           
    LAST=`tail -n 1 pull_$2_$3x.xvg | awk '{print $2}'` #get last distance      awk print $2 means print second column and $2 is not referencing to K (second input parameter)
    DX=$(expr "$LAST - $FIRST" | bc -l)                 #difference in x
    if [[ $(echo "$DX>=0.9" | bc -l) ]]                 #if distance between the domains is >= 0.9
    then
        STATUS_ARRAY[$1]=1                              #1 = successful
        echo "Status for $2 domain K=$3 is successful"
    else
        STATUS_ARRAY[$1]=0                              #0 = unsuccessful
        echo "Status for $2 domain K=$3 is unsuccessful"
    fi
}

#Function for determining new K
#Assumes the STATUS_ARRAY has 3 values
new_K_3 () {
    if [[ STATUS_ARRAY[0] -eq 1 ]]             #if min K was successful
    then
        done
    elif [[ STATUS_ARRAY[1] -eq 1 ]]           #if middle K was successful
    then
        K_MAX=$K_MID                           #previous middle value is now max value
        K_MID=$(( ($K_MID - $K_MIN)/2 ))       #new middle value is between old mid and min
        K_MID=$(( (($K_MID+2)/5)*5 ))          #rounded to the nearest multiple of 5
        STATUS_ARRAY=(0 0 1)
    elif [[ STATUS_ARRAY[2] -eq 1 ]]           #if max K was successful
    then
        K_MIN=$K_MID                           #previous mid value is now min value
        K_MID=$(expr ($K_MAX - $K_MID)/2)      #new middle value is between max and old mid
        K_MID=$(( (($K_MID+2)/5)*5 ))          #roundend to the nearest multiple of 5
        STATUS_ARRAY=(0 0 1)
    fi
    echo "New K is $K_MID"
}

#New function for parallel version for determining a new K after running 5 pulling sims
#Assumes the STATUS_ARRAY has 5 values
new_K_5 () {
    for i in "${K_array[@]}"
    do
        if [[ ${STATUS_ARRAY[$i]} -eq 1 ]]
        then
            K_MAX=$i
            K_MIN=$i-1
            K_MID=$(expr ($K_MAX - $K_MIN)/2)
            K_MID=$(( (($K_MID+2)/5)*5 ))
            STATUS_ARRAY=(0 0 1)
            break
        fi
    done        
}

#Function for checking if the best force constant is found
check_if_done () {
    if [[ STATUS_ARRAY[1] -eq 1 && $(expr $K_MID - $K_MIN) -le 5 ]]         #best force constant is found if K_MID is successful and the difference to K_MIN is < 5
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
#$1 = domain (TK, JM or TM)
run_eq () {
    sed -i '$d' pull_eq_$1.mdp             #delete last two lines of mdp file (pull_coord_init lines)
    sed -i '$d' pull_eq_$1.mdp
    RANGE_HIGH=$(($init + 0.25))
    RANGE_LOW=$(($init - 0.25))
    echo "pull_coord1_init = $RANGE_HIGH" >> /scratch/project_2006125/vanilja/pull_eq_$1.mdp
    echo "pull_coord2_init = $RANGE_LOW" >> /scratch/project_2006125/vanilja/pull_eq_$1.mdp
    gmx_mpi grompp -f pull_eq_$1.mdp -o pull_eq_$1.tpr -c $GRO_FILE -r $GRO_FILE -p topol.top -n index.ndx -maxwarn 1
    sbatch --output=pull_eq_$1.txt --job-name=pull_eq_$1 pull_eq.sh
    echo "Running pull_$1 with range: $RANGE_LOW-$RANGE_HIGH"
                                               

    #check if equilibration was successful
        #check avg force, potential, temp, pressure, volume etc
    #what to do if not successful?
        #run again?
}


#This function runs for selected domain (TK, JM, TM):
    #simulations for finding the best K
    #equilibration
#Inputs: 
    #$1 = domain
    #$2 = number of iterations
run_simulation () {
    for ((i=0; i<=$2; i++))          
    do
        K_MIN=$K_MIN_ORIG                   #set 5 different evenly spaced Ks 
        K_MAX=$K_MAX_ORIG                   
        K_MID=$((($K_MAX - $K_MIN)/2))
        K_MID=$(( (($K_MID+2)/5)*5 ))
        K2=$((($K_MID - $K_MIN)/2))
        K2=$(( (($K2+2)/5)*5 ))
        K4=$((($K_MAX - $K_MID)/2))
        K4=$(( (($K4+2)/5)*5 ))

        run_pull $i $K_MIN $1                #run 5 pulling sims with different Ks
        run_pull $i $K2 $1
        run_pull $i $K_MID $1
        run_pull $i $K2 $1
        run_pull $i $K_MAX $1

        sleep 15h                           #wait for batch jobs to finish (should take about 14h)

        status 0 $1 $K_MIN 
        status 1 $1 $K2      
        status 2 $1 $K_MID                     #check if sims were successful
        status 3 $1 $K4
        status 4 $1 $K_MAX

        new_K_5

        while [[ $FUNC_RESULT==0 ]]         #while K isn't found yet
        do
            run_pull $2 $K_MID
            status 1 $K_MID
            if [[ $res -eq 1 ]]
            then
                local FINAL_TEXT="The optimal force constant has been found"
                echo "$FINAL_TEXT"
                FORCE_CONSTANT=$K_MID
                echo "K=$FORCE_CONSTANT"
                done
            else
                new_K_3                                   #continue searching for best K
            fi
        done

        #Continue with equilibration

        run_eq eq_$1                            #equilibrate domains
}


#This is actually running the simulations

    for ((i=0; i<$NUM_OF_DOMAINS; i++))
    do
        run_simulation $DOMAIN_NAMES[i] $NUM_OF_ITERATIONS
    done


    

done
