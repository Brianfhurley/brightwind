
# coding: utf-8

# In[1]:


# Andy Good - 2018-11-21
import brightwind as bw
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


# # Define function

# In[2]:


# Define inner functions

# define thresholds used to determine if an anemometer is in the mast shadow
def _calc_sector_limits(boom_dir, inflow_span = 60): 
    inflow_lower = (boom_dir - (inflow_span / 2) + 180) % 360
    inflow_higher = (boom_dir + (inflow_span / 2) + 180) % 360
    return inflow_lower, inflow_higher

# define selective averaging method
def _selective_avg(wspd1, wspd2, wdir, boom_dir1, boom_dir2, inflow_lower1, inflow_higher1, inflow_lower2, inflow_higher2, inflow_span = 60):
    # duplicate threshold values into lists which are the same length as other inputs
    inflow_lower1 = [inflow_lower1] * len(wdir) 
    inflow_higher1 = [inflow_higher1] * len(wdir)
    inflow_lower2 = [inflow_lower2] * len(wdir)
    inflow_higher2 = [inflow_higher2] * len(wdir)
    # if boom 1 'inflow' sector overlaps with 0/360
    if ((boom_dir1 + 180) % 360) >= (360 - (inflow_span/2)) or ((boom_dir1 + 180) % 360) <= (inflow_span/2):
        # many nested if statments follow, all within one mapped lamda function
        sel_avg = list(map(lambda spd1,spd2,Dir,inflowlow1,inflowhigh1,inflowlow2,inflowhigh2: 
                           # if one value is Nan, use the other one
                           spd2 if (np.isnan(spd1)==True) else (spd1 if np.isnan(spd2)==True 
                               # use spd1 if 2 is in mast shadow
                               else (spd1 if Dir >= inflowlow2 and Dir <= inflowhigh2 
                                  # use spd2 if 1 is in mast shadow ('left' of 360) 
                                  else (spd2 if Dir >= inflowlow1 and Dir <= 360 
                                        # use spd2 if 1 is in mast shadow ('right' of 0)
                                        else (spd2 if Dir >= 0 and Dir <= inflowhigh1 
                                              # otherwise, selective average
                                              else (spd1 + spd2)/2)))),
                           # end of map function, list input variables
                           wspd1,wspd2,wdir,inflow_lower1,inflow_higher1,inflow_lower2,inflow_higher2))           
    # if boom 2 'inflow' sector overlaps with 0/360
    elif ((boom_dir2 + 180) % 360) >= (360 - (inflow_span/2)) or ((boom_dir2 + 180) % 360) <= (inflow_span/2): 
        # many nested if statments follow, all within one mapped lamda function
        sel_avg = list(map(lambda spd1,spd2,Dir,inflowlow1,inflowhigh1,inflowlow2,inflowhigh2:
                           # if one value is Nan, use the other one
                           spd2 if (np.isnan(spd1)==True) else (spd1 if np.isnan(spd2)==True 
                               # use spd2 if 1 is in mast shadow
                               else (spd2 if (Dir >= inflowlow1 and Dir <= inflowhigh1)
                                  # use spd1 if 2 is in mast shadow ('left' of 360)
                                  else (spd1 if (Dir >= inflowlow2 and Dir <= 360) 
                                        # use spd1 if 2 is in mast shadow ('right' of 0)
                                        else (spd1 if (Dir >= 0 and Dir <= inflowhigh2) 
                                              # otherwise, selective average
                                              else (spd1 + spd2)/2)))),
                           # end of map function, list input variables
                           wspd1,wspd2,wdir,inflow_lower1,inflow_higher1,inflow_lower2,inflow_higher2))
    # if neither boom 'inflow' sectors overlap with 0/360 threshold
    else: 
        # many nested if statments follow, all within one mapped lamda function
        sel_avg = list(map(lambda spd1,spd2,Dir,inflowlow1,inflowhigh1,inflowlow2,inflowhigh2:
                           # if one value is Nan, use the other one
                           spd2 if np.isnan(spd1)==True else (spd1 if np.isnan(spd2)==True 
                              # use spd2 if 1 is in mast shadow 
                              else (spd2 if (Dir >= inflowlow1 and Dir <= inflowhigh1) 
                                    # use spd1 if 2 is in mast shadow and spd1 is not Nan
                                    else (spd1 if (Dir >= inflowlow2 and Dir <= inflowhigh2) 
                                           # otherwise, selective average
                                           else (spd1 + spd2) / 2))),
                            # end of map function, list input variables
                            wspd1,wspd2,wdir,inflow_lower1,inflow_higher1,inflow_lower2,inflow_higher2))
    return sel_avg


# In[3]:


# define main function
def selective_avg(wspd1, wspd2, wdir, boom_dir1, boom_dir2, inflow_span=60):
    inflow_lower1,inflow_higher1 = _calc_sector_limits(boom_dir1, inflow_span)
    inflow_lower2,inflow_higher2 = _calc_sector_limits(boom_dir2, inflow_span)
    sel_avg = _selective_avg(wspd1, wspd2, wdir, boom_dir1, boom_dir2, inflow_lower1, inflow_higher1, inflow_lower2, inflow_higher2)
    return sel_avg
