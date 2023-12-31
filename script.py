import os
from datetime import datetime
import re
import cv2
import numpy as np
from scipy.ndimage import shift
from skimage import exposure
from scipy.signal import correlate2d
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from scipy.stats import iqr
import csv
from PIL import Image

# CALLED BY CREATEREDOX-- This function checkes the image for bit-depth, if image is 8-bit image performs math(22) to convert to 16-bit
def convert_to_16_bit(image_path):
    img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    bit_depth = img.dtype.itemsize * 8

    if bit_depth == 8:
        # Perform bit depth expansion to convert 8-bit image to 16-bit image
        img_16_bit = img.astype(np.uint16) * 257  # Scale the values to [0, 65535]

        # Overwrite the original image with the converted 16-bit image
        cv2.imwrite(image_path, img_16_bit)

         # Return the path of the modified image

    return None
# CALLED BY CREATEREDOX-- This function checks each dated directory and finds the current instance(the folder with closest time to present)
def findcurrentfolder():
    # Pulls list of folders and initalizes a foramtting string
    os.chdir('ImageAnalyzerASTJO')
    time_list = os.listdir()
    format_string = '%Y-%m-%d_%H-%M-%S'

    # Exclude '.DS_Store' from the time list
    time_list = [time for time in time_list if time != '.DS_Store']

    # Uses format string to use the strptime function to isolate the times.
    datetime_list = [datetime.strptime(time, format_string) for time in time_list]

    current_time = datetime.now()

    # Calculate the differences between the current time and each time in the list
    differences = [abs(current_time - dt) for dt in datetime_list]

    # Find the index of the closest time
    closest_index = differences.index(min(differences))

    # Get the closest time from the list
    closest_time = time_list[closest_index]
    return closest_time

# CALLED BY CREATEREDOX --  This function performs math using the power and gain inputs from the client. It then normalizes the values so they scale properly
def CalibrateImage(image_array, gain, power):
    if power == 0:
        calibrated_image = image_array / gain
    else:
        calibrated_image = (image_array / power**2) / gain

    # Find the minimum and maximum values of the calibrated image
    min_value = np.min(calibrated_image)
    max_value = np.max(calibrated_image)

    # Normalize the calibrated image between -1 and 1
    normalized_image = -1 + 2 * (calibrated_image - min_value) / (max_value - min_value)

    return normalized_image

# CALLED BY CREATEREDOX-- This function checks the images to see if they are properly centered onto eachother, it uses a coorelation function to center the images on to themselves
def Normalizedcorrelation(FAD_array_cal, NADH_array_cal):
    # Normalization process
    normalized_FAD = (FAD_array_cal - np.mean(FAD_array_cal)) / np.std(FAD_array_cal)
    normalized_NADH = (NADH_array_cal - np.mean(NADH_array_cal)) / np.std(NADH_array_cal)

    # Data convertion
    normalized_FAD = normalized_FAD.astype(np.float32)  # Convert to CV_32F
    normalized_NADH = normalized_NADH.astype(np.float32)  # Convert to CV_32F
    
    # Coorelation mapping
    correlation_map = cv2.matchTemplate(normalized_NADH, normalized_FAD, cv2.TM_CCORR_NORMED)
    return correlation_map

# CALLED BY CREATEREDOX -- This function isolates the 99th and 1st percentile inetencities to and saturates the values to the bottom and top 1%. This makes the intensities much ore distinguishable
def PrettyRedox(redox, total_intensity, lut=None, botlim=0, uplim=1):
    # Isolation process
    ImR = np.sort(total_intensity[total_intensity != 0].flatten())[::-1]
    maxFlr = np.percentile(ImR, 1)  # 99th percentile
    minFlr = np.percentile(ImR, 99)  # 1st percentile
    avgi2 = (total_intensity - minFlr) / (maxFlr - minFlr)
    avgi2 = np.clip(avgi2, 0, 1)  # saturate bottom 1% and top 1%

    # Colormapping and bitscale convertion
    if lut is None:
        lut = plt.cm.jet(64)
        lut = np.array(lut)
    bitScale = lut.shape[0] - 1

    # Isolation lapsed onto actual redox values
    redox = (redox - botlim) / (uplim - botlim)
    redox = np.clip(redox, 0, 1)
    redox = 1 - redox  # Invert the redox values
    redox = np.round(bitScale * redox) + 1
    redox_indices = np.clip(redox.astype(int), 0, bitScale)  # Clip indices to valid range
    redox2 = lut[redox_indices]


    return redox2

