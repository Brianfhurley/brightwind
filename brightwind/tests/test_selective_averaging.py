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

