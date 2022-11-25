#!/usr/bin/env python3

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import linregress
import math
import subprocess

def bash_command(cmd):
    subprocess.Popen(cmd, shell=True, executable='/bin/bash')

#subprocess.run(["ls"])
#bash_command('echo "backbone"')

#file=sys.argv[1]
#domain=sys.argv[2]
#file="rmsd.xvg"
#domain="TK"
def analyze(file, domain):
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
    plt.savefig('rmsd.png')
    plt.show()
    if res == 0:
        #print("The equilibration wasn't successful. The structure isn't equilibrated enough.")
        return 0
    else:
        #print("The equilibration was successful.")
        return 1