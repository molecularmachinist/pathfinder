#!/bin/bash

module load gromacs

#Take K_MIN and K_MAX as variables from user input
#or use some default values for example 5 and 100
#Take total of 5 Ks, equally separated for example 5, 25, 50, 75 and 100 and run in parallel


#Array for domain/molecule names that the user wants to be pulled/pushed
declare -A DOMAIN_NAMES
#Array for starting distances
declare -A STARTS
#Array for number of iterations each total pull will need
declare -A ITERATIONS

#Ask the user for the index file, the first gro file (gro file of the first domain/molecule to be pulled) 
#and how many domains/molecules are we working with
read -p "Enter the name of the index file with filename extension (e.g. index.ndx): " INDEX_FILE
read -p "Enter the name of the gro file to start simulations with, with filename extensions: " GRO_FILE
read -p "How many domains?" NUM_OF_DOMAINS

for ((i=1; i<=$NUM_OF_DOMAINS; i++))
do
    echo "Enter domains in the order you want them to be pushed/pulled"
    read -p "Enter domain name (uppercase abbreviation (the same as in the index groups), for example TK, JM): " DOMAIN_NAME
    DOMAIN_NAMES+=$DOMAIN_NAME
    read -p "Push or pull? " DIRECTION
    read -p "What is the target distance? Enter in nm: " TARGET
    gmx_mpi distance -f $GRO_FILE -s $GRO_FILE -n $INDEX_FILE -oav distance.xvg -select "com of group ${DOMAIN_NAME}1 plus com of group ${DOMAIN_NAME}2"
    GET_LINE=$(sed '25q;d' distance.xvg)                                                                        
    STARTS+=( ["${DOMAIN_NAME}"]=${GET_LINE: -5} )
    ITERATIONS+=( ["${DOMAIN_NAME}"]=$(expr "$TARGET-${STARTS[${DOMAIN_NAME}]}" | bc -l) )
done

K_MIN_ORIG=5                            #some starting values for K
K_MAX_ORIG=100
K_MIN=5
K_MAX=100
K_MID=$(( $K_MIN + ($K_MAX - $K_MIN)/2 ))
K_MID=$(( (($K_MID+2)/5)*5 ))
K2=$((($K_MID - $K_MIN)/2))
K2=$(( (($K2+2)/5)*5 ))
K4=$((($K_MAX - $K_MID)/2))
K4=$(( (($K4+2)/5)*5 ))
K4=$(( $K4+$K_MID ))

K_ARRAY=($K_MIN $K2 $K_MID $K4 $K_MAX) 
declare -A STATUS_ARRAY                           
STATUS_ARRAY[0]=0
STATUS_ARRAY[1]=0
STATUS_ARRAY[2]=0
STATUS_ARRAY[3]=0
STATUS_ARRAY[4]=0


#Function for setting up the pull sim (TK, JM or TM) and running it
#Takes index and K as input
#$1=iteration
#$2=K
#$3=DOMAIN
run_pull () {
    local ITERATION=$1
    local K=$2
    local DOMAIN=$3

    sed -i '$d' pull_$DOMAIN.mdp                                                        #delete last two lines of mdp file (pull_coord_init and K lines)
    sed -i '$d' pull_$DOMAIN.mdp
    echo "pull_coord1_k = $K" >> pull_$DOMAIN.mdp                                       #set K in mdp                                                                                               #get starting distance
    INIT=$(expr "${STARTS[${DOMAIN}]} + 1.5" | bc -l)                                   #pull 1nm (+0.5 for margin)
    echo "pull_coord1_init = $INIT" >> pull_$DOMAIN.mdp                                 #set init distance in mdp
    gmx_mpi grompp -f pull_$DOMAIN.mdp -c $GRO_FILE -p topol.top -r $GRO_FILE -n $INDEX_FILE -o pull_${DOMAIN}${ITERATION}_$K.tpr -maxwarn 1
    sbatch --output=pull_${DOMAIN}${ITERATION}_$K.txt --job-name=pull_${DOMAIN}${ITERATION}_$K pull_$DOMAIN.sh
    GRO_FILE=pull_${DOMAIN}${ITERATION}_$K                                                                                                                               
    echo "Pulling $DOMAIN domains (iteration $ITERATION) with K=$K"
}


