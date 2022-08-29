#!/bin/bash

module load gromacs

declare -A STATUS_ARRAY                           
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
K4=$(( $K4+$K_MID ))

K_ARRAY=($K_MIN $K2 $K_MID $K4 $K_MAX) 
echo "${K_ARRAY[*]}"

K_MID=10
K_MIN=5
echo "${K_ARRAY[*]}"

declare -A STATUS_ARRAY                           
STATUS_ARRAY[0]=0
STATUS_ARRAY[1]=1
STATUS_ARRAY[2]=0
STATUS_ARRAY[3]=0
STATUS_ARRAY[4]=0

check_if_done () {
    if [[ STATUS_ARRAY[1] -eq 1 && ($(expr $K_MID - $K_MIN) -le 5 || $(expr $K2 - $K_MIN) -le 5) ]]         #best force constant is found if K_MID is successful and the difference to K_MIN is < 5
    then
        RES=1                                                             #1=success
        echo "Done"
    else
        RES=0                                                             #0=fail
        echo "Not done"
    fi
}

check_if_done