#!/bin/bash

read_config () {
    . input.config
    


    #ERROR HANDLING
    #STOP SCRIPT RUN IF INPUT IS INCORRECT

    echo "Index file=${INDEX_FILE}"

    echo "Starting gro/pdb file=${GRO_FILE}"

    if [[ $GRO_FILE == *.pdb ]]
    then
        echo "Structure file is in pdb format."
        echo "Converting pdb to gro file."
        local prefix=${GRO_FILE::-4}
        gmx_mpi pdb2gmx -f ${GRO_FILE} -o ${prefix}.gro -water tip3p -ignh -his
    fi

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

}

read_config