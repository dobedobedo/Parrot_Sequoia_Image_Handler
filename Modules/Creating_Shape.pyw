#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  8 10:47:19 2017

@author: Yu-Hsuan Tu

This module uses photo's geotag to create waypoints and trajectory shapefile
"""
import os
from osgeo import ogr, osr
from Dependency import Retrieve_Metadata
from Dependency import Metadata_Interpreter

if __name__ == '__main__':
    PathImage = Retrieve_Metadata.OpenDirectory()
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
    kmldriver = ogr.GetDriverByName('KML')
    
    # create the data source
    path, file = os.path.split(PathImage)
    Waypoints = driver.CreateDataSource(os.path.join(path, 'waypoints.shp'))
    Waypoints_kml = kmldriver.CreateDataSource(os.path.join(path, 'waypoints.kml'))
    
    Trajectory = driver.CreateDataSource(os.path.join(path, 'trajectory.shp'))
    
    # create the spatial reference, WGS84
    wgs84 = osr.SpatialReference()
    wgs84.ImportFromEPSG(4326)
    
    # create layer
    PtLayer = Waypoints.CreateLayer('waypoints.shp', geom_type=ogr.wkbPoint ,srs=wgs84)
    PtLayer_kml = Waypoints_kml.CreateLayer('waypoints.kml', geom_type=ogr.wkbPoint ,srs=wgs84)
    TjyLayer = Trajectory.CreateLayer('trajectory.shp', geom_type=ogr.wkbLineString, srs=wgs84)
    FieldList = {'File':ogr.OFTString, 'Longitude':ogr.OFTReal, 'Latitude':ogr.OFTReal, 'Altitude':ogr.OFTReal}
    for field, fieldtype in FieldList.items():
        Fields = ogr.FieldDefn(field, fieldtype)
        PtLayer.CreateField(Fields)
    
    # Create geometry, features and set value
    line = ogr.Geometry(ogr.wkbLineString)
    
    WpfeatureDefn = PtLayer.GetLayerDefn()
    WpfeatureDefn_kml = PtLayer_kml.GetLayerDefn()
    LinefeatureDefn = TjyLayer.GetLayerDefn()
    for key in keys:
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(PositionAltList[key][0], PositionAltList[key][1], PositionAltList[key][2])
        line.AddPoint(PositionAltList[key][0], PositionAltList[key][1], PositionAltList[key][2])
        PtFeature = ogr.Feature(WpfeatureDefn)
        PtFeature.SetGeometry(point)
        PtFeature.SetField('File', key)
        PtFeature.SetField('Longitude', PositionAltList[key][0])
        PtFeature.SetField('Latitude', PositionAltList[key][1])
        PtFeature.SetField('Altitude', PositionAltList[key][2])
        PtLayer.CreateFeature(PtFeature)
        PtFeature_kml = ogr.Feature(WpfeatureDefn_kml)
        PtFeature_kml.SetGeometry(point)
        PtFeature_kml.SetField('Name', key)
        PtLayer_kml.CreateFeature(PtFeature_kml)
    LineFeature = ogr.Feature(LinefeatureDefn)
    LineFeature.SetGeometry(line)
    TjyLayer.CreateFeature(LineFeature)
    
    PtFeature = None
    PtFeature_kml = None
    LineFeature = None
    PtLayer = None
    PtLayer_kml = None
    LTrjLayer = None
    Waypoints = None
    Waypoints_kml = None
    Trajectory = None
    
    Retrieve_Metadata.ShowMessage('Done', 'Finish processing image')
