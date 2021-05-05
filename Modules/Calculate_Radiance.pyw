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
import math
from osgeo import gdal
from osgeo import gdal_array
from Dependency import Retrieve_Metadata
from Dependency import Metadata_Interpreter
from Dependency import Image_masking

def Image_Math(Fullfilename, SensorModel, ExposureTime, ISO, FNumber, K):
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
        
    for band in range(channel):
        image = bands[band].ReadAsArray(0,0,cols,rows)
                
        if K == 1:
            scalar = 100
        else:
            scalar = 10000
        # Calibrate to reflectance without using sunshine measurement.
        # This calculation assumes the irradiance level is equivalent across all images
        # A scalar is applied to make 100% equivalent to 10000 DN.
        outimage = (scalar * K * math.pow(FNumber, 2) * (image-SensorModel[1]) / (
                    SensorModel[0]*ExposureTime*ISO+SensorModel[2])).round()
        
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
        
if __name__ == '__main__':
    PathImage = Retrieve_Metadata.OpenDirectory()
    Metadata = Retrieve_Metadata.RetrieveData(PathImage, 'SensorModel', 'ExposureTime', 'ISO', 'FNumber', 'BandName')
    
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
        except AttributeError:
            continue
        
    for file in files:
        SensorModel = Metadata_Interpreter.GetSensorModelCoef(Metadata[file])
        ExposureTime = Metadata_Interpreter.GetExposureTime(Metadata[file])
        ISO = Metadata_Interpreter.GetISO(Metadata[file])
        FNumber = Metadata_Interpreter.GetFNumber(Metadata[file])
        BandName = Metadata[file]['BandName']
        Image_Math(os.path.join(path, file), SensorModel, ExposureTime, ISO, FNumber, K_list[BandName])
        
    Retrieve_Metadata.ShowMessage('Done', 'Finish processing image')
    
