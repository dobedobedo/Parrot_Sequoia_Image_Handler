#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 14 17:09:32 2018

@author: uqytu1
"""

#!/usr/bin/env python3

# -*- coding: utf-8 -*-
"""
The mosaic has actually nodata value at 0.
However, due to some technical issue, it is set to some other value automatically.
Therefore, the nodata value is set manually here.
0 for mosaic
-10000 for reflectnace image
you can change the extraction method by uncomment the ndv sourcecode.
"""

import os
import numpy as np
import numpy.ma as ma
import cv2
from osgeo import gdal
import tkinter as tk
from tkinter.filedialog import askopenfilename
from tkinter import messagebox
from . import Retrieve_Metadata

drawing = False
mode = True
roi_corners = []
ix, iy = -1, -1
mean_DN = []
reflectance = []
brightness = 1.0

#Read image using GDAL to avoid unusual bands problem by opencv
def Read_Image(filename):
    InputFile = gdal.Open(filename)
    cols = InputFile.RasterXSize
    rows = InputFile.RasterYSize
    channel = InputFile.RasterCount
    GeoTransform = InputFile.GetGeoTransform()
    Projection = InputFile.GetProjection()
    driver = InputFile.GetDriver()
    bands = []
    for band in range(channel):
        bands.append(InputFile.GetRasterBand(band+1))
    #ndv = bands[band].GetNoDataValue() #Get nodata automatically
    ndv = 0   #Set nodata manually to 0, which is the usual situation
    if channel <= 2:
        image = np.zeros((rows,cols), dtype=InputFile.ReadAsArray().dtype)
    else:
        image = np.zeros((rows,cols,channel), dtype=InputFile.ReadAsArray().dtype)
    
    for band in range(channel):
        if channel == 1:
            image = bands[band].ReadAsArray(0,0,cols,rows)
            alpha = None
        elif channel == 2:
            if band != channel-1:
                image = bands[band].ReadAsArray(0,0,cols,rows)
            else:
                alpha = bands[band].ReadAsArray(0,0,cols,rows)
        elif channel == 4:
            if band != channel-1:
                image[:,:,band] = bands[band].ReadAsArray(0,0,cols,rows)
            else:
                alpha = bands[band].ReadAsArray(0,0,cols,rows)
        else:
            image[:,:,band] = bands[band].ReadAsArray(0,0,cols,rows)
            alpha = None
    InputFile = None    
    return image, ndv, alpha, GeoTransform, Projection, driver

#draw polygon or zoom by rectangle depend on the switch trackbar
def draw_polygon(event,x,y,flags,param):
    global drawing, mode, roi_corners, ix, iy, temp, temp_zoom, mean_DN, reflectance, brightness, image_used
            
    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        if mode == True:
            if len(roi_corners) == 0:
                roi_corners = [(x,y)]
                temp_zoom = temp.copy()
            else:
                roi_corners.append((x,y))
        else:
            ix, iy = x, y

    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing == True:
            draw_image = temp.copy()
            if mode == True:
                cv2.line(draw_image, roi_corners[-1], (x,y), (0,160,0), 1)
                cv2.imshow("Original", (np.clip(draw_image*brightness, 
                                                np.iinfo(temp.dtype).min, 
                                                np.iinfo(temp.dtype).max)).astype(temp.dtype))
            else:
                cv2.rectangle(draw_image, (ix,iy), (x,y), (0,0,160), -1)
                cv2.addWeighted(draw_image, 0.4, temp, 0.6, 0, draw_image)
                cv2.imshow("Original", (np.clip(draw_image*brightness, 
                                                np.iinfo(temp.dtype).min, 
                                                np.iinfo(temp.dtype).max)).astype(temp.dtype))

    elif event == cv2.EVENT_LBUTTONUP:
        if mode == True:
            if len(roi_corners) > 1:
                if len(roi_corners) >= 3:
                    for pt in range(1,len(roi_corners)-1):
                        error_code = line_check(
                                    roi_corners[pt-1], roi_corners[pt]
                                    , roi_corners[-2], roi_corners[-1])
                        if error_code == 1:
                            drawing = False
                            temp = temp_zoom.copy()
                            cv2.imshow("Original", (np.clip(temp*brightness, 
                                                            np.iinfo(temp.dtype).min, 
                                                            np.iinfo(temp.dtype).max)).astype(temp.dtype))
                            roi_corners = []
                            messagebox.showinfo("Warning",
                                        "Polygon cannot be self-intersected!")
                            break
                        elif error_code == 2:
                            drawing = False
                            temp = temp_zoom.copy()
                            cv2.imshow("Original", (np.clip(temp*brightness, 
                                                            np.iinfo(temp.dtype).min, 
                                                            np.iinfo(temp.dtype).max)).astype(temp.dtype))
                            roi_corners = []
                            messagebox.showinfo("Warning",
                                        "Duplicated edges!")
                            break
                    if error_code == 0:
                        cv2.line(temp, roi_corners[-2], 
                                 roi_corners[-1], (0,160,0), 1)
                        cv2.imshow("Original", (np.clip(temp*brightness, 
                                                        np.iinfo(temp.dtype).min, 
                                                        np.iinfo(temp.dtype).max)).astype(temp.dtype))
                else:
                    cv2.line(temp, roi_corners[-2], 
                             roi_corners[-1], (0,160,0), 1)
                    cv2.imshow("Original", (np.clip(temp*brightness, 
                                                    np.iinfo(temp.dtype).min, 
                                                    np.iinfo(temp.dtype).max)).astype(temp.dtype))
        else:
            rect = (min(ix,x),min(iy,y),abs(ix-x),abs(iy-y))
            x1, y1, w, h = rect
            if w != 0 and h != 0:
                temp = temp[y1:y1+h, x1:x1+w]
                temp_zoom = temp.copy()
            cv2.imshow("Original", (np.clip(temp*brightness, 
                                            np.iinfo(temp.dtype).min, 
                                            np.iinfo(temp.dtype).max)).astype(temp.dtype))
            drawing = False

    elif event == cv2.EVENT_RBUTTONDOWN:
        if mode == True:
            drawing = False
            if len(roi_corners) < 3:
                messagebox.showinfo("Warning",
                                    "You need at least 3 points to form a polygon!")
                temp = temp_zoom.copy()
                cv2.imshow("Original", (np.clip(temp*brightness, 
                                                np.iinfo(temp.dtype).min, 
                                                np.iinfo(temp.dtype).max)).astype(temp.dtype))
                roi_corners = []
            else:
                roi_corners.append(roi_corners[0])
                for pt in range(2,len(roi_corners)-1):
                    error_code = line_check(
                            roi_corners[pt-1], roi_corners[pt]
                            , roi_corners[-2], roi_corners[-1])
                    if error_code == 1:
                        temp = temp_zoom.copy()
                        cv2.imshow("Original", (np.clip(temp*brightness, 
                                                        np.iinfo(temp.dtype).min, 
                                                        np.iinfo(temp.dtype).max)).astype(temp.dtype))
                        roi_corners = []
                        messagebox.showinfo("Warning",
                                    "Polygon cannot be self-intersected!")
                        break
                    elif error_code == 2:
                        temp = temp_zoom.copy()
                        cv2.imshow("Original", (np.clip(temp*brightness, 
                                                        np.iinfo(temp.dtype).min, 
                                                        np.iinfo(temp.dtype).max)).astype(temp.dtype))
                        roi_corners = []
                        messagebox.showinfo("Warning",
                                    "Duplicated edges!")
                        break
                if error_code == 0:
                    cv2.line(temp, roi_corners[-2], roi_corners[-1], (0,160,0), 1)
                    cv2.imshow("Original", (np.clip(temp*brightness, 
                                                    np.iinfo(temp.dtype).min, 
                                                    np.iinfo(temp.dtype).max)).astype(temp.dtype))
                    temp = temp_zoom.copy()
                    mask = create_mask(temp.shape, roi_corners, temp.dtype)
                    masked_image = cv2.bitwise_and(temp, mask)
                    mean_DN.append(ma.array(temp, mask=np.invert(mask)).mean())
                    reflectance.append(Ref_inputBox())
                    WindowName = "DN:{}, reflectance:{}".format(int(mean_DN[-1]), reflectance[-1])
                    cv2.namedWindow(WindowName, cv2.WINDOW_NORMAL)
                    cv2.imshow(WindowName, masked_image)
                    roi_corners = []
        else:
            temp = image_used.copy()
            temp_zoom = temp.copy()
            cv2.imshow("Original", (np.clip(temp*brightness, 
                                            np.iinfo(temp.dtype).min, 
                                            np.iinfo(temp.dtype).max)).astype(temp.dtype))

def create_mask(shape, roi_corners, img_type):
    mask = np.zeros(shape, dtype=img_type)
    fill_value = np.iinfo(img_type).max
    roi = np.array([roi_corners], dtype=np.int32)
    
    if len(shape) < 3:
        ignore_mask_colour = (fill_value,)
    else:
        ignore_mask_colour = (fill_value,)*shape[-1]
    
    cv2.fillPoly(mask, roi, ignore_mask_colour)
    return mask

def mode_switch(x):
    global mode, roi_corners, drawing, brightness
    drawing = False
    temp = temp_zoom.copy()
    cv2.imshow("Original", (np.clip(temp*brightness, 
                                    np.iinfo(temp.dtype).min, 
                                    np.iinfo(temp.dtype).max)).astype(temp.dtype))
    if x == 0:
        mode = True
    else:
        mode = False
    roi_corners = []

def adjust_brightness(x):
    global brightness
    brightness = x/100.0
    cv2.imshow("Original", (np.clip(temp*brightness, 
                                    np.iinfo(temp.dtype).min, 
                                    np.iinfo(temp.dtype).max)).astype(temp.dtype))

def line_check(pt1, pt2, pt3, pt4):
    error_code = 0
    line1 = [pt1, pt2]
    line2 = [pt3, pt4]
    xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
    ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

    #calculate line intersection using Cramer's rule
    def det(a,b):
        return a[0]*b[1] - a[1]*b[0]
    div = det(xdiff, ydiff)
    d = (det(*line1), det(*line2))
    try:
        x = det(d, xdiff)/div
        y = det(d, ydiff)/div
        #check whether the intersections are within segments
        if not ((x < max(min(pt1[0], pt2[0]), min(pt3[0], pt4[0])) or
            x > min(max(pt1[0], pt2[0]), max(pt3[0], pt4[0]))) and 
            (y < max(min(pt1[1], pt2[1]), min(pt3[1], pt4[1])) or
            y > min(max(pt1[1], pt2[1]), max(pt3[1], pt4[1])))):
            if x != pt3[0] and y != pt3[1]:
                error_code = 1
        return error_code
    
    #except condition if segments are parallel or colinear
    except ZeroDivisionError:
        try:
            l1a = (line1[1][1]-line1[0][1])/float((line1[1][0]-line1[0][0]))
            l1b = line1[0][1] - l1a*line1[0][0]
            l2a = (line2[1][1]-line2[0][1])/float((line2[1][0]-line2[0][0]))
            l2b = line2[0][1] - l2a*line2[0][0]
        #except condition if segments are vertical lines
        except ZeroDivisionError:
            l1b = line1[0][0]
            l2b = line2[0][0]
        if l1b == l2b:
            if not (pt4[1] < max(min(pt1[1], pt2[1]), min(pt3[1], pt4[1])) or
            pt4[1] > min(max(pt1[1], pt2[1]), max(pt3[1], pt4[1]))):
                error_code = 2
        return error_code

def Ref_inputBox():
    class popupWindow(tk.Tk):
        def __init__(self):
            tk.Tk.__init__(self)
            self.resizable(width=False, height=False)
            self.title("")
            self.l=tk.Label(self,text="Reflectance")
            self.l.pack()
            self.e=tk.Entry(self, width=30)
            self.e.bind('<Return>', self.cleanup)
            self.e.bind('<KP_Enter>', self.cleanup)
            self.e.pack()
            self.b=tk.Button(self,text="Ok", width=40, height=2)
            self.b.bind('<Button-1>', self.cleanup)
            self.b.pack()
            # Make popup window at the centre
            self.update_idletasks()
            w = self.winfo_screenwidth()
            h = self.winfo_screenheight()
            size = tuple(int(_) for _ in self.geometry().split('+')[0].split('x'))
            x = w/2 - size[0]/2
            y = h/2 - size[1]/2
            self.geometry("%dx%d+%d+%d" % (size + (x, y)))
        def cleanup(self, event):
            try:
                self.value=self.e.get()
                float(self.value)
                self.quit()
            except ValueError:
                if len(self.value) > 0:
                    messagebox.showerror("Warning!", 
                                         "Input must be number!")
                else:
                    messagebox.showerror("Warning!",
                                        "Input cannot be blank!")
                self.e.delete(0, 'end')
    m=popupWindow()
    m.mainloop()
    m.destroy()
    return eval(m.value)

def clearup(x):
    global mean_DN, reflectance
    if x:
        mean_DN = []
        reflectance = []

def main(band):
    global drawing, mode, roi_corners, ix, iy, temp, temp_zoom, mean_DN, reflectance, brightness, image_used
    gdal.AllRegister()
    root = tk.Tk()
    root.withdraw()
    ScreenH = root.winfo_screenheight()
    ScreenW = root.winfo_screenwidth()
    WindowH = ScreenH*2/3
    WindowW = ScreenW*2/3
    filetype = [('Tiff', ['*.tif', '*.TIF']), 
                ('Common 8-bit images', ['*.jpg', '*.jpeg', '*.png'])]
    title = 'Select the image to calibrate {} band'.format(band)
    while True:
        Fullfilename = askopenfilename(title=title, filetypes=filetype)
        
        try:
            path, filename = os.path.split(Fullfilename)
            BandName = Retrieve_Metadata.RetrieveData(Fullfilename, 'BandName')[filename]['BandName']
            if BandName == band:
                break
            else:
                messagebox.showinfo("Wrong band detected!", 
                                    "Wrong band detected. Please try again")
                
        except:
            messagebox.showinfo("Discard!", "No image is selected. No scalar is set for {}".format(band))
            break
        
    try:
        filename, ext = os.path.splitext(filename)
        image, ndv, alpha, GeoTransform, Projection, driver = \
            Read_Image(os.path.join(path, filename+ext))
        
        if ndv is not None:
            image = ma.masked_values(image,ndv)
            image_used = image.filled(0)
        else:
            image_used = image.copy()
        
        if alpha is not None:
            if alpha.max() != np.iinfo(alpha.dtype).max:
                alpha[alpha==alpha.max()] = np.iinfo(alpha.dtype).max
        if len(image_used.shape) > 2:
            if image_used.shape[2] == 3:
                image_used = image_used[...,::-1]
        temp = image_used.copy()
        temp_zoom = temp.copy()
        messagebox.showinfo(
                "Control tips", 
                "Use scroll bar to change mode:\n\n"
                "mode 0: draw polygon for regions of interest, right click to finish\n"
                "mode 1: zoom with rectangle, right click to reset extent\n\n"
                "When finish, press ESC to continue.")
        cv2.namedWindow("Original", cv2.WINDOW_NORMAL | cv2.WINDOW_GUI_NORMAL)
        cv2.resizeWindow("Original", int(WindowW), int(WindowH))
        cv2.moveWindow("Original", int(ScreenW/2-WindowW/2), int(ScreenH/2-WindowH/2))
        
        cv2.createTrackbar("mode", "Original", 0, 1, mode_switch)
        cv2.createTrackbar("brightness", "Original", 100, 300, adjust_brightness)
        
        cv2.setMouseCallback("Original", draw_polygon)
        
        while cv2.getWindowProperty("Original", 0) >= 0:
            cv2.imshow("Original", temp)
            key = cv2.waitKey(0) & 0xFF
            if key == 27:
                break
            cv2.getTrackbarPos("mode", "Original")
            cv2.getTrackbarPos("brightness", "Original")
        
        cv2.destroyAllWindows()
        
        meanDN = mean_DN
        ref = reflectance
        clearup(True)
        
        if len(meanDN) == len(ref) > 1:
            messagebox.showinfo('Multiple targets detected', 
                                'Multiple targets are detected \
                                \nOnly the last one will be used')
        elif len(meanDN) == len(ref) == 0:
            messagebox.showinfo('Discard!', 
                                    'No target is detected for calibration.')
            raise UnboundLocalError
        
        return meanDN[-1], ref[-1], Fullfilename
    
    except UnboundLocalError:
        pass
