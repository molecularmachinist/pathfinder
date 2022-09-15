#!/bin/bash

run_eq() {
    #gmx_mpi rms -s pull_eq_${DOMAIN}${ITERATION}.tpr -f pull_eq_${DOMAIN}${ITERATION}.trr -o pull_eq_${DOMAIN}${ITERATION}_rmsd.xvg -tu ns
    #echo "backbone backbone"

    FILE="rmsd.xvg"
    echo "HI"
    #RESULT=$(/usr/bin/env python3 analyze.py $FILE)      #0 means fail, the slope wasnt close enough to 0
    RESULT=0
    if [[ $RESULT -eq 0 ]]                               #1 means success, the slope was close enough to 0  
    then
        echo "The equilibration wasn't successful. The structure isn't equilibrated enough."
        #echo "Please increase equilibration wall time."
        #read -p "Please give a longer wall time for equilibration. New time: " TIME       
        #Some input error handling here
        #Make sure new time is an integer
        #Make sure new time is longer than old time
        #slurm time should also be increased 
        EQ_TIME=$TIME
        #run_eq $1 $2
    else
        echo "The equilibration was successful."
    fi
}
