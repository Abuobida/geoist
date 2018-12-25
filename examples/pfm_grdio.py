# -*- coding: utf-8 -*-
"""
Created on Thu Nov 15 10:03:33 2018
测试对网格数据对象的操作
@author: chens
"""    
import numpy as np
import matplotlib.pyplot as plt
from geoist.pfm import grdio
from geoist.pfm import pftrans

grd1=grdio.grddata()
grd1.load_surfer(r'D:\demo\demogrid.grd')
if np.ma.is_masked(grd1.data):
   grd1.fill_nulls()
   plt.imshow(grd1.data0)
else:
   print('not null region in dataset')
   plt.imshow(grd1.data)

shape = (grd1.rows, grd1.cols) 
height = 0.5
x, y, gz = grd1.grd2xyz()
gzcontf = pftrans.upcontinue(x, y, gz, shape, height)
gz2d = gzcontf.reshape(grd1.rows, grd1.cols)
grd1.data = np.ma.masked_equal(gz2d, grd1.nullvalue)
grd1.export_surfer(r'D:\demo\demogrid-up1000.grd') 
#grd1.data=d1*d1
#v = d1.reshape(grd1.rows*grd1.cols)
# #gridder.interpolation.fill_nans(x, y, v, xp, yp, vp):
# plt.imshow(grd1.data)     #显示绘图结果
#grd1.export_surfer(r'D:\demo\demogrid3-blk.grd', flag = False)
#np.ma.getdata(gz)
 

