#!/bin/bash

NUM_OF_ITERATIONS=3

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


for ((i=1; i<=$NUM_OF_ITERATIONS; i++))          
do

    echo "This is iteration $i"

    if [[ $i -ne $NUM_OF_ITERATIONS ]]
    then
        ask_continue                                #ask user if they wish to continue with the next iteration
    else
        echo "That was the last iteration. The program will stop now."
    fi
done