# CALLED BY CREATEREDOX -- This function takes user input of what type of redox they desire and performs the operations necessary. 
# This function also converts nan and inf values to 0. Outlier control
def typeofredox(choice, fad , nadh):

    operations = {
        'NADH_div_FAD': lambda x, y: np.divide(x, y),
        'NADH_div_FAD_NADH': lambda x, y: np.divide(x, x + y),
        'FAD_div_NADH': lambda x, y: np.divide(x, y),
        'FAD_div_NADH_FAD': lambda x, y: np.divide(x, x + y)
    }

    with np.errstate(divide='ignore', invalid='ignore'):
        redox = operations[choice](fad, nadh)

    redox[np.isnan(redox)] = 0  # Replace NaN with 0
    redox[np.isinf(redox)] = 0  # Replace infinity with 0

    return redox
# MAIN CALLING -- CALLED BY client.py -- THis function creates redox and calls all functions transforming data
def CreateRedox(fad_gain, nadh_gain, fad_power, nadh_power, choice, apply_pretty_redox):
    # Finds current directory and creates two sorted lists of all the input images. This order makes the images linked based off of what they end in. ie. FADH_List[2] = FADHIMAGE_3, NADH_LIST[2] = NADHIMAGE_3
    os.chdir(findcurrentfolder())
    if not os.path.exists('results'):
        os.mkdir('results')
    results_path = os.getcwd() + '/results'
    FAD_list = sorted(os.listdir('FAD'), key=lambda x: int(re.findall(r'\d+', x.split('.')[0])[-1]))
    NADH_list = sorted(os.listdir('NADH'), key=lambda x: int(re.findall(r'\d+', x.split('.')[0])[-1]))

    # Iterates through each of the image pairs and performs operations creating redox
    for i in range(len(FAD_list)):
        # Takes path and converts them to 16 bit if 8 bit
        FAD_image_path = f'FAD/{FAD_list[i]}'
        NADH_image_path = f'NADH/{NADH_list[i]}'
        convert_to_16_bit(FAD_image_path)
        convert_to_16_bit(NADH_image_path)

        # Creates arrays of intensities based using MATPLOTLIB and NUMPY
        FAD_image = plt.imread(FAD_image_path)
        NADH_image = plt.imread(NADH_image_path)

        FAD_image_array = np.array(FAD_image)
        NADH_image_array = np.array(NADH_image)

        # Calibrates images with user input
        fad_image_calibrated = CalibrateImage(FAD_image_array, fad_gain, fad_power)
        nadh_image_calibrated = CalibrateImage(NADH_image_array, nadh_gain, nadh_power)

        # Centers images with eachotehr, to insure values are paired
        correlation_map = Normalizedcorrelation(fad_image_calibrated, nadh_image_calibrated)
        corr_max_y, corr_max_x = np.unravel_index(correlation_map.argmax(), correlation_map.shape)
        y_shift = corr_max_y
        x_shift = corr_max_x
        fad_image_calibrated_shifted = shift(fad_image_calibrated, (y_shift, x_shift))
        
        # Normalizes the values, since the values tend to be a very reduced numbers that cant have accurate math performed on the,
        fad_normalized = (fad_image_calibrated_shifted - np.min(fad_image_calibrated_shifted)) / ((np.max(fad_image_calibrated_shifted) - np.min(fad_image_calibrated_shifted)))
        nadh_normalized = (nadh_image_calibrated - np.min(nadh_image_calibrated)) / ((np.max(nadh_image_calibrated) - np.min(nadh_image_calibrated)))

        # Calculate redox map
        redox_map = typeofredox(choice, fad_normalized, nadh_normalized)

        # Pull total_intensity

        # Saves Redox Image in results folder
        redox_image_path = f'results/redox_image_{i}_{choice}.tif'
        
        plt.imsave(redox_image_path, redox_map, cmap='plasma',vmax= 1, vmin = 0.5, format='tiff')

        # If Pretty Redox Option selected, performs necessary operations and saves the pretty redox to results
        if apply_pretty_redox:
            total_intensity = fad_image_calibrated_shifted + nadh_image_calibrated
            redox_map = PrettyRedox(redox_map, total_intensity)
            redox_image_path = f'results/redox_image_{i}_{choice}_pretty.tif'
            plt.imsave(redox_image_path, redox_map, cmap='plasma',vmax= 1, vmin = 0.5, format='tiff')

        #saves mean and interquartile range to a csv file
        mean_rr = np.mean(redox_map[redox_map != 0])

        rr_iqr = iqr(redox_map[redox_map != 0])
        infolist = [f'redox_map_{i}', choice, mean_rr, rr_iqr]
        with open('db.csv', 'w') as f:

            writeline = csv.writer(f)
            writeline.writerow(infolist)
    return results_path








        
       
        





