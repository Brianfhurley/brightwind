#     brightwind is a library that provides wind analysts with easy to use tools for working with meteorological data.
#     Copyright (C) 2018 Stephen Holleran, Inder Preet
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU Lesser General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU Lesser General Public License for more details.
#
#     You should have received a copy of the GNU Lesser General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.

import numpy as np
import pandas as pd
import math
from ..utils import utils

__all__ = ['average_data_by_period', 'adjust_slope_offset', 'scale_wind_speed', 'offset_wind_direction']


def _compute_wind_vector(wspd, wdir):
    """
    Returns north and east component of wind-vector
    """
    return wspd*np.cos(wdir), wspd*np.sin(wdir)


def _convert_days_to_hours(prd):
    return str(int(prd[:-1])*24)+'H'


def _convert_weeks_to_hours(prd):
    return str(int(prd[:-1])*24*7)+'H'


def _get_min_overlap_timestamp(df1_timestamps, df2_timestamps):
    """
    Get the minimum overlapping timestamp from two series
    """
    if df1_timestamps.max() < df2_timestamps.min() or df1_timestamps.min() > df2_timestamps.max():
        raise IndexError("No overlapping data. Ranges: {0} to {1}  and {2} to {3}"
                         .format(df1_timestamps.min(), df1_timestamps.max(),
                                 df2_timestamps.min(), df2_timestamps.max()), )
    return max(df1_timestamps.min(), df2_timestamps.min())


def _get_data_resolution(data_idx):
    """
    Get the frequency of data i.e. the most common time interval between timestamps. Returns a timedelta object
    """
    import warnings
    time_diff_btw_timestamps = data_idx.to_series().diff()
    most_freq_time_diff = time_diff_btw_timestamps.mode().values[0]
    minimum_time_diff = time_diff_btw_timestamps.min()
    if minimum_time_diff != most_freq_time_diff:
        warnings.warn("Frequency of input data might not be determined correctly (most frequent time "
                      "difference between adjacent timestamps"
                      " does not match minimum time difference) most frequent time difference: {0}  "
                      "minimum time difference {1}. Using most frequent time difference as resolution"
                      .format(pd.to_timedelta(most_freq_time_diff, unit='s'), minimum_time_diff))
    return pd.to_timedelta(most_freq_time_diff, unit='s')


def _round_timestamp_down_to_averaging_prd(timestamp, period):
    if period[-3:] == 'min':
        return '{year}-{month}-{day} {hour}:00:00'.format(year=timestamp.year, month=timestamp.month,
                                                          day=timestamp.day, hour=timestamp.hour)
    elif period[-1] == 'H' or period[-1] == 'D' or period[-1] == 'W':
        return '{year}-{month}-{day}'.format(year=timestamp.year, month=timestamp.month, day=timestamp.day,
                                             hour=timestamp.hour)
    elif period[-1] == 'M' or period[-2:] == 'MS':
        return '{year}-{month}'.format(year=timestamp.year, month=timestamp.month)
    elif period[-2:] == 'AS' or period[-1:] == 'A':
        return '{year}'.format(year=timestamp.year)
    else:
        print("Warning: Averaging period not identified returning default timestamps")
        return '{year}-{month}-{day} {hour}:{minute}:{second}'.format(year=timestamp.year, month=timestamp.month,
                                                                      day=timestamp.day, hour=timestamp.hour,
                                                                      minute=timestamp.minute, second=timestamp.second)


def _common_idxs(reference, site):
    """
    Finds overlapping indexes from two dataframes.
    Coverage is 1 if whole site data is covered. Also returns the number data points
    """
    common = reference.index.intersection(site.index)
    return common, len(common)


def _get_overlapping_data(df1, df2, period):
    if isinstance(period, str):
        start = _round_timestamp_down_to_averaging_prd(_get_min_overlap_timestamp(df1.index, df2.index), period)
    else:
        start = _get_min_overlap_timestamp(df1.index, df2.index)
    return df1[start:], df2[start:]


def _max_coverage_count(data_index, averaged_data_index)->pd.Series:
    """
    For a given resolution of data finds the maximum number of data points in the averaging period
    """
    max_pts = (averaged_data_index.to_series().diff().shift(-1)) / _get_data_resolution(data_index)
    max_pts[-1] = ((averaged_data_index[-1] + 1) - averaged_data_index[-1]) / _get_data_resolution(data_index)
    return max_pts


def _get_coverage_series(data, grouper_obj):
    coverage = grouper_obj.count().divide(_max_coverage_count(data.index, grouper_obj.mean().index), axis=0)
    return coverage


