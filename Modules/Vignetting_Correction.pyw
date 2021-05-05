# -*- coding: utf-8 -*-
"""
Created on Mon Sep  3 11:46:11 2018

@author: Yu-Hsuan Tu

This module use the equation from Parrot developer manual SEQ-AN-02 to
calculate vignetting polynomial and correct vignetting effect.
Do not use with the colour correction feature together in image pre-processing
software packages (e.g. Pix4DMapper, Agisoft PhotoScan)
"""

import os
import subprocess
import numpy as np
from osgeo import gdal
from osgeo import gdal_array
from Dependency import Retrieve_Metadata
from Dependency import Metadata_Interpreter

def Image_Math(Fullfilename, PowerCoefs):
    path, filename = os.path.split(Fullfilename)
    outpath = os.path.join(path, 'Vig_corrected')
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
    Vig_Array = VignettingArray(PowerCoefs, rows, cols)
    
    for band in range(channel):
        image = bands[band].ReadAsArray(0,0,cols,rows)
        
        # Correct vignetting effect
        outimage = (image / Vig_Array).round()
        
        # Limite the DN within data type range
        np.clip(outimage, np.iinfo(image.dtype).min, np.iinfo(image.dtype).max, outimage)
        
        # Save the output image to the same format as input
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

def VignettingArray(PowerCoefs, rows, cols):
    Vig_Array = np.ones((rows, cols))
    PowerArray = np.array(PowerCoefs)
    for y, x in [(y, x) for y in range(rows) for x in range(cols)]:
        Vig_Array[y, x] = (
                PowerArray[:, 2] * np.power(x/cols, PowerArray[:, 0]) * np.power(y/rows, PowerArray[:, 1])
                ).sum()
    return Vig_Array

if __name__ == '__main__':
    PathImage = Retrieve_Metadata.OpenDirectory()
    Metadata = Retrieve_Metadata.RetrieveData(PathImage, 'VignettingPolynomial2DName', 'VignettingPolynomial2D')
    gdal.AllRegister()
    
    files = sorted(Metadata.keys())
    path = os.path.split(PathImage)[0]
    for file in files:
        PowerCoefs = Metadata_Interpreter.GetPowerCoefficients(Metadata[file])
        Image_Math(os.path.join(path, file), PowerCoefs)
        
    Retrieve_Metadata.ShowMessage('Done', 'Finish processing image')
