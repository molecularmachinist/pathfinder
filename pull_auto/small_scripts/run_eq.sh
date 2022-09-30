#!/bin/bash
LOG_LOCATION=/mnt/c/Users/vanil/Documents/HY/pull_script.sh/pathfinder/pull_auto
exec > >(tee -a $LOG_LOCATION/output.txt)
exec 2>&1

run_eq() {
    #gmx_mpi rms -s pull_eq_${DOMAIN}${ITERATION}.tpr -f pull_eq_${DOMAIN}${ITERATION}.trr -o pull_eq_${DOMAIN}${ITERATION}_rmsd.xvg -tu ns
    #echo "backbone backbone"

    DOMAIN=TK
    FILE="rmsd.xvg"
    RESULT=$(/usr/bin/env python3 analyze.py $FILE $DOMAIN)      
    echo "RESULT: $RESULT"                                      #0 means fail, the slope wasnt close enough to 0
    if [[ $RESULT -eq 0 ]]
    then
        echo "Running equilibration again with a longer wall time."
        #run_eq $1 $2                #Use the same domain and iteration
    else
        echo "Equilibration was successful."
    fi
}

run_eq