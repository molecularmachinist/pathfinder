#!/bin/bash

module load gromacs

declare -A STATUS_ARRAY                           
STATUS_ARRAY[0]=0

status () {
    local INDEX=$1
    local DOMAIN=$2
    local K=$3
    local ITERATION=$4

    GET_LINE=$(sed '18q;d' pull_${DOMAIN}${ITERATION}_${K}x.xvg)             #get first distance (18th line of xvg file)
    echo $GET_LINE
    FIRST=${GET_LINE: -7}                           
    echo $FIRST
    LAST=`tail -n 1 pull_${DOMAIN}${ITERATION}_${K}x.xvg | awk '{print $2}'` #get last distance      awk print $2 means print second column and $2 is not referencing to K (second input parameter)
    echo $LAST
    DX=$(expr "$LAST - $FIRST" | bc -l)                 #difference in x
    echo $DX
    if [[ $(echo "$DX>=0.9" | bc -l) -eq "1" ]]                 #if distance between the domains is >= 0.9
    then
        STATUS_ARRAY[$INDEX]=1                              #1 = successful
        echo "Status for $DOMAIN domain iteration $ITERATION K=$K is successful"
    else
        STATUS_ARRAY[$INDEX]=0                              #0 = unsuccessful
        echo "Status for $DOMAIN domain iteration $ITERATION K=$K is unsuccessful"
    fi
}

status 0 TK 20 1

status 0 TK 30 1