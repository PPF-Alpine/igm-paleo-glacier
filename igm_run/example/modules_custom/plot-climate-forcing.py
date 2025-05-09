# File: plot-climate-forcing.py
# This script is used to plot the climate forcing data from the EPICA ice core

import os
import numpy as np
import matplotlib.pyplot as plt
 
from netCDF4 import Dataset

# load the EPICA signal from the dT_epica.nc file
epica_nc = Dataset(
    os.path.join("../data/dT_epica.nc")
)
# extract time BP, change to AD (1950 is present for EPICA)
time = np.squeeze(epica_nc.variables["time"]).astype("int")  # unit : years
time = time - 1950
# extract the dT, i.e. global temp. difference
dT = np.squeeze(epica_nc.variables["delta_T"]).astype("float32")  # unit : degree Kelvin
epica_nc.close()

dT_interp = lambda t: np.interp(t, time, dT, left=dT[0], right=dT[-1])

fig, ax1 = plt.subplots()
ax2 = ax1.twinx()
ax1.plot(time, dT_interp(time),'-r') 
ax2.plot(time, 3000 + 200.0*dT_interp(time),'b') 
ax1.set_xlabel('Time')
ax1.set_ylabel('DT', color='g')
ax2.set_ylabel('ELA', color='b')
plt.show()
