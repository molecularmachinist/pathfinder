#!/bin/bash

module load gromacs

#Array for domain/molecule names that the user wants to be pulled/pushed
declare -A DOMAIN_NAMES
#Array for starting distances
declare -A STARTS
#Array for number of iterations each total pull will need
declare -A ITERATIONS
#Array for keeping track of the successful route of simulations
declare -A ROUTE


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
    read -p "Push (together) or pull (apart)? Answer push/pull " DIRECTION
    case "$DIRECTION" in
            [Pp][Uu][Ll][lL])
                echo "You answered pull."
                SIGN='+'
                ;;
            [pP][Uu][sS][hH])
                echo "You answered push."
                SIGN='-'
                ;;
            *)
                echo "Invalid input" >&2
        esac
    read -p "What is the starting distance? Enter in nm: " START
    read -p "What is the target distance? Enter in nm: " TARGET                                                                       
    STARTS+=( ["${DOMAIN_NAME}"]=${START} )
    ITERATIONS+=( ["${DOMAIN_NAME}"]=$(expr "$TARGET-${STARTS[${DOMAIN_NAME}]}" | bc -l) )
done

DOMAIN=$DOMAIN_NAME
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

run_pull () {
    local ITERATION=$1
    local K=$2
    local DOMAIN=$3

    sed -i '$d' pull_$DOMAIN.mdp                                                        #delete last two lines of mdp file (pull_coord_init and K lines)
    sed -i '$d' pull_$DOMAIN.mdp
    echo "pull_coord1_k = ${SIGN}$K" >> pull_${DOMAIN}.mdp                                #set K in mdp                                                                                               #get starting distance
    INIT=$(expr "${STARTS[${DOMAIN}]} $SIGN 1.5" | bc -l)                               #pull/push 1nm (+0.5 for margin)
    echo "pull_coord1_init = ${INIT}" >> pull_${DOMAIN}.mdp                                 #set init distance in mdp
    gmx_mpi grompp -f pull_$DOMAIN.mdp -c $GRO_FILE -p topol.top -r $GRO_FILE -n $INDEX_FILE -o pull_${DOMAIN}${ITERATION}_$K.tpr -maxwarn 1
    sed -i '$d' pull_$DOMAIN.sh
    echo "srun gmx_mpi mdrun -v -deffnm pull_${DOMAIN}${ITERATION}_$K -pf pull_${DOMAIN}${ITERATION}_${K}f.xvg -px pull_${DOMAIN}${ITERATION}_${K}x.xvg" >> pull_$DOMAIN.sh
    sbatch --output=pull_${DOMAIN}${ITERATION}_$K.txt --job-name=pull_${DOMAIN}${ITERATION}_$K pull_$DOMAIN.sh                                                                                                                              
    echo "Pulling $DOMAIN domains (iteration $ITERATION) with K=$K"
}

for ((j=0; j<=4; j++))                  #run pulling sims for 5 different Ks
do
    run_pull 1 ${K_ARRAY[$j]} $DOMAIN
done