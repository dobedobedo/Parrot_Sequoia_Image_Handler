#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul  4 18:08:04 2017

@author: Yu-Hsuan Tu
"""
import os
import tkinter as tk
from tkinter.filedialog import askopenfilename
import numpy as np
import gdal
from osgeo import gdal_array
import Retrieve_Metadata
from Retrieve_Metadata import PathImage
import Metadata_Interpreter

def Image_Math(Fullfilename, IrradianceRatio):
    path, filename = os.path.split(Fullfilename)
    outpath = os.path.join(path, 'Calibrated')
    if not os.path.exists(outpath):
        os.makedirs(outpath)
    InputFile = gdal.Open(Fullfilename)
    cols = InputFile.RasterXSize
    rows = InputFile.RasterYSize
    channel = InputFile.RasterCount
    GeoTransform = InputFile.GetGeoTransform()
    Projection = InputFile.GetProjection()
    driver = InputFile.GetDriver()
    bands = []
    for band in range(channel):
        bands.append(InputFile.GetRasterBand(band+1))
    ndv = bands[band].GetNoDataValue()
    image = np.zeros((rows,cols), dtype=InputFile.ReadAsArray().dtype)
    
    for band in range(channel):
        image = bands[band].ReadAsArray(0,0,cols,rows)
        
        # Note: we keep the output and input image as the same type to avoid potential problem
        outimage = ((image * IrradianceRatio).round()).astype(image.dtype)
        OutFile = os.path.join(outpath,filename)
        if os.path.exists(OutFile):
            os.remove(OutFile)
        Type = gdal_array.NumericTypeCodeToGDALTypeCode(outimage.dtype.type)
        OutImage = driver.Create(OutFile, 
                                     outimage.shape[1], outimage.shape[0], channel, Type)
        OutImage.GetRasterBand(band+1).WriteArray(outimage[:,:])
        if ndv is not None:
            OutImage.GetRasterBand(band+1).SetNoDataValue(ndv)
    
    OutImage.SetGeoTransform(GeoTransform)
    OutImage.SetProjection(Projection)
    OutImage = None
    InputFile = None
    os.system("exiftool -tagsFromFile \"{Src}\" -all:all "
              "-tagsFromFile \"{Src}\" -xmp:all \"{Dst}\" && "
              "exiftool -delete_original! \"{Dst}\"".format(
                        Src=Fullfilename, 
                        Dst=OutFile))

Metadata = Retrieve_Metadata.RetrieveData(PathImage, 'SubSecCreateDate', 'IrradianceList')

gdal.AllRegister()
tk.Tk().withdraw()
path, SelectFile = os.path.split(askopenfilename(title='Select a reference image. Bands doesn\'t matter.'))
ReferenceFile = os.path.splitext(SelectFile)[0][0:-3]

IrradianceRefGRE = Metadata_Interpreter.GetSunIrradiance(Metadata[ReferenceFile+'GRE.TIF'])
IrradianceRefRED = Metadata_Interpreter.GetSunIrradiance(Metadata[ReferenceFile+'RED.TIF'])
IrradianceRefREG = Metadata_Interpreter.GetSunIrradiance(Metadata[ReferenceFile+'REG.TIF'])
IrradianceRefNIR = Metadata_Interpreter.GetSunIrradiance(Metadata[ReferenceFile+'NIR.TIF'])

files = sorted(Metadata.keys())

if SelectFile in files:
    for file in files:
        Irradiance = Metadata_Interpreter.GetSunIrradiance(Metadata[file])
        if 'GRE' in file:
            Image_Math(os.path.join(path, file), Irradiance/IrradianceRefGRE)
        elif 'RED' in file:
            Image_Math(os.path.join(path, file), Irradiance/IrradianceRefRED)
        elif 'REG' in file:
            Image_Math(os.path.join(path, file), Irradiance/IrradianceRefREG)
        elif 'NIR' in file:
            Image_Math(os.path.join(path, file), Irradiance/IrradianceRefNIR)
        
        