#Function for determining fail/success for K
#Takes index, domain name (TK, JM or TM) and K as input
#$1 = index for status array
#$2 = domain
#$3 = K
status () {
    local INDEX=$1
    local DOMAIN=$2
    local K=$3
    local ITERATION=$4

    GET_LINE=$(sed '18q;d' pull_${DOMAIN}${ITERATION}_${K}x.xvg)             #get first distance (18th line of xvg file)
    FIRST=${GET_LINE: -7}                           
    LAST=`tail -n 1 pull_${DOMAIN}${ITERATION}_${K}x.xvg | awk '{print $2}'` #get last distance      awk print $2 means print second column and $2 is not referencing to K (second input parameter)
    DX=$(expr "$LAST - $FIRST" | bc -l)                 #difference in x
    if [[ $(echo "$DX>=0.9" | bc -l) -eq "1" ]]                 #if distance between the domains is >= 0.9
    then
        STATUS_ARRAY[$INDEX]=1                              #1 = successful
        echo "Status for $DOMAIN domain iteration $ITERATION K=$K is successful"
    else
        STATUS_ARRAY[$INDEX]=0                              #0 = unsuccessful
        echo "Status for $DOMAIN domain iteration $ITERATION K=$K is unsuccessful"
    fi
}

#Function for determining new K
#Assumes the STATUS_ARRAY has 3 values
new_K_3 () {
    if [[ STATUS_ARRAY[0] -eq 1 ]]             #if min K was successful
    then
        echo "K_MIN=${K_ARRAY[0]} was successful"
        break
    elif [[ STATUS_ARRAY[1] -eq 1 ]]           #if middle K was successful
    then
        echo "K_MID=${K_ARRAY[1]} was successful"
        K_MAX=$K_MID                           #previous middle value is now max value
        K_MID=$(( $K_MIN + ($K_MAX - $K_MIN)/2 ))       #new middle value is between old mid and min
        K_MID=$(( (($K_MID+2)/5)*5 ))          #rounded to the nearest multiple of 5
        K_ARRAY=($K_MIN $K_MID $K_MAX)
        declare -A STATUS_ARRAY
        STATUS_ARRAY[0]=0
        STATUS_ARRAY[1]=0
        STATUS_ARRAY[2]=1
    elif [[ STATUS_ARRAY[2] -eq 1 ]]           #if max K was successful
    then
        echo "K_MAX=${K_ARRAY[2]} was successful"
        K_MIN=$K_MID                           #previous mid value is now min value
        K_MID=$(( $K_MIN + ($K_MAX - $K_MIN)/2 ))      #new middle value is between max and old mid
        K_MID=$(( (($K_MID+2)/5)*5 ))          #roundend to the nearest multiple of 5
        K_ARRAY=($K_MIN $K_MID $K_MAX)
        declare -A STATUS_ARRAY
        STATUS_ARRAY[0]=0
        STATUS_ARRAY[1]=0
        STATUS_ARRAY[2]=1
    fi
    echo "New K_MID is $K_MID"
    echo "New values of K are: ${K_ARRAY[*]}"
}

#New function for parallel version for determining a new K after running 5 pulling sims
#Assumes the STATUS_ARRAY has 5 values
new_K_5 () {                                               
    for i in {0..4}
    do
        echo "Checking K=${K_ARRAY[$i]}"
        if [[ ${STATUS_ARRAY[$i]} -eq 1 ]]
        then
            echo "K=${K_ARRAY[$i]} was successful"
            K_MAX=${K_ARRAY[$i]}
            local prev=$(( $i - 1 ))
            K_MIN=${K_ARRAY[$prev]}
            K_MID=$(( $K_MIN + ($K_MAX - $K_MIN)/2 ))
            K_MID=$(( (($K_MID+2)/5)*5 ))
            declare -A STATUS_ARRAY
            STATUS_ARRAY[0]=0
            STATUS_ARRAY[1]=0
            STATUS_ARRAY[2]=1
            K_ARRAY=($K_MIN $K_MID $K_MAX)
            echo "New values of K are: ${K_ARRAY[*]}"
            break
        else
            echo "K=${K_ARRAY[$i]} was not successful"
        fi
    done        
}

