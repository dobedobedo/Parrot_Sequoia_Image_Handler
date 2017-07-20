#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  7 12:26:49 2017

@author: Yu-Hsuan Tu
This module is designed to scan specific file type in selected directory
Do not use to scan directories

**************************************************************
Usage:
Add the following codes in your script:
    
import Retrieve_Metadata
from Retrieve_Metadata import PathImage

Metadata = Retrieve_Metadata.RetrieveData(PathImage, 'Tags')
**************************************************************
'Tags' are optional and must be separated by comma.

If there's no Tags arguments, the program will retrieve all accessible tags.
However, it will be very time-consuming.
"""

import os
import subprocess
from glob import glob
import sys
import tkinter as tk
from tkinter.filedialog import askdirectory
from tkinter import messagebox

def RetrieveData(PathImage, *Tags):
    #Retrive all metadata using exiftool
    Args = ['exiftool', '-s', '{File}'.format(File=PathImage)]
    for Tag in Tags:
        Args.insert(-1, '-{}'.format(Tag))
    command = ' '.join(Args)
    MetadataLines = subprocess.run(command,
                              shell=True, 
                              stdout=subprocess.PIPE,
                              universal_newlines=True).stdout.split('\n')
    ImageMetadata = {}
    Metadata = {}
    
    # Store metadata as dictionarty
    for LineIndex in range(len(MetadataLines)):
        item = MetadataLines[LineIndex].split(' ',1)
        
        # Skip the record if encounter error
        if 'Error' in item[0]:
            continue
        
        # Check whether there are multiple images
        if len(glob(PathImage)) > 1:
            
            # Record the first line's filename
            if LineIndex == 0:
                path, UsedFilename = os.path.split(item[1].strip())
                continue
            
            # Break at the second last line
            elif LineIndex == len(MetadataLines) - 2:
                if len(Metadata) > 0:
                    ImageMetadata[UsedFilename] = Metadata
                break
            else:
                
                # If reach a new file's metadata, record the current metadata
                # And start a new record
                if '==' in item[0].strip():
                    if len(Metadata) > 0:
                        ImageMetadata[UsedFilename] = Metadata
                    path, UsedFilename = os.path.split(item[1].strip())
                    Metadata = {}
                    continue
                else:
                    Metadata[item[0].strip()] = item[1].strip().lstrip(': ')
        else:
            if LineIndex == len(MetadataLines) -1:
                path, UsedFilename = os.path.split(glob(PathImage)[0])
                if len(Metadata) > 0:
                    ImageMetadata[UsedFilename] = Metadata
                break
            Metadata[item[0].strip()] = item[1].strip().lstrip(': ')
            
    return ImageMetadata

def Ext_SelectBox():
    class popupWindow(tk.Tk):
        def __init__(self):
            tk.Tk.__init__(self)
            # Make window unresizable
            self.resizable(width=False, height=False)
            self.title("Select file format")
            # Make a drop down menu
            self.v=tk.StringVar(self)
            self.v.set('TIF')
            self.opt=tk.OptionMenu(self,self.v,*['TIF', 'JPG'])
            self.opt.pack(side='left', padx=10, pady=10)
            # Make an ok button
            self.b=tk.Button(self,text="Ok", width=35, height=2)
            self.b.bind('<Button-1>', self.select)
            self.b.pack()
            # Make clicking x to exit application
            self.protocol("WM_DELETE_WINDOW", self.on_exit)
            # Make popup window at the centre
            self.update_idletasks()
            w = self.winfo_screenwidth()
            h = self.winfo_screenheight()
            size = tuple(int(_) for _ in self.geometry().split('+')[0].split('x'))
            x = w/2 - size[0]/2
            y = h/2 - size[1]/2
            self.geometry("%dx%d+%d+%d" % (size + (x, y)))
                   
        def select(self, event):
            self.value=self.v.get()
            self.quit()
        def on_exit(self):
        # When you click x to exit, this function is called
            if messagebox.askyesno("Exit", "Do you want to quit the application?"):
                self.destroy()
                sys.exit(0)
        
    m=popupWindow()
    m.mainloop()
    m.destroy()
    return m.value

root = tk.Tk().withdraw()
Ext = Ext_SelectBox()
path = askdirectory()
PathImage = os.path.join(path, '*.{}'.format(Ext))
