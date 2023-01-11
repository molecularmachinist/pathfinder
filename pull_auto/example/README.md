PATHFINDER - USAGE EXAMPLE

Insulin receptor (IR) TK domain pulling example

Needed files:
-pathfinder.py
-sbatch.sh (template)
-config.py (template)

-toppar (Files for structure)
-topol.top
-step7.gro 
-index.ndx

-pull_eq.mdp (template)
-pull_TK.mdp (template)

Setup
Here solvation, energy minimization, equilibration etc. have all been done for you.
When using this tool, you need to do these yourself.
-modify files as needed
-login to mahti
-copy needed files into your mahti repo
-import gromacs and python-data
(module load ...)

Start
-python pathfinder.py init