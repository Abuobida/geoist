#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import scipy.signal as signal
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.seasonal import seasonal_decompose
from scipy.signal import detrend,butter,sosfilt,sosfiltfilt,sosfreqz,welch,\
    lombscargle,periodogram
import sys


# In[345]:


def despike(dt,th=None,fill_end=True,*args,**kwargs):
    diff_dt = dt.diff()
    if th is None:
        th = diff_dt.std()*2
    is_spike = (diff_dt-diff_dt.mean()).abs() > th
    dt[is_spike] = np.nan
    method = kwargs.get('method','linear')
    order = kwargs.get('order',1)
    res = dt.interpolate(method=method,order=order)
    if fill_end:
        res = res.fillna(method='ffill').fillna(method='bfill')
    return res,is_spike*1
def dejump(dt,th=None,fill_end=True,*args,**kwargs):
    res,is_jump = despike(dt.diff(),th,fill_end=False,*args,**kwargs)
    if fill_end:
        res.fillna(0.0)
        res.iloc[0] = dt.dropna().iloc[0]
        return res.cumsum(),is_jump
    else:
        res[~res.isna()] = res[~res.isna()].cumsum()
        return res,is_spike
def despike_v2(dt,th=None,fill_end=True,*args,**kwargs):
    despiked,is_spike = despike(dt,th,fill_end)
    dejumped,is_jump = dejump(despiked,th,fill_end)
    is_spike_jump = is_spike + is_jump
    return dejumped,is_spike_jump

def departure(data,freq='M'):
    '''Calculate departure(ju4ping2 in Chinese)

    Args:
        data (Series or 1-column DataFrame): Data to be processed
        freq (str): M==Month,D==Day

    Returns:
        DataFrame
    '''
    if freq.lower() == 'm':
        datefmt = '%m'
    elif freq.lower() == 'd':
        datefmt = '%m%d'
    else:
        raise ValueError("freq must be 'D' or 'M'!")
    if type(data) is pd.Series:
        data = pd.DataFrame({'origin_data':data})
    tmp = data.index.map(lambda x: x.strftime(datefmt))
    data['departure_mean'] = data.groupby(tmp,axis=0).transform(lambda x: x.mean())
    data['departure'] = data.iloc[:,0] - data['departure_mean']
    return data

def print_adf(res,data_name,file=sys.stdout):
    print('Augmented Dickey–Fuller test for {}:'.format(data_name),file=file)
    print(' ' * 2 + 'adf: {}'.format(res[0]),file=file)
    print(' ' * 2 + 'p-value: {}'.format(res[1]),file=file)
    print(' ' * 2 + 'norder: {}'.format(res[2]),file=file)
    print(' ' * 2 + 'number of points: {}'.format(res[3]),file=file)
    print(' ' * 2 + 'critical values:',file=file)
    for key,value in res[4].items():
        print(' '*4 + '{} : {}'.format(key,value),file=file)

