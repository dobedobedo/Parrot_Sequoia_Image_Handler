#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 23 16:08:19 2017

@author: Yu-Hsuan Tu
"""
import math
import numpy as np
import urllib.request
import json
import base64
import struct
import datetime
import pytz

def GetLonLat(Metadata):
    Position = Metadata['GPSPosition'].split(',')
    Latitude = Position[0].split()
    Lat = eval(Latitude[0]) + \
          eval(Latitude[2].strip("'"))/60.0 + \
          eval(Latitude[3].strip('"'))/3600.0
    if Latitude[4] == 'S':
        Lat = math.copysign(Lat,-1)
    else:
        Lat = math.copysign(Lat,1)

    Longitude = Position[1].split()
    Lon = eval(Longitude[0]) + \
          eval(Longitude[2].strip("'"))/60.0 + \
          eval(Longitude[3].strip('"'))/3600.0
    if Longitude[4] == 'W':
        Lon = math.copysign(Lon,-1)
    else:
        Lon = math.copysign(Lon,1)
        
    return Lon, Lat

def GetAltitude(Metadata):
    return eval(Metadata['GPSAltitude'].split()[0])

def GetTime(Metadata):
    Time = datetime.datetime.strptime(Metadata['SubSecDateTimeOriginal'], "%Y:%m:%d %H:%M:%S.%f")
    Time_UTC = pytz.utc.localize(Time, is_dst=False)
    return Time_UTC
    
def GetGPSTime(Metadata):
    Time = datetime.datetime.strptime(Metadata['GPSTimeStamp'], "%H:%M:%S.%f")
    Time_UTC = pytz.utc.localize(Time, is_dst=False)
    return Time_UTC.time()

def GetTimefromStart(Metadata):
    Time = datetime.datetime.strptime(Metadata['SubSecCreateDate'], "%Y:%m:%d %H:%M:%S.%f")
    Time_UTC = pytz.utc.localize(Time, is_dst=False)
    duration = datetime.timedelta(hours = Time_UTC.hour, 
                                  minutes = Time_UTC.minute, 
                                  seconds = Time_UTC.second, 
                                  microseconds = Time_UTC.microsecond)
    return duration

def GetTimeOffset(Metadata):
    GPSTime = GetGPSTime(Metadata)
    ImageTime = GetTime(Metadata).time()
    offset = datetime.timedelta(hours = GPSTime.hour - ImageTime.hour, 
                                minutes = GPSTime.minute - ImageTime.minute, 
                                seconds = GPSTime.second - ImageTime.second, 
                                microseconds = GPSTime.microsecond - ImageTime.microsecond)
    return offset

def GetPrincipalPoint(Metadata, sensor_size):
    cx, cy = eval(Metadata['PrincipalPoint'].split(',').strip())
    w = eval(Metadata['ImageWidth'])
    h = eval(Metadata['ImageHeight'])
    
    # Note that Sequoia's origin is at lower left instead of top left
    CP = np.array([[w*cx/sensor_size[0]],[h*(cy/sensor_size[1])]])
    return CP

def GetFisheyeAffineMatrix(Metadata):
    CDEF = eval(Metadata['FisheyeAffineMatrix'].split(','))
    FisheyeAffineMatrix = np.array([[CDEF[0], CDEF[1]],[CDEF[2],CDEF[3]]])
    return FisheyeAffineMatrix

def GetFisheyePolynomial(Metadata):
    return eval(Metadata['FisheyePolynomial'].split(','))

def GetElevation(Metadata):
    Lon, Lat = GetLonLat(Metadata)
    
    # Retrieve Elevation from Google Map API
    # Note: 2500 querry per day for free users
    Elevation_Base_URL = 'http://maps.googleapis.com/maps/api/elevation/json?'
    URL_Params = 'locations={Lat},{Lon}&sensor={Bool}'.format(Lat=Lat, Lon=Lon, Bool='false')
    url = Elevation_Base_URL + URL_Params
    with urllib.request.urlopen(url) as f:
        response = json.loads(f.read().decode())
        result = response['results'][0]
        elevation = result['elevation']
    return elevation
    
def GetSunIrradiance(Metadata):
    encoded = Metadata['IrradianceList']
    # decode the string
    data = base64.standard_b64decode(encoded)
    
    # ensure that there's enough data QHHHfff
    assert len(data) % 28 == 0
    
    # determine how many datasets there are
    count = len(data) // 28
    
    # unpack the data as uint64, uint16, uint16, uint16, uint16, float, float, float
    result = []
    for i in range(count):
        index = 28 * i
        s = struct.unpack('<QHHHHfff', data[index:index + 28])
        result.append(s)
    CreateTime = GetTimefromStart(Metadata)
    timestamp = []
    for measurement in result:
        q, r = divmod(measurement[0], 1000000)
        timestamp.append(abs(datetime.timedelta(seconds=q, microseconds=r)-CreateTime))
    TargetIndex = timestamp.index(min(timestamp))
    count = result[TargetIndex][1]
    gain = result[TargetIndex][3]
    exposuretime = result[TargetIndex][4]
    Irradiance = count / (gain * exposuretime)
    return Irradiance
    
