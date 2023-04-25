# Instructions for Pathfinder

The Pathfinder tool works in iterations, with the same stages repeating in each iteration.

1. Pulling/pushing simulations until the smallest successful force constant K is found. 
2. Equilibration with flat-bottom position restraints.
3. Repeat

## Before using the tool
You need to perform solvation, energy minimization, equilibration or whatever your system needs before using the tool. 
It is suggested to look at the example (in the example folder) before using this tool.

## Needed files
Templates are found in templates folder
* pathfinder.py
* sbatch.sh (template)
* config.ini (template)

Parameter files for equilibration and 
* eq.mdp (template)
* pull.mdp (template)

Topology and structure files for your system
* itp file(s)
* topol.top
* gro file
* index.ndx

## Setup
* Fill in config.ini with starting parameters
* Fill in mdp files and sbatch.sh
* Copy needed files into Mahti (currently this tool is designed only for Mahti)
* In Mahti, import gromacs and python-data (module load ...)

## Help
```
python pathfinder.py help
```
If you need help remembering which function does what, what arguments the 
functions take as input, or what command you ran previously, you can call the 'help' function.

## Revert
```
python pathfinder.py revert
```
If you run into a situation where you encounter a warning or an error during the simulation and need to restart it, use the revert command to revert the K_array to the previous stage. If you don't, you will notice that contpull will check the wrong K's and will not work correctly.

## Start
```
python pathfinder.py init 0 
```
Each new iteration of simulations is started with the init command, which 
takes one argument as input: the number of the iteration. This will start 
the first round of simulations with 5 different values of K.


## After init
```
python pathfinder.py contpull 0 
```
After pulling simulations, you will always continue with the contpull command, which takes one argument as input: the number of the iteration (starting from 0). This command will check if any of the simulations were successful and if the best K has been found. If it has, the program will ask if you wish to continue to equilibration (yes). If it has not, it will calculate new values for K and ask if you want to run this new set of simulations (yes). Keep running contpull command until you found the best K, and then continue to equilibration.
NOTE: When running contpull, if you encounter an error of type: "ValueError: the number of columns changed from 2 to 1 at row 478; use usecols to select a subset and avoid this error", ignore it for now and just run contpull again. This will be fixed.

## Continuing to equilibration
When the best force constant K has been found, the program will continue from the simulation with the best K into equilibration. 

## After equilibration
```
python pathfinder.py conteq 0 
```
After equilibration, the conteq command will check if the structure is equilibrated enough. The command takes one argument as input: the number of the iteration (starting from 0). If the equilibration time was too short and the structure is not equilibrated enough, it will double the running time and run the equilibration again. If the equilibration was successful, the program will tell you and exit, and now you are ready to continue into the next iteration if you wish. 







