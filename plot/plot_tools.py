import matplotlib.pyplot as plt
import calendar
import numpy as np
import pandas as pd
from analyse.frequency_analysis import *

plt.style.use(r'C:\Dropbox (brightwind)\RTD\repos-hadley\brightwind\plot\bw.mplstyle')


def BWcolors(BWcolor):
    #Define color scheme to be used across graphs, and tables.
    if BWcolor == 'green':
        BWcolor = [156, 197, 55]
    elif BWcolor == 'asphault':
        BWcolor = [46, 55, 67]
    elif BWcolor == 'greyline':
        BWcolor = [108, 120, 134]
    elif BWcolor == 'darkgreen':
        BWcolor = [108, 144, 35]
    elif BWcolor == 'redline':
        BWcolor = [255, 0, 0]
    else:
        BWcolor = [156, 197, 55]
    BWcolor[:] = [x / 255 for x in BWcolor]
    return BWcolor


def plot_freq_distribution(data, max_speed=30, save_fig=False):
    from matplotlib.ticker import PercentFormatter
    fig = plt.figure(figsize=(15, 8))
    ax = fig.add_axes([0.1, 0.1, 0.8,0.8])
    ax.set_xlabel('Speed [m/s]')
    ax.set_ylabel('Frequency [%]')
    if isinstance(data.index[0], pd.Interval):
        ax.set_xticks([i.mid for i in data.index])
    else:
        ax.set_xticks(data.index)
    ax.set_xlim(-0.5,max_speed+0.5)
    ax.set_ylim(0,max(data)+5)
    ax.yaxis.set_major_formatter(PercentFormatter())
    ax.grid(b=True, axis='y', zorder=0)
    #ax.bar(result.index, result.values,facecolor='#9ACD32',edgecolor=['#6C9023' for i in range(len(result))],zorder=3)
    for frequency, bin in zip(data,[i.mid for i in data.index]):
        ax.imshow(np.array([[[154, 205, 50]], [[215, 235, 173]]])/255.0, interpolation='gaussian',
                  extent=(bin-0.4, bin+0.4, 0, frequency), aspect='auto', zorder=3)
        ax.bar(bin, frequency, edgecolor='#6c9023', linewidth=0.3, fill=False, zorder=5)
    ax.set_title('Wind Speed Frequency Distribution')
    if save_fig:
        plt.savefig(save_fig)
    plt.show()


def plot_wind_rose(data, freq_table=False, direction_col_name=0,sectors=12):
    """Plot a wind rose from a direction data or a frequency table.
    """
    if not freq_table:
        data = data.dropna(subset=[direction_col_name])
        data.loc[:, 'direction_bin'] = data[direction_col_name].apply(map_direction_bin,
                                                                      bins=get_direction_bin_array(sectors))
        result = data['direction_bin'].value_counts() / len(data['direction_bin']) * 100.0
        result.loc[1] += result.loc[sectors+1]
        result = result.drop(sectors+1, axis=0).sort_index()
    else:
        sectors= data.shape[1]
        result = data.sum(axis=0)
    fig = plt.figure(figsize=(12, 12))
    ax = fig.add_axes([0.1, 0.1, 0.8,0.8], polar=True)
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    ax.set_thetagrids(np.arange(0,360,360.0/sectors))
    ax.set_rgrids(np.arange(0,101,10),labels=[str(i)+'%' for i in np.arange(0,101,10)],angle=0)
    ax.bar(np.arange(0,2.0*np.pi,2.0*np.pi/sectors), result, width=2.0*np.pi/sectors, bottom=0.0,color='#9ACD32',
           edgecolor=['#6C9023' for i in range(len(result))],alpha=0.8)
    ax.set_title(str(direction_col_name)+' Wind Rose',loc='center')
    plt.show()


