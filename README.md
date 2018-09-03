# Parrot_Sequoia_Image_Handler
Homemade code to deal with Parrot Sequoia Images

Modules will be continuously updated  
  
# Tools included:
  - **Creating_Shape**: Create shapefile and kml for images waypoints and shapefile for trajectory based on photo's geotags  
  - **Sunshine_Normalisation**: Adjust photo's brightness based on the sunshine sensor's measurement  
  - **Calculate_Radiance**: Convert Photo's pixel values to radiance without panel image or reflectance with panel image.  
  - **Vignetting_Correction**: Correct photo's vignetting effect
  
# Note
Several python dependencies are needed:  
 - **numpy**  
 - **gdal**  
 - **opencv**  
 - **pytz**  
  
The tools use the three modules in _Dependency_. Please put them in the same folder.  
exiftool is required. See http://www.sno.phy.queensu.ca/~phil/exiftool/  
Put the exiftool executable to the same folder or add it to your environment path.
