#! /usr/bin/env python3

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import scipy
from scipy.stats import linregress
import math
import sys
import os


file=sys.argv[1]
x,y = np.loadtxt(file,comments=["@","#"],unpack=True)
n=math.ceil(0.8*len(x))
x=x[-n:]
y=y[-n:]
slope=linregress(x,y).slope
slope=float('{:f}'.format(slope))
if slope < 0.25 and slope > -0.25:
    res=1
else:
    res=0
print(res)