def plot_wind_rose_with_speed_3_bins(table):
    import matplotlib as mpl
    sectors=len(table.columns)
    table_binned=pd.DataFrame()
    table_trans = table.T
    table_binned = pd.concat([table_binned,table_trans.loc[:,0:3].sum(axis=1).rename(3)],axis=1)
    table_binned = pd.concat([table_binned,table_trans.loc[:,4:6].sum(axis=1).rename(6)],axis=1)
    table_binned = pd.concat([table_binned,table_trans.loc[:,7:9].sum(axis=1).rename(9)],axis=1)
    table_binned = pd.concat([table_binned,table_trans.loc[:,10:12].sum(axis=1).rename(12)],axis=1)
    table_binned = pd.concat([table_binned,table_trans.loc[:,13:15].sum(axis=1).rename(15)],axis=1)
    table_binned = pd.concat([table_binned, table_trans.loc[:, 16:].sum(axis=1).rename(18)], axis=1)
    table_binned = table_binned.T
    fig = plt.figure(figsize=(12, 12))
    ax = fig.add_axes([0.1, 0.1, 0.8,0.8], polar=True)
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    ax.set_thetagrids(np.arange(0,360,360.0/sectors))
    ax.set_rgrids(np.linspace(0,max(table.sum(axis=0))+2.0,10),labels=[ '%.0f' % round(i)+'%' for i in
                                                                np.linspace(0,max(table.sum(axis=0))+2.0,10)],angle=0)
    direction_bins = get_direction_bin_array(sectors)[1:-2]
    direction_bins = np.insert(direction_bins,0,direction_bins[-2])
    ax.set_ylim(0,max(table.sum(axis=0))+3.0)
    angular_width = 2*np.pi/sectors - (np.pi/180) #Leaving 1 degree gap
    def _choose_color(speed_bin):
        colors = ['#f5faea','#d6ebad','#b8dc6f','#9acd32','#7ba428', '#5c7b1e']
        bins = [0,3.5,6.5,9.5,12.5,15.5,18.5,41]
        return(colors[np.digitize([speed_bin], bins)[0]-1])

    for column in table_binned:
        radial_pos = 0.0
        angular_pos = (np.pi / 180.0) * float(column.split('-')[0])
        for speed_bin,frequency in zip(table_binned.index,table_binned[column]):
            color = _choose_color(speed_bin)
            patch = mpl.patches.Rectangle((angular_pos, radial_pos), angular_width, frequency, facecolor=color,
                                          edgecolor='#5c7b1e',linewidth=0.3)
            ax.add_patch(patch)
            radial_pos += frequency
    legend_patches = [mpl.patches.Patch(color='#f5faea', label='0-3 m/s'),
                        mpl.patches.Patch(color='#d6ebad', label='4-6 m/s'),
                        mpl.patches.Patch(color='#b8dc6f', label='7-9 m/s'),
                        mpl.patches.Patch(color='#9acd32', label='10-12 m/s'),
                        mpl.patches.Patch(color='#7ba428', label='13-15 m/s'),
                      mpl.patches.Patch(color='#5c7b1e', label='15+ m/s')]
    ax.legend(handles=legend_patches)
    plt.show()


