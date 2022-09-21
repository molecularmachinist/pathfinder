#!/usr/bin/env python3

import sys
import os
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import math
import subprocess

pullx_file=sys.argv[1]
pullf_file=sys.argv[2]
 
x,y = np.loadtxt(pullx_file,comments=["@","#"],unpack=True)
n=math.ceil(0.8*len(x))
x=x[-n:]
y=y[-n:]
figure = plt.figure(figsize=(6,3))
ax = figure.add_subplot(111)
ax.plot(x, y)
ax.set_xlim(x[0], x[-1])
ax.set_xlabel("Time (ps)")
ax.set_ylabel("COM")
ax.set_title("Pull COM")
figure.tight_layout()
plt.savefig('../outputs/{}.png'.format(pullx_file))
plt.show()

x,y = np.loadtxt(pullf_file,comments=["@","#"],unpack=True)
n=math.ceil(0.8*len(x))
x=x[-n:]
y=y[-n:]
figure = plt.figure(figsize=(6,3))
ax = figure.add_subplot(111)
ax.plot(x, y)
ax.set_xlim(x[0], x[-1])
ax.set_xlabel("Time (ps)")
ax.set_ylabel("Pull force")
ax.set_title("Pull force for COM pulling")
figure.tight_layout()
plt.savefig('../outputs/{}.png'.format(pullf_file))
plt.show()