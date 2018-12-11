
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


# # 1) Test on short, fake dataset which covers all directional sectors

# In[5]:


# create dataset
date_today = datetime.now()
days = pd.date_range(date_today, date_today + timedelta(24), freq='D')
data = pd.DataFrame({'DTM': days})
data = data.set_index('DTM')
data['Spd1'] = [1,np.nan,1,1,1,1,1,1,1,np.nan,1,1,1,1,np.nan,1,1,1,1,1,1,1,np.nan,1,1]
data['Spd2'] = [2,2,np.nan,2,2,2,2,2,np.nan,2,2,2,2,np.nan,2,2,2,np.nan,2,2,2,2,2,np.nan,2]
data['Dir'] = [0,15,30,45,60,75,90,105,120,135,150,165,180,195,210,225,240,255,270,285,300,315,330,345,360]
data


# ## 1) Test Case 1: Neither boom is near 0-360 crossover

# In[21]:


data['Sel_Avg'] = selective_avg(data.Spd1,data.Spd2,data.Dir, boom_dir1=315,boom_dir2=135,inflow_span=60)
concat = data[['Spd1','Spd2','Dir','Sel_Avg']]
concat


# ## 1) Test Case 2: Boom 1 is near 0-360 crossover¶

# In[15]:


data['Sel_Avg'] = selective_avg(data.Spd1,data.Spd2,data.Dir, boom_dir1=20,boom_dir2=200,inflow_span=60)
concat = data[['Spd1','Spd2','Dir','Sel_Avg']]
concat


# ## 1) Test Case 3: Boom 2 is near 0-360 crossover

# In[16]:


data['Sel_Avg'] = selective_avg(data.Spd1,data.Spd2,data.Dir, boom_dir1=175,boom_dir2=355,inflow_span=60)
concat = data[['Spd1','Spd2','Dir','Sel_Avg']]
concat


# ## 1) Test Case 4: Booms at 90 deg to eachother

# In[22]:


data['Sel_Avg'] = selective_avg(data.Spd1,data.Spd2,data.Dir, boom_dir1=270,boom_dir2=180,inflow_span=60)
concat = data[['Spd1','Spd2','Dir','Sel_Avg']]
concat


# # 2) Timed test on real mast data

# In[4]:


# load data
data = bw.load_timeseries(r'C:\Dropbox (brightwind)\Consult\Coillte\2018-11-05-Castlebanny LT assessement\1. Analysis\2018-11-07-AG-Castlebanny_mast_data_clean.csv')
data


# In[24]:


import datetime
import time
start_time = time.time()
data['Sel_Avg_80m'] = selective_avg(data.Spd_80m_315,data.Spd_80m_135,data.Dir_77m_315, boom_dir1=315,boom_dir2=135,inflow_span=60)
concat = data[['Spd_80m_315','Spd_80m_135','Dir_77m_315','Sel_Avg_80m']]
print(time.time() - start_time)


# In[25]:


concat.head(800)