def plot_wind_rose_with_speed(table):
    import matplotlib as mpl
    sectors=len(table.columns)
    table_binned=pd.DataFrame()
    table_trans = table.T
    table_binned = pd.concat([table_binned,table_trans.loc[:,0:4].sum(axis=1).rename(4)],axis=1)
    table_binned = pd.concat([table_binned,table_trans.loc[:,5:8].sum(axis=1).rename(8)],axis=1)
    table_binned = pd.concat([table_binned,table_trans.loc[:,9:12].sum(axis=1).rename(12)],axis=1)
    table_binned = pd.concat([table_binned,table_trans.loc[:,13:16].sum(axis=1).rename(16)],axis=1)
    table_binned = pd.concat([table_binned,table_trans.loc[:,17:].sum(axis=1).rename(40)],axis=1)
    table_binned = table_binned.T

    fig = plt.figure(figsize=(12, 12))
    ax = fig.add_axes([0.1, 0.1, 0.8,0.8], polar=True)
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    ax.set_thetagrids(np.arange(0,360,360.0/sectors))
    ax.set_rgrids(np.linspace(0,max(table.sum(axis=0))+2.0,10),labels=[ '%.0f' % round(i)+'%' for i in
                                                                np.linspace(0,max(table.sum(axis=0))+2.0,10)],angle=0)
    direction_bins = get_direction_bin_array(sectors)[1:-2]
    direction_bins = np.insert(direction_bins,0,direction_bins[-2])
    ax.set_ylim(0,max(table.sum(axis=0))+3.0)
    angular_width = 2*np.pi/sectors - (np.pi/180) #Leaving 1 degree gap

    def _choose_color(speed_bin):
        colors = ['#d6ebad','#b8dc6f','#9acd32','#7ba428', '#5c7b1e']
        bins = [0,4.5,8.5,12.5,16.5,41]
        return(colors[np.digitize([speed_bin], bins)[0]-1])

    for column in table_binned:
        radial_pos = 0.0
        angular_pos = (np.pi / 180.0) * float(column.split('-')[0])
        for speed_bin,frequency in zip(table_binned.index,table_binned[column]):
            color = _choose_color(speed_bin)
            patch = mpl.patches.Rectangle((angular_pos, radial_pos), angular_width, frequency, facecolor=color,
                                          edgecolor='#5c7b1e',linewidth=0.3)
            ax.add_patch(patch)
            radial_pos += frequency
    legend_patches = [mpl.patches.Patch(color='#d6ebad', label='0-4 m/s'),
                        mpl.patches.Patch(color='#b8dc6f', label='5-8 m/s'),
                        mpl.patches.Patch(color='#9acd32', label='9-12 m/s'),
                        mpl.patches.Patch(color='#7ba428', label='13-16 m/s'),
                        mpl.patches.Patch(color='#5c7b1e', label='16+ m/s')]
    ax.legend(handles=legend_patches)
    plt.show()


def plot_TI_by_Speed(data,speed_col_name,std_col_name):

    #IEC Class 2005
    #Note we have removed option to include IEC Class 1999 as no longer appropriate.
    #This may need to be placed in a separate function when updated IEC standard is released

    columns = ['Windspeed', 'IEC Class A', 'IEC Class B', 'IEC Class C']
    IEC_Class_2005 = pd.DataFrame(np.zeros([26, 4]), columns=columns)

    for n in range(1, 26):
        IEC_Class_2005.iloc[n, 0] = n
        IEC_Class_2005.iloc[n, 1] = 0.16 * (0.75 + (5.6 / n))
        IEC_Class_2005.iloc[n, 2] = 0.14 * (0.75 + (5.6 / n))
        IEC_Class_2005.iloc[n, 3] = 0.12 * (0.75 + (5.6 / n))

    #Get Average Turbulence Intensity and Representative Turbulence Intensity for the plot
    TI = get_TI_by_Speed(data, speed_col_name, std_col_name)
    data['Turbulence_Intensity'] = data[std_col_name] / data[speed_col_name]

    #Plot Figure
    plt.figure(figsize=(15, 7.5))
    plt.scatter([data[speed_col_name]], [data['Turbulence_Intensity']], color=BWcolors('green'), s=1, alpha=0.3)
    plt.plot(TI.iloc[:, 0], TI.iloc[:, 1], color=BWcolors('darkgreen'))
    plt.plot(TI.iloc[:, 0], TI.iloc[:, 5], color=BWcolors('redline'))
    plt.plot(IEC_Class_2005.iloc[:, 0], IEC_Class_2005.iloc[:, 1], color=BWcolors('greyline'))
    plt.plot(IEC_Class_2005.iloc[:, 0], IEC_Class_2005.iloc[:, 2], color=BWcolors('greyline'))
    plt.plot(IEC_Class_2005.iloc[:, 0], IEC_Class_2005.iloc[:, 3], color=BWcolors('greyline'))
    plt.axis([2, 25, 0, 0.6])
    plt.xticks(np.arange(2, 26, 1))
    plt.xlabel('Wind speed [m/s]')
    plt.ylabel('Turbulence Intensity')
    # plt.title('Turbulence Intensity by Windspeed for ' + str(speed_col))
    plt.grid(True)
    plt.legend()
    plt.show()


