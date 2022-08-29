#!/bin/bash


K_MIN=10
K2=20
K_MID=30
K4=40
K_MAX=50

K_ARRAY=($K_MIN $K2 $K_MID $K4 $K_MAX) 
echo "Current values of K are: ${K_ARRAY[*]}"
declare -A STATUS_ARRAY                           
STATUS_ARRAY[0]=0
STATUS_ARRAY[1]=0
STATUS_ARRAY[2]=1
STATUS_ARRAY[3]=1
STATUS_ARRAY[4]=1

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

new_K_5

K_MIN=5
K_MID=25
K_MAX=50

STATUS_ARRAY[1]=1

new_K_3
