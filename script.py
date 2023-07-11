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


def findcurrentfolder():
    os.chdir('ImageAnalyzerASTJO')
    time_list = os.listdir()
    format_string = '%Y-%m-%d_%H-%M-%S'

    # Exclude '.DS_Store' from the time list
    time_list = [time for time in time_list if time != '.DS_Store']

    datetime_list = [datetime.strptime(time, format_string) for time in time_list]

    current_time = datetime.now()

    # Calculate the differences between the current time and each time in the list
    differences = [abs(current_time - dt) for dt in datetime_list]

    # Find the index of the closest time
    closest_index = differences.index(min(differences))

    # Get the closest time from the list
    closest_time = time_list[closest_index]
    return closest_time


def calibrate_image(image_array, gain, power):
    if power == 0:
        calibrated_image = image_array / gain
    else:
        calibrated_image = (image_array / power**2) / gain
    calibrated_image = np.clip(calibrated_image, -1, 1)
    return calibrated_image


def Normalizedcorrelation(FAD_array_cal, NADH_array_cal):
    normalized_FAD = (FAD_array_cal - np.mean(FAD_array_cal)) / np.std(FAD_array_cal)
    normalized_NADH = (NADH_array_cal - np.mean(NADH_array_cal)) / np.std(NADH_array_cal)

    normalized_FAD = normalized_FAD.astype(np.float32)  # Convert to CV_32F
    normalized_NADH = normalized_NADH.astype(np.float32)  # Convert to CV_32F

    correlation_map = cv2.matchTemplate(normalized_NADH, normalized_FAD, cv2.TM_CCORR_NORMED)
    return correlation_map


def PrettyRedox(redox, total_intensity, lut=None, botlim=0, uplim=1):
    ImR = np.sort(total_intensity[total_intensity != 0].flatten())[::-1]
    maxFlr = np.percentile(ImR, 1)  # 99th percentile
    minFlr = np.percentile(ImR, 99)  # 1st percentile
    avgi2 = (total_intensity - minFlr) / (maxFlr - minFlr)
    avgi2 = np.clip(avgi2, 0, 1)  # saturate bottom 1% and top 1%

    if lut is None:
        lut = plt.cm.jet(64)
        lut = np.array(lut)
    bitScale = lut.shape[0] - 1

    redox = (redox - botlim) / (uplim - botlim)
    redox = np.clip(redox, 0, 1)
    redox = 1 - redox  # Invert the redox values
    redox = np.round(bitScale * redox) + 1
    redox_indices = np.clip(redox.astype(int), 0, bitScale)  # Clip indices to valid range
    redox2 = lut[redox_indices]


    return redox2


def CreateRedox(fad_gain, nadh_gain, fad_power, nadh_power):
    os.chdir(findcurrentfolder())
    os.mkdir('results')
    FAD_list = sorted(os.listdir('FAD'), key=lambda x: int(re.findall(r'\d+', x.split('.')[0])[-1]))
    NADH_list = sorted(os.listdir('NADH'), key=lambda x: int(re.findall(r'\d+', x.split('.')[0])[-1]))
    for i in range(len(FAD_list)):
        FAD_image_path = f'FAD/{FAD_list[i]}'
        NADH_image_path = f'NADH/{NADH_list[i]}'

        FAD_image = plt.imread(FAD_image_path)
        NADH_image = plt.imread(NADH_image_path)

        FAD_image_array = np.array(FAD_image)
        NADH_image_array = np.array(NADH_image)

        im_size = NADH_image_array.shape[0]
        fad_image_calibrated = calibrate_image(FAD_image_array, fad_gain, fad_power)
        nadh_image_calibrated = calibrate_image(NADH_image_array, nadh_gain, nadh_power)
        correlation_map = Normalizedcorrelation(fad_image_calibrated, nadh_image_calibrated)
        corr_max_y, corr_max_x = np.unravel_index(correlation_map.argmax(), correlation_map.shape)
        y_shift = corr_max_y
        x_shift = corr_max_x
        fad_image_calibrated_shifted = shift(fad_image_calibrated, (y_shift, x_shift))
        
        fad_normalized = (fad_image_calibrated_shifted - np.min(fad_image_calibrated_shifted)) / ((np.max(fad_image_calibrated_shifted) - np.min(fad_image_calibrated_shifted)))
        nadh_normalized = (nadh_image_calibrated - np.min(nadh_image_calibrated)) / ((np.max(nadh_image_calibrated) - np.min(nadh_image_calibrated)))

# Calculate redox map
        redox_map = fad_normalized / (fad_normalized + nadh_normalized)


        total_intensity = fad_image_calibrated_shifted + nadh_image_calibrated

        redox_pretty = PrettyRedox(redox_map, total_intensity)
        redox_image_path = f'results/redox_image_{i}.tif'
        
        plt.imsave(redox_image_path, redox_pretty, cmap='gist_gray',vmax= 1, vmin = 0.5, format='tiff')


        mean_rr = np.mean(redox_map[redox_map != 0])

        rr_iqr = iqr(redox_map[redox_map != 0])
        infolist = [f'redox_map_{i}', mean_rr, rr_iqr]
        with open('db.csv', 'w') as f:

            writeline = csv.writer(f)
            writeline.writerow(infolist)








        
       
        





