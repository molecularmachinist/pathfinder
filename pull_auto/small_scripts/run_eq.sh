#!/bin/bash

run_eq() {
    #gmx_mpi rms -s pull_eq_${DOMAIN}${ITERATION}.tpr -f pull_eq_${DOMAIN}${ITERATION}.trr -o pull_eq_${DOMAIN}${ITERATION}_rmsd.xvg -tu ns
    #echo "backbone backbone"

    DOMAIN=TK
    FILE="rmsd.xvg"
    RESULT=$(/usr/bin/env python3 analyze.py $FILE $DOMAIN)      #0 means fail, the slope wasnt close enough to 0
    echo "RESULT: $RESULT" 
    #run longer simulation
}

run_eq