#!/usr/bin/env python3

import sys
import os
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import scipy
from scipy.stats import linregress
import math



file=sys.argv[1]
domain=sys.argv[2]
#file="rmsd.xvg"
x,y = np.loadtxt(file,comments=["@","#"],unpack=True)
n=math.ceil(0.8*len(x))
x=x[-n:]
y=y[-n:]
slope=linregress(x,y).slope
slope=float('{:f}'.format(slope))
#print("Slope:", slope)
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
plt.show()
print(res)