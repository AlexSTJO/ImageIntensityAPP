# ImageIntensityAPP
Completed Application -- creates redox from two images -- Created for Georgakoudi Lab

PyQt6 Application that takes 8-bit(get coverted to 16-bit) or 16-bit tif files, organizes them in dated folder. 
The GUI takes four float values, gain and power for each images, and then performs a specified operation on them. 
The resulting images and data(mean redox ratio and iqr) are stored in the results folder.
There is also the option to add a prettyRedox function which saturates the top 1 and bottom 1 percent of the pixel values.