#Function for checking if the best force constant is found
check_if_done () {
    if [[ ${#STATUS_ARRAY[@]} -eq 3 ]]
    then
        if [[ STATUS_ARRAY[1] -eq 1 && $(expr $K_MID - $K_MIN) -le 5 ]]         #best force constant is found if K_MID is successful and the difference to K_MIN is < 5
        then
            RES=1                                                             #1=success
        else
            RES=0                                                             #0=fail
        fi
    elif [[ ${#STATUS_ARRAY[@]} -eq 5 ]]
        if [[ STATUS_ARRAY[1] -eq 1 && $(expr $K2 - $K_MIN) -le 5 ]]          #best force constant is found if K_MID is successful and the difference to K_MIN is < 5
        then
            RES=1                                                             #1=success
            BEST_K=$K2
        elif [[ STATUS_ARRAY[2] -eq 1 && $(expr $K_MID - $K2) -le 5 ]]
            RES=1
            BEST_K=$K_MID
        elif [[ STATUS_ARRAY[3] -eq 1 && $(expr $K4 - $K_MID) -le 5 ]]
            RES=1
            BEST_K=$K4
        else
            RES=0                                                             #0=fail
        fi
    fi
}

#Function for running equilibrations
#Equilibrations require 2 coordinates, one flat bottom and one flat bottom high
#Function needs to insert a range (+-0.25nm) into pull coord init parameters
#K is large value 1000 
#$1 = domain (TK, JM or TM)
#$2 = index/iteration
run_eq () {
    local DOMAIN=$1
    local ITERATION=$2

    sed -i '$d' pull_eq.mdp             #delete last two lines of mdp file (pull_coord_init lines)
    sed -i '$d' pull_eq.mdp
    RANGE_HIGH=$(($INIT + 0.25))
    RANGE_LOW=$(($INIT - 0.25))
    echo "pull_coord1_init = $RANGE_HIGH" >> pull_eq.mdp
    echo "pull_coord2_init = $RANGE_LOW" >> pull_eq.mdp
    gmx_mpi grompp -f pull_eq.mdp -o pull_eq_${DOMAIN}${ITERATION}.tpr -c $GRO_FILE -r $GRO_FILE -p topol.top -n $INDEX_FILE -maxwarn 1
    sbatch --output=pull_eq_${DOMAIN}${ITERATION}.txt --job-name=pull_eq_${DOMAIN}${ITERATION} pull_eq.sh
    echo "Running pull_${DOMAIN}${ITERATION} with range: $RANGE_LOW-$RANGE_HIGH"
                                               

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
    local DOMAIN=$1
    local NUM_OF_ITERATIONS=$2

    for ((i=1; i<=$NUM_OF_ITERATIONS; i++))          
    do
        K_MIN=$K_MIN_ORIG                   #set 5 different evenly spaced Ks 
        K_MAX=$K_MAX_ORIG                   
        K_MID=$(( $K_MIN + ($K_MAX - $K_MIN)/2 ))
        K_MID=$(( (($K_MID+2)/5)*5 ))
        K2=$((($K_MID - $K_MIN)/2))
        K2=$(( (($K2+2)/5)*5 ))
        K4=$((($K_MAX - $K_MID)/2))
        K4=$(( (($K4+2)/5)*5 ))

        for ((j=0; j<=4; j++))                  #run pulling sims for 5 different Ks
        do
            run_pull $i $K_ARRAY[$j] $DOMAIN
        done

        sleep 15h                           #wait for batch jobs to finish (should take about 14h)

        for ((j=0; j<=4; j++))                  
        do
            status $j $DOMAIN $K_ARRAY[$j] $i
        done

        check_if_done
        if [[ $RES -eq 1 ]]
        then
            local FINAL_TEXT="The optimal force constant has been found"
            echo "$FINAL_TEXT"
            echo "K=$BEST_K"
        else
            new_K_5                                   #continue searching for best K
        fi

        while [[ $FUNC_RESULT -eq 0 ]]         #while K isn't found yet
        do
            run_pull $i $K_MID $DOMAIN
            status 1 $K_MID
            check_if_done
            if [[ $RES -eq "1" ]]
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

        run_eq $DOMAIN $i                           #equilibrate domains

        sleep 15h

        GRO_FILE=pull_eq_${DOMAIN}$i
}


#This is actually running the simulations

    for ((i=0; i<$NUM_OF_DOMAINS; i++))
    do
        run_simulation $DOMAIN_NAMES[i] $NUM_OF_ITERATIONS
    done


    

done