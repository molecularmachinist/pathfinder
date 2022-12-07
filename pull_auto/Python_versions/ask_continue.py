#!/usr/bin/env python3

import sys

def ask_continue():
    print("The first iteration of pulling and equilibration has finished.")
    print("Please check the pullf and pullx files, aswell as the trajectory files and make sure everything looks correct.")
    answer = input('Do you want to continue to the next iteration? (y/n)')
    if answer == 'y':
        print("You answered yes. Continuing simulations...")
    elif answer == 'n':
        print("You answered no. Exiting...")
        sys.exit()
    else:
        print("Invalid answer. Please try again.")
        ask_continue()

ask_continue()