def plot_TI_by_sector(data,speed_col_name,std_col_name,direction_col_name,sectors,min_speed):

    #First we need to calculate the Turbulence Intensity by sector by calling the sector function.
    TI = get_TI_by_sector(data, speed_col_name, std_col_name, direction_col_name, sectors, min_speed)

    #Next we convert the Median bin degree to radians for plotting
    TI['Polar degrees'] = np.radians(TI.index * (360 / sectors))

    #To complete the plot, we need to copy the first row and append a new last row.
    TI.loc[-1] = TI.loc[0, :]

    #Set Figure size, define it as polar, set north, set number of sectors to be displayed
    fig = plt.figure(figsize=(9, 9))
    ax = fig.add_axes([0.1, 0.1, 0.8, 0.8], polar=True)
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    ax.set_thetagrids(np.arange(0, 360, 360.0 / sectors))
    ax.tick_params(axis='y',labelsize=15)
    #,grid_color='white',labelcolor='white
    #Convert name of Turbulence Intensity Avg Column so it will read well in legend.
    TI['Turbulence Intensity Average by sector'] = TI['Turbulence_Intensity_Avg']

    #Plot the Average turbulence Intensity and assign a title to the graph
    ax.plot(TI['Polar degrees'], TI['Turbulence Intensity Average by sector'], c=BWcolors('green'), linewidth=4)
    plt.title('Turbulence Intensity by Direction')

    #Set the max extent of the polar plot to be the max average sector turbulence + 0.1
    maxlevel = TI['Turbulence_Intensity_Avg'].max() + 0.1
    ax.set_ylim(0, maxlevel)

    #Add in comment at bottom of graph about what anemometer and wind vane are used.
    ax.annotate('*Plot generated using Anemometer ' + speed_col_name + ' and Wind Vane ' + direction_col_name,
                xy=(120, 10), xycoords='figure pixels')

    #Finally produce a scatter plot of all of the Turbulence Intensity data points
    data['Turbulence Intensity by datapoint'] = data[std_col_name] / data[speed_col_name]
    data['Polar degrees'] = np.radians(data[direction_col_name])
    ax.scatter(data['Polar degrees'], data['Turbulence Intensity by datapoint'], c=BWcolors('asphault'), alpha=0.3, s=1)
    plt.legend(loc=8, framealpha=1)
    plt.show()


def plot_monthly_means(data,time_col_name):
    #Get table of monthly means from data passed
    data = get_monthly_means(data, time_col_name)

    #Make Timestamp its own column and not an index
    data = data.reset_index()

    #Setup figure for plotting, then plot all columns in dataframe
    plt.figure(figsize=(15, 7.5))
    for i in range(1, len(data.columns)):
        plt.plot(data.iloc[:, 0], data.iloc[:, i])
    plt.ylabel('Wind speed [m/s]')
    plt.xticks(rotation=90)
    plt.legend()
    plt.show()


def plot_12x24_TI_Contours(data,time_col_name,speed_col_name,std_col_name):
    #Get Contour Plot of 12 month x 24 hour matrix of turbulence intensity
    result = get_12x24_TI_matrix(data,time_col_name,speed_col_name,std_col_name)
    plt.figure(figsize=(15, 7.5))
    x = plt.contourf(result, cmap="Greens")
    cbar = plt.colorbar(x)
    cbar.ax.set_ylabel('Turbulence Intensity')
    plt.xlabel('Month of Year')
    plt.ylabel('Hour of Day')
    plt.xticks(np.arange(12), calendar.month_name[1:13])
    plt.yticks(np.arange(0, 24, 1))
    plt.title('Hourly Mean Turbulence Intensity by Calendar Month')
    plt.show()

