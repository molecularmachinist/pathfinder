#!/bin/bash

read_config () {
    . input.config
    
    case "$DIRECTION" in
        [Pp][Uu][Ll][lL])
            SIGN='+'
            ;;
        [pP][Uu][sS][hH])
            SIGN='-'
            ;;
        *)
            echo "Invalid input" >&2
    esac

    echo "gro file=${GRO_FILE}"
    echo "num of domains=${NUM_OF_DOMAINS}"
    if [[ ${NUM_OF_DOMAINS} -le 1 ]]
    echo "domain name=${DOMAIN_NAME}"
}

read_config