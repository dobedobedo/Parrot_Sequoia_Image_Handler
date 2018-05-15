#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 14 14:39:56 2018

@author: Yu-Hsuan Tu

This module use the equation from Parrot developer manual SEQ-AN-01 to calculate arbitrary radiance.
When executed, it will prompt the user to select the folder containing all images, 
then ask for the reference image for each band to solve the arbitrary.
The reference image must contains a Lambertian reflectance panel.
Cancel the file dialog to skip solving arbitrary.
"""

import os
import subprocess
import numpy as np
import gdal
import math
from osgeo import gdal_array
from Dependency import Retrieve_Metadata
from Dependency import Metadata_Interpreter
from Dependency import Image_masking

def Image_Math(Fullfilename, PowerCoefs, SensorModel, ExposureTime, ISO, FNumber, K):
    path, filename = os.path.split(Fullfilename)
    outpath = os.path.join(path, 'Radiance')
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
        Vig_corr_image = (image / Vig_Array).round()
        
        # Calibrate to reflectance without using sunshine measurement.
        # This calculation assumes the irradiance level is equivalent across all images
        outimage = K * math.pow(FNumber, 2) * (Vig_corr_image-SensorModel[1]) / (
                SensorModel[0]*ExposureTime*ISO+SensorModel[2])
        
        # Limite the DN within data type range
        np.clip(outimage, np.finfo(outimage.dtype).min, np.finfo(outimage.dtype).max, outimage)
        
        # Reduce the float precision to 32-bit
        outimage = outimage.astype(np.float32)
            
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
    Metadata = Retrieve_Metadata.RetrieveData(PathImage, 'VignettingPolynomial2DName', 'VignettingPolynomial2D',
                                              'SensorModel', 'ExposureTime', 'ISO', 'FNumber', 'BandName')
    
    gdal.AllRegister()
    
    files = sorted(Metadata.keys())
    bands = set()
    for file in files:
        bands.add(Metadata[file]['BandName'])
    path = os.path.split(PathImage)[0]
    
    K_list = dict()
    for band in bands:
        K_list[band] = 1
        try:
            DN, ref_factor, reference_image = Image_masking.main(band)
            file = os.path.split(reference_image)[1]
            ref_Metadata = Retrieve_Metadata.RetrieveData(reference_image, 
                                                          'SensorModel', 'ExposureTime', 'ISO', 'FNumber', 'BandName')
            Coefs = Metadata_Interpreter.GetSensorModelCoef(ref_Metadata[file])
            ref_Exp = Metadata_Interpreter.GetExposureTime(ref_Metadata[file])
            ref_ISO = Metadata_Interpreter.GetISO(ref_Metadata[file])
            ref_f = Metadata_Interpreter.GetFNumber(ref_Metadata[file])
            K = ref_factor/ (math.pow(ref_f, 2) * ((DN-Coefs[1])/(Coefs[0]*ref_Exp*ref_ISO+Coefs[2])))
            K_list[band] = K
        except TypeError:
            continue
        
    for file in files:
        PowerCoefs = Metadata_Interpreter.GetPowerCoefficients(Metadata[file])
        SensorModel = Metadata_Interpreter.GetSensorModelCoef(Metadata[file])
        ExposureTime = Metadata_Interpreter.GetExposureTime(Metadata[file])
        ISO = Metadata_Interpreter.GetISO(Metadata[file])
        FNumber = Metadata_Interpreter.GetFNumber(Metadata[file])
        BandName = Metadata[file]['BandName']
        Image_Math(os.path.join(path, file), PowerCoefs, SensorModel, ExposureTime, ISO, FNumber, K_list[BandName])
        
    Retrieve_Metadata.ShowMessage('Done', 'Finish processing image')
    