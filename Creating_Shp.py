#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  8 10:47:19 2017

@author: Yu-Hsuan Tu
"""
import os
from osgeo import ogr, osr
import Retrieve_Metadata
from Retrieve_Metadata import PathImage
import Metadata_Interpreter

Metadata = Retrieve_Metadata.RetrieveData(PathImage, 'GPSPosition', 'GPSAltitude')
PositionAltList = {}
for file, meta in Metadata.items():
    #Get Position in decimal latitude, longitude
    Lon, Lat = Metadata_Interpreter.GetLonLat(meta)
    Alt = Metadata_Interpreter.GetAltitude(meta)
        
    PositionAltList[file] = [Lon, Lat, Alt]

keys = sorted(PositionAltList.keys())

# set up the shapefile driver
driver = ogr.GetDriverByName('ESRI Shapefile')

# create the data source
path, file = os.path.split(PathImage)
Waypoints = driver.CreateDataSource(os.path.join(path, 'waypoints.shp'))
Trajectory = driver.CreateDataSource(os.path.join(path, 'trajectory.shp'))

# create the spatial reference, WGS84
wgs84 = osr.SpatialReference()
wgs84.ImportFromEPSG(4326)

# create layer
PtLayer = Waypoints.CreateLayer('waypoints.shp', geom_type=ogr.wkbPoint ,srs=wgs84)
TjyLayer = Trajectory.CreateLayer('trajectory.shp', geom_type=ogr.wkbLineString, srs=wgs84)
FieldList = {'File':ogr.OFTString, 'Longitude':ogr.OFTReal, 'Latitude':ogr.OFTReal, 'Altitude':ogr.OFTReal}
for field, fieldtype in FieldList.items():
    Fields = ogr.FieldDefn(field, fieldtype)
    PtLayer.CreateField(Fields)

# Create geometry, features and set value
line = ogr.Geometry(ogr.wkbLineString)

WpfeatureDefn = PtLayer.GetLayerDefn()
LinefeatureDefn = TjyLayer.GetLayerDefn()
for key in keys:
    point = ogr.Geometry(ogr.wkbPoint)
    point.AddPoint(PositionAltList[key][0], PositionAltList[key][1])
    line.AddPoint(PositionAltList[key][0], PositionAltList[key][1])
    PtFeature = ogr.Feature(WpfeatureDefn)
    PtFeature.SetGeometry(point)
    PtFeature.SetField('File', key)
    PtFeature.SetField('Longitude', PositionAltList[key][0])
    PtFeature.SetField('Latitude', PositionAltList[key][1])
    PtFeature.SetField('Altitude', PositionAltList[key][2])
    PtLayer.CreateFeature(PtFeature)
LineFeature = ogr.Feature(LinefeatureDefn)
LineFeature.SetGeometry(line)
TjyLayer.CreateFeature(LineFeature)

PtFeature = None
LineFeature = None
Waypoints = None
Trajectory = None