def average_data_by_period(data: pd.Series, period, aggregation_method='mean', filter_by_coverage_threshold=False,
                           coverage_threshold=1, return_coverage=False) -> pd.DataFrame:
    """
    Averages the data by the time period specified by period.
    Set period to 1D for a daily average, 3D for three hourly average, similarly 5D, 7D, 15D etc.
    Set period to 1H for hourly average, 3H for three hourly average and so on for 5H, 6H etc.
    Set period to 1M for monthly average
    Set period to 1AS for annual taking start of the year as the date
    For minutes use 10min, 20 min, etc.
    Can be a DateOffset object too
    """
    data = data.sort_index()
    if isinstance(period, str):
        if period[-1] == 'D':
            period = _convert_days_to_hours(period)
        if period[-1] == 'W':
            period = _convert_weeks_to_hours(period)
        if period[-1] == 'M':
            period = period+'S'
        if period[-1] == 'Y':
            raise TypeError("Please use '1AS' for annual frequency at the start of the year.")
    grouper_obj = data.resample(period, axis=0, closed='left', label='left', base=0,
                                convention='start', kind='timestamp')

    grouped_data = grouper_obj.agg(aggregation_method)
    coverage = _get_coverage_series(data, grouper_obj)

    if filter_by_coverage_threshold:
        grouped_data = grouped_data[coverage >= coverage_threshold]

    if return_coverage:
        if isinstance(coverage, pd.DataFrame):
            coverage.columns = [col_name+"_Coverage" for col_name in coverage.columns]
        elif isinstance(coverage, pd.Series):
            coverage = coverage.rename(grouped_data.name+'_Coverage')
        else:
            raise TypeError("Coverage not calculated correctly. Coverage", coverage)
        return grouped_data, coverage
    else:
        return grouped_data


def adjust_slope_offset(wspd, current_slope, current_offset, new_slope, new_offset):
    """
    Adjust a wind speed that already has a slope and offset applied with a new slope and offset.
    Can take either a single wind speed value or a pandas dataframe/series.
    :param wspd: The wind speed value or series to be adjusted.
    :type wspd: float or pd.DataFrame or pd.Series
    :param current_slope: The current slope that was applied to create the wind speed.
    :type current_slope: float
    :param current_offset: The current offset that was applied to create the wind speed.
    :type current_offset: float
    :param new_slope: The new desired slope to adjust the wind speed by.
    :type new_slope: float
    :param new_offset: The new desired offset to adjust the wind speed by.
    :type new_offset: float
    :return: The adjusted wind speed as a single value or pandas dataframe.

    The new wind speed is calculated by equating the old and new y=mx+c equations around x and then solving for
    the new wind speed.

    y2 = m2*x + c2   and   y1 = m1*x + c1

    y2 = m2*(y1 - c1)/m1 + c2

    **Example usage**
    ::
        import brightwind as bw
        df = bw.load_campbell_scientific(bw.datasets.demo_site_data)
        df['Spd80mS_adj'] = bw.adjust_slope_offset(df.Spd80mS, 0.044, 0.235, 0.04365, 0.236)
        df[['Spd80mS', 'Spd80mS_adj']]

    """
    try:
        return new_slope * ((wspd - current_offset) / current_slope) + new_offset
    except TypeError as type_error:
        for arg_value in [current_slope, current_offset, new_slope, new_offset]:
            if not utils.is_float_or_int(arg_value):
                raise TypeError("argument '" + str(arg_value) + "' is not of data type number")
        if not utils.is_float_or_int(wspd):
            if type(wspd) == pd.DataFrame and (wspd.dtypes == object)[0]:
                raise TypeError('some values in the DataFrame are not of data type number')
            elif type(wspd) == pd.Series and (wspd.dtypes == object):
                raise TypeError('some values in the Series are not of data type number')
            raise TypeError('wspd argument is not of data type number')
        raise type_error
    except Exception as error:
        raise error


def scale_wind_speed(spd, scale_factor: float) -> pd.Series:
    """
    Scales wind speed by the scale_factor
    :param spd: Series or data frame or a single value of wind speed to scale
    :param scale_factor: Scaling factor in decimal, if scaling factor is 0.8 output would be (1+0.8) times wind speed,
    if it is -0.8 the output would be (1-0.8) times the wind speed
    :return: Series or data frame with scaled wind speeds
    """
    return spd * scale_factor


def offset_wind_direction(wdir, offset: float) -> pd.Series:
    """
    Add/ subtract offset from wind direction. Keeps the ranges between 0 to 360
    :param wdir: Series or data frame or a single direction to offset
    :param offset: Offset in degrees can be negative or positive
    :return: Series or data frame with offsetted directions
    """
    if isinstance(wdir, float):
        return utils._range_0_to_360(wdir + offset)
    elif isinstance(wdir, pd.DataFrame):
        return wdir.add(offset).applymap(utils._range_0_to_360)
    else:
        return wdir.to_frame().add(offset).applymap(utils._range_0_to_360)


# def selective_avg(wspd1, wspd2, wdir, boom_dir1, boom_dir2, angular_span):

#     df = pd.Series()
#     angular_span = angular_span/2
#     boom1_lower = (boom_dir1 - angular_span +360)%360
#     boom1_higher = (boom_dir1 + angular_span +360)%360
#     boom2_lower = (boom_dir2 - angular_span+360)%360
#     boom2_higher = (boom_dir2 + angular_span +360)%360

