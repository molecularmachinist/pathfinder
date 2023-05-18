# Pathfinder with multiple coordinates
This is a (work in progress) version of the pathfinder tool, that is able to pull along more than one reaction coordinate simultaneously (or back to back), and check successes and perform equilibrations etc. like the "original" pathfinder. This feature is not yet implemented, and the code in this folder is still unfinished.

# Main ideas
Input files remain mostly the same, config.ini and mdp files need info about the coordinates.
The plan for multiple coordinates includes:
* Run pulling on first coordinate and use position restraints on the rest of the coordinates
* Find the best K for the first coordinate
* Then use this best K to find the best Ks for the rest of the coordinates in a similar way using position restraints
* When the best Ks have been found for each coordinate, equilibrate everything

Currently the code in this folder does not work according to the plan above. This code pulls along the reaction coordinates simultaneously, which is perhaps not the best idea. The ```init``` function works for 2 coordinates, and the ```contpull``` function works correcly until status check, then onward it does not work. It may be the case, that the code in the pathfinder_multi.py file is mostly useless, and it might be easier to start over and use the original pathfinder.py in the Python_versions folder as a base to implement the multiple coordinates feature.
