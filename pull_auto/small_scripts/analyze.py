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
slope=linregress(x,y)
print(slope)