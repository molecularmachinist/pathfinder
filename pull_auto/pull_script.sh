#!/bin/bash
LOG_LOCATION=/scratch/project_2006125/vanilja/pathfinder/testing
exec > >(tee -a $LOG_LOCATION/output.txt)
exec 2>&1

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
#Array for keeping track of the successful route of simulations
declare -A ROUTE

read_config () {
    . input.config

    #ERROR HANDLING
    #STOP SCRIPT RUN IF INPUT IS INCORRECT

    echo "Index file=${INDEX_FILE}"

    echo "Starting gro/pdb file=${GRO_FILE}"


    if [[ $INDEX_FILE == *.ndx ]]
    then
        echo "Index file is in correct format"
    else
        echo "ERROR: File was not NDX file. Fix input."
        exit 1
    fi

    echo "Number of domains=${NUM_OF_DOMAINS}"

    if [[ $NUM_OF_DOMAINS -le 0 ]]
    then
        echo "ERROR: NUMBER OF DOMAINS was 0 or less. Fix input."
        exit 1
    fi

    if [[ ${#DOMAIN_NAMES[@]} -ne $NUM_OF_DOMAINS ]]
        then
            echo "ERROR: The number of DOMAIN NAMES does not match the number of domains."
            exit 1
        fi

    i=0
    for d in "${DOMAIN_NAMES[@]}"
    do
        echo "Info for ${d} domain: "

        if [[ ${#DIRECTIONS[@]} -ne $NUM_OF_DOMAINS ]]
        then
            echo "ERROR: The number of DIRECTIONS does not match the number of domains."
            exit 1
        fi

        DIRECTIONS[$d]=${DIRECTIONS[$i]}
        case "${DIRECTIONS[$d]}" in
        [Pp][Uu][Ll][lL])
            ;;
        [pP][Uu][sS][hH])
            ;;
        *)
            echo "ERROR: DIRECTION input wasn't 'push' or 'pull'."
            exit 1
        esac
        echo "Direction: ${DIRECTIONS[$d]}"

        STARTS[$d]=${STARTS[$i]}
        if [[ ${#STARTS[@]} -ne $NUM_OF_DOMAINS ]]
        then
            echo "ERROR: The number of STARTING DISTANCES does not match the number of domains."
            exit 1
        fi

        TARGETS[$d]=${TARGETS[$i]}
        if [[ ${#TARGETS[@]} -ne $NUM_OF_DOMAINS ]]
        then
            echo "ERROR: The number of TARGET DISTANCES does not match the number of domains."
            exit 1
        fi

        K_MAX[$d]=${K_MAX[$i]}
        if [[ ${#K_MAX[@]} -ne $NUM_OF_DOMAINS ]]
        then
            echo "ERROR: The number of MAXIMUM FORCE CONSTANTS K does not match the number of domains."
            exit 1
        fi

        ITERATIONS+=( ["$d"]=$(expr "${TARGETS[$d]}-${STARTS[$d]}" | bc -l) )

        i+=1
    done

    echo "Check that the inputs are correct."
    sleep 30s
}

read_config


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


#Function for writing a batch script (CSC Mahti)
#Takes file name as input
write_batch () {
    local FILE=$1                

    touch ${FILE}.sh                                
    echo '#!/bin/bash' >> $FILE.sh
    echo "#SBATCH --output=$FILE.txt" >> $FILE.sh
    echo "#SBATCH --time=${TIME}" >> $FILE.sh
    echo "#SBATCH --job-name=$FILE" >> $FILE.sh
    echo "#SBATCH --nodes=${NODES}" >> $FILE.sh
    echo "#SBATCH --ntasks-per-node=${NTASKS-PER-NODE}" >> $FILE.sh
    echo "#SBATCH --mem=${MEMORY}" >> $FILE.sh
    echo "#SBATCH --account=${ACCOUNT}" >> $FILE.sh
    echo "#SBATCH --partition=${PARTITION}" >> $FILE.sh

    echo "srun gmx_mpi mdrun -v -deffnm $FILE -pf ${FILE}f.xvg -px ${FILE}x.xvg" >> $FILE.sh
    
}


#Function for setting up the pull sim (TK, JM or TM) and running it
#Takes iteration, domain and K as input
#$1=iteration
#$2=K
#$3=DOMAIN
run_pull () {
    local ITERATION=$1
    local K=$2
    local DOMAIN=$3
    local FILE=pull_${DOMAIN}${ITERATION}_$K

    sed -i '$d' pull_$DOMAIN.mdp                                                        #delete last two lines of mdp file (pull_coord_init and K lines)
    sed -i '$d' pull_$DOMAIN.mdp
    echo "pull_coord1_k = ${SIGN}$K" >> pull_$DOMAIN.mdp                                #set K in mdp                                                                                               #get starting distance
    INIT=$(expr "${STARTS[${DOMAIN}]} $SIGN 1.5" | bc -l)                               #pull/push 1nm (+0.5 for margin)
    echo "pull_coord1_init = $INIT" >> pull_$DOMAIN.mdp                                 #set init distance in mdp
    gmx_mpi grompp -f pull_$DOMAIN.mdp -c $GRO_FILE -p topol.top -r $GRO_FILE -n $INDEX_FILE -o pull_${DOMAIN}${ITERATION}_$K.tpr -maxwarn 1

    write_batch $FILE
    sbatch $FILE.sh                                                                                                                              
}


#Function for determining fail/success for K
#Takes index, domain name (TK, JM or TM) and K as input
#$1 = index for status array
#$2 = domain
#$3 = K
#$4 = iteration
status () {
    local INDEX=$1
    local DOMAIN=$2
    local K=$3
    local ITERATION=$4

    GET_LINE=$(sed '18q;d' pull_${DOMAIN}${ITERATION}_${K}x.xvg)             #get first distance (18th line of xvg file)
    FIRST=${GET_LINE: -7}                           
    LAST=`tail -n 1 pull_${DOMAIN}${ITERATION}_${K}x.xvg | awk '{print $2}'` #get last distance      awk print $2 means print second column and $2 is not referencing to K (second input parameter)
    DX=$(expr "$LAST - $FIRST" | bc -l)                                      #difference in x
    if [[ $(echo "${DX#-}>=0.9" | bc -l) -eq "1" ]]                          #if difference in starting and ending distance is >= 0.9
    then
        STATUS_ARRAY[$INDEX]=1                                              #1 = successful
        echo "Status for $DOMAIN domain iteration $ITERATION K=$K is successful"
    else
        STATUS_ARRAY[$INDEX]=0                                              #0 = unsuccessful
        echo "Status for $DOMAIN domain iteration $ITERATION K=$K is unsuccessful"
    fi
}

#Function for determining an array of new K values
new_K () {
    if [[ ${#STATUS_ARRAY[@]} -eq 3 ]]
    then
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
    elif [[ ${#STATUS_ARRAY[@]} -eq 5 ]]
    then
        if [[ ${STATUS_ARRAY[4]} -eq 0 ]]       #If K_MAX was unsuccessful i.e. none of the K's worked
        then
            echo "The largest K was unsuccessful. Let's double Kmax."
            K_MAX=$((2*$K_MAX))
            K_MID=$(( $K_MIN + ($K_MAX - $K_MIN)/2 ))
            K_MID=$(( (($K_MID+2)/5)*5 ))
            K2=$((($K_MID - $K_MIN)/2))
            K2=$(( (($K2+2)/5)*5 ))
            K4=$((($K_MAX - $K_MID)/2))
            K4=$(( (($K4+2)/5)*5 ))
            K4=$(( $K4+$K_MID ))
            STATUS_ARRAY[0]=0
            STATUS_ARRAY[1]=0
            STATUS_ARRAY[2]=0
            STATUS_ARRAY[3]=0
            STATUS_ARRAY[4]=0
            echo "New values of K are: ${K_ARRAY[*]}"
            break
        fi                                       
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
    else
        echo "Error in new_K. K_ARRAY length was 3 nor 5."
        exit 1
    fi
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
    local FILE=pull_eq_${DOMAIN}${ITERATION}

    sed -i '$d' pull_eq.mdp             #delete last two lines of mdp file (pull_coord_init lines)
    sed -i '$d' pull_eq.mdp
    RANGE_HIGH=$(($INIT + 0.25))
    RANGE_LOW=$(($INIT - 0.25))
    echo "pull_coord1_init = $RANGE_HIGH" >> pull_eq.mdp
    echo "pull_coord2_init = $RANGE_LOW" >> pull_eq.mdp
    gmx_mpi grompp -f pull_eq.mdp -o ${FILE}.tpr -c $GRO_FILE -r $GRO_FILE -p topol.top -n $INDEX_FILE -maxwarn 1

    write_batch $FILE
    sbatch ${FILE}.sh

    echo "Running ${FILE} with range: $RANGE_LOW-$RANGE_HIGH"
                                               
    #some waiting will need to happen here
    #or new function for analyzing

    gmx_mpi rms -s ${FILE}.tpr -f ${FILE}.trr -o ${FILE}_rmsd.xvg -tu ns
    echo "backbone backbone"

    RESULT=$(/usr/bin/env python3 analyze.py ${FILE}_rmsd.xvg $DOMAIN)      #0 means fail, the slope wasnt close enough to 0
    echo "RESULT: $RESULT" 
    if [[ $RESULT -eq 0 ]]
    then
        echo "Running equilibration again with longer wall time"
        run_eq $1 $2                #Use the same domain and iteration
    else
        echo "Equilibration was successful"
    fi
}

#Ask user if they wish to continue simulation with the next iteration
ask_continue () {
    echo "The first iteration of pulling and equilibration has finished."
    echo "Please check the pullf and pullx files, aswell as the trajectory files and make sure everything looks correct."
    while true; do
        read -p "Do you wish to continue to the next iteration? Y/N?" ANSWER        #Ask if the user wishes to continue simulations
        case "$ANSWER" in
            [yY] | [yY][eE][sS])
                echo "You answered yes. Continuing the simulations"
                break
                ;;
            [nN] | [nN][oO])
                echo "You answered no. Exiting"
                exit 1
                ;;
            *)
                echo "Invalid input" >&2
        esac
    done
}

#Function for cleaning up unnecessary files
cleanup () {
    echo "Removing files from the unsuccessful simulations is recommended."
    read -p "Do you want to delete unnecessary files? Y/N" CLEAN
    case "$CLEAN" in 
        [yY] | [yY][eE][sS])
            echo "You answered yes. Deleting unnecessary files."

            break
            ;;
        [nN] | [nN][oO])
            echo "You answered no. Keeping all files."
            break
            ;;
        *)
            echo "Invalid input" >&2
    esac
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
        echo "Running 5 pulling simulations for $DOMAIN domains (iteration $i) with K values: ${K_ARRAY[*]}"

        sleep 15h                           #wait for batch jobs to finish (should take about 14h)

        for ((j=0; j<=4; j++))                  #determine status for each K
        do
            status $j $DOMAIN $K_ARRAY[$j] $i   #status=1 means the K managed to pull/push and status=0 means the K didn't manage to pull/push
        done

        check_if_done                           #check if the best K has been found
        if [[ $RES -eq 1 ]]                     #stop search is best K is found
        then
            ROUTE+=(pull_${DOMAIN}${i}_$BEST_K)
            PULLF="pull_${DOMAIN}${i}_${BEST_K}f.xvg"
            PULLX="pull_${DOMAIN}${i}_${BEST_K}x.xvg"
            /usr/bin/env python3 pull_plot.py $PULLX $PULLF
            local FINAL_TEXT="The optimal force constant for ${DOMAIN} domain (iteration: $i) has been found"
            echo "$FINAL_TEXT"
            echo "K=$BEST_K"
        else
            new_K                         #continue searching for best K
        fi

        while [[ $RES -eq 0 ]]         #while K isn't found yet
        do
            run_pull $i $K_MID $DOMAIN
            status 1 $K_MID
            check_if_done
            if [[ $RES -eq 1 ]]
            then
                ROUTE+=(pull_${DOMAIN}${i}_$BEST_K)
                PULLF="pull_${DOMAIN}${i}_${BEST_K}f.xvg"
                PULLX="pull_${DOMAIN}${i}_${BEST_K}x.xvg"
                /usr/bin/env python3 pull_plot.py $PULLX $PULLF
                local FINAL_TEXT="The optimal force constant has been found"
                echo "$FINAL_TEXT"
                FORCE_CONSTANT=$K_MID
                echo "K=$FORCE_CONSTANT"
                done
            else
                new_K                                   #continue searching for best K
            fi
        done

        run_eq $DOMAIN $i                           #equilibrate

        sleep 15h

        if [[ $i -ne $NUM_OF_ITERATIONS ]]
        do
            ask_continue                                #ask user if they wish to continue with the next iteration
        else
            echo "That was the last iteration. The program will stop now."
        fi

        GRO_FILE=pull_eq_${DOMAIN}$i                #next iteration will continue with the gro file from the equilibration
    done
}




#This is actually running the simulations
#Run simulation for each domain (e.g. TK, JM and TM)
#Number of iterations depends on the target distance
    for ((i=0; i<$NUM_OF_DOMAINS; i++))
    do
        case "${DIRECTIONS[${DOMAIN_NAMES[$i]}]}" in
            [Pp][Uu][Ll][lL])
                SIGN='+'
                ;;
            [pP][Uu][sS][hH])
                SIGN='-'
                ;;
        esac
        run_simulation $DOMAIN_NAMES[$i] ${ITERATIONS[${DOMAIN_NAMES[$i]}]}
    done


    

done