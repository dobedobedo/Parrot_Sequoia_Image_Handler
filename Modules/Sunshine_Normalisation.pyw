#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul  4 18:08:04 2017

@author: Yu-Hsuan Tu

This module uses Sequoia's sunshine irradiance to adjust photo's brightness.
Usage:
Select a folder containing all the photos.
The program will use the image which has minimum sunshine irradiance as reference,
and manipulate the other photos based on the sunshine irradiance ratio to the reference image
"""
import os
import subprocess
import numpy as np
import gdal
from osgeo import gdal_array
import Retrieve_Metadata
from Retrieve_Metadata import PathImage
import Metadata_Interpreter

def Image_Math(Fullfilename, IrradianceRatio):
    path, filename = os.path.split(Fullfilename)
    outpath = os.path.join(path, 'SunNormalised')
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
        
        outimage = (image / IrradianceRatio).round()
        
        # Limite the DN within data type range
        np.clip(outimage, np.iinfo(image.dtype).min, np.iinfo(image.dtype).max, outimage)
        
        # Note: we keep the output and input image as the same type to avoid potential problem
        outimage = outimage.astype(image.dtype)
            
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
    subprocess.run(['exiftool', '-tagsFromFile', Fullfilename, '-ALL', '-XMP', OutFile])
    subprocess.run(['exiftool', '-delete_original!', OutFile])

Metadata = Retrieve_Metadata.RetrieveData(PathImage, 'SubSecCreateDate', 'IrradianceList')

gdal.AllRegister()

files = sorted(Metadata.keys())
IrradianceList = []
for file in files:
    IrradianceList.append(Metadata_Interpreter.GetSunIrradiance(Metadata[file]))
    
# Use the file which has minimum irradiance as reference to reduce chance of over-exposured
SelectFile = files[IrradianceList.index(min(IrradianceList))]
ReferenceFile = os.path.splitext(SelectFile)[0][0:-3]
RefNumber = 'Ref_' + ReferenceFile.split('_')[-2]

IrradianceRefGRE = Metadata_Interpreter.GetSunIrradiance(Metadata[ReferenceFile+'GRE.TIF'])
IrradianceRefRED = Metadata_Interpreter.GetSunIrradiance(Metadata[ReferenceFile+'RED.TIF'])
IrradianceRefREG = Metadata_Interpreter.GetSunIrradiance(Metadata[ReferenceFile+'REG.TIF'])
IrradianceRefNIR = Metadata_Interpreter.GetSunIrradiance(Metadata[ReferenceFile+'NIR.TIF'])

path = os.path.split(PathImage)[0]

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
with open(os.path.join(path, RefNumber), 'a'):
    os.utime(os.path.join(path, RefNumber), None)
        
