#!/usr/bin/env python3

def cleanup():
    print("Removing files from the unsuccessful simulations is recommended.")
    # ask user if they want to remove files
    answer = input("Do you want to remove files? (y/n)")
    if answer == 'y':
        print("Removing files...")
        # remove files
    elif answer == 'n':
        print("Not removing files.")
    else:    
        print("Invalid answer. Please try again.")
        cleanup()


cleanup()