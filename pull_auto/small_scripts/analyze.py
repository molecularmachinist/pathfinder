#!/usr/bin/env python3

import sys
import os
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import scipy
from scipy.stats import linregress
import math
import subprocess

def bash_command(cmd):
    subprocess.Popen(cmd, shell=True, executable='/bin/bash')

#subprocess.run(["ls"])
#bash_command('echo "backbone"')

file=sys.argv[1]
domain=sys.argv[2]
#file="rmsd.xvg"
#domain="TK"

x,y = np.loadtxt(file,comments=["@","#"],unpack=True)
n=math.ceil(0.8*len(x))
x=x[-n:]
y=y[-n:]
slope=linregress(x,y).slope
slope=float('{:f}'.format(slope))  
#print("Slope:", slope)         #Write slope into output file
if slope < 0.25 and slope > -0.25:
    res=1
else:
    res=0
figure = plt.figure(figsize=(6,3))
ax = figure.add_subplot(111)
ax.plot(x, y)
ax.set_xlim(x[0], x[-1])
ax.set_ylim(0, 2)
ax.set_xlabel("Time (ns)")
ax.set_ylabel("RMSD (Å)")
ax.set_title("RMSD: Equilibration of {} domain".format(domain))
figure.tight_layout()
plt.savefig('../outputs/rmsd.png')
plt.show()
if res == 0:
    print("The equilibration wasn't successful. The structure isn't equilibrated enough.")
    print("Please increase the equilibration time by increasing the number of steps.")
    while True:
        try:
            steps=int(input("Please give the new number of steps. New nsteps: "))
        except ValueError:
            print("Please give the steps as an integer.")
            continue
        else:
            break
    print("Make sure to also increase slurm time!")
    bash_command("sed -i '$d' pull_eq.mdp")               #remove nsteps from mdp file
    with open("pull_eq.mdp", "a") as f:
        f.write("nsteps          = ", steps)
    print(0)
else:
    #print("The equilibration was successful.")
    print(1)