#!/bin/bash

read_config () {
    . input.config
    
    # case "$DIRECTION" in
    #     [Pp][Uu][Ll][lL])
    #         SIGN='+'
    #         ;;
    #     [pP][Uu][sS][hH])
    #         SIGN='-'
    #         ;;
    #     *)
    #         echo "Invalid input" >&2
    # esac

    echo "Starting gro file=${GRO_FILE}"
    echo "Number of domains=${NUM_OF_DOMAINS}"

    i=0
    for d in "${DOMAIN_NAMES[@]}"
    do
        echo "Info for ${d} domain: "
        DIRECTIONS[$d]=${DIRECTIONS[$i]}
        echo "Direction: ${DIRECTIONS[$d]}"
        STARTS[$d]=${STARTS[$i]}
        TARGETS[$d]=${TARGETS[$i]}
        K_MAX[$d]=${K_MAX[$i]}
        ITERATIONS+=( ["$d"]=$(expr "${TARGETS[$d]}-${STARTS[$d]}" | bc -l) )
        i+=1
    done
}

read_config