#     for i, row in wspd1.iteritems():
#         if wdir[i] >= boom1_lower and wdir[i]<= boom1_higher:
#             if np.isnan(row) == True:
#                 df[i] = wspd2[i]
#             else:
#                 df[i] = row
#         elif wdir[i] >= boom2_lower and wdir[i]<=boom2_higher:
#             if np.isnan(wspd2[i])==True:
#                 df[i] = row
#             else:
#                 df[i] = wspd2[i]
#         else:
#             if np.isnan(row) == True:
#                 df[i] = wspd2[i]
#             elif np.isnan(wspd2[i])==True:
#                 df[i] = row
#             else:
#                 df[i] = (row +wspd2[i])/2

#     return df


# Clean_synth['Spd_120m_SelAvg'] = selective_avg(Clean_synth.Vaisala_120_avg,
#                                                Clean_synth.FirstClass_120_avg_Synthesized,
#                                                Clean_synth.FirstClass_120_dir,
#                                                boom_dir1=135, boom_dir2=315, angular_span=60)


def _preprocess_data_for_correlations(ref: pd.DataFrame, target: pd.DataFrame, averaging_prd, coverage_threshold,
                                      aggregation_method_ref='mean', aggregation_method_target='mean',
                                      get_coverage=False):
    ref_overlap, target_overlap = _get_overlapping_data(ref.sort_index().dropna(), target.sort_index().dropna(),
                                                        averaging_prd)
    from pandas.tseries.frequencies import to_offset
    ref_resolution = _get_data_resolution(ref_overlap.index)
    target_resolution = _get_data_resolution(target_overlap.index)
    if (to_offset(ref_resolution) != to_offset(averaging_prd)) and \
            (to_offset(target_resolution) != to_offset(averaging_prd)):
        if ref_resolution > target_resolution:
            target_overlap = average_data_by_period(target_overlap, to_offset(ref_resolution),
                                                    filter_by_coverage_threshold=True, coverage_threshold=1,
                                                    aggregation_method=aggregation_method_target)
        if ref_resolution < target_resolution:
            ref_overlap = average_data_by_period(ref_overlap, to_offset(target_resolution),
                                                 filter_by_coverage_threshold=True, coverage_threshold=1,
                                                 aggregation_method=aggregation_method_ref)
        common_idxs, data_pts = _common_idxs(ref_overlap, target_overlap)
        ref_overlap = ref_overlap.loc[common_idxs]
        target_overlap = target_overlap.loc[common_idxs]

    if get_coverage:
        return pd.concat([average_data_by_period(ref_overlap, averaging_prd, filter_by_coverage_threshold=False,
                                                 coverage_threshold=0, aggregation_method=aggregation_method_ref)] +
                         list(average_data_by_period(target_overlap, averaging_prd, filter_by_coverage_threshold=False,
                                                     coverage_threshold=0, aggregation_method=aggregation_method_target,
                                                     return_coverage=True)),
                         axis=1)
    else:
        ref_processed, target_processed = average_data_by_period(ref_overlap, averaging_prd,
                                                                 filter_by_coverage_threshold=True,
                                                                 coverage_threshold=coverage_threshold,
                                                                 aggregation_method=aggregation_method_ref), \
                                          average_data_by_period(target_overlap, averaging_prd,
                                                                 filter_by_coverage_threshold=True,
                                                                 coverage_threshold=coverage_threshold,
                                                                 aggregation_method=aggregation_method_target)
        concurrent_idxs, data_pts = _common_idxs(ref_processed, target_processed)
        return ref_processed.loc[concurrent_idxs], target_processed.loc[concurrent_idxs]


def _preprocess_dir_data_for_correlations(ref_spd: pd.DataFrame, ref_dir: pd.DataFrame, target_spd: pd.DataFrame,
                                          target_dir: pd.DataFrame, averaging_prd, coverage_threshold):
    ref_N, ref_E= _compute_wind_vector(ref_spd.sort_index().dropna(), ref_dir.sort_index().dropna().map(math.radians))
    target_N, target_E = _compute_wind_vector(target_spd.sort_index().dropna(),
                                              target_dir.sort_index().dropna().map(math.radians))
    ref_N_avgd, target_N_avgd = _preprocess_data_for_correlations(ref_N, target_N, averaging_prd=averaging_prd,
                                                                  coverage_threshold=coverage_threshold)
    ref_E_avgd, target_E_avgd = _preprocess_data_for_correlations(ref_E, target_E, averaging_prd=averaging_prd,
                                                                  coverage_threshold=coverage_threshold)
    ref_dir_avgd = np.arctan2(ref_E_avgd, ref_N_avgd).map(math.degrees).map(utils._range_0_to_360)
    target_dir_avgd = np.arctan2(target_E_avgd, target_N_avgd).map(math.degrees).map(utils._range_0_to_360)

    return round(ref_dir_avgd.loc[:]), round(target_dir_avgd.loc[:])
