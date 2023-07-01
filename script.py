
import os
from datetime import datetime
import re
import cv2
from PIL import Image
import numpy as np
from scipy.ndimage import shift
from scipy.ndimage import maximum_position
from skimage import exposure
from scipy.signal import correlate2d
import matplotlib.pyplot as plt

def findcurrentfolder():
    os.chdir('ImageAnalyzerASTJO')
    time_list = os.listdir()
    format_string = '%Y-%m-%d_%H-%M-%S'
    datetime_list = [datetime.strptime(time, format_string) for time in time_list]

   
    current_time = datetime.now()

    # Calculate the differences between the current time and each time in the list
    differences = [abs(current_time - dt) for dt in datetime_list]

    # Find the index of the closest time
    closest_index = differences.index(min(differences))

    # Get the closest time from the list
    closest_time = time_list[closest_index]
    return closest_time


def calibrate_image(image_array,gain,power):
    if power == 0:
        calibrated_image=image_array/gain
    else:
        calibrated_image=(image_array/power**2)/gain
    calibrated_image = np.clip(calibrated_image, -1, 1)
    return calibrated_image

def Normalizedcorrelation(FAD_array_cal, NADH_array_cal):
    print(FAD_array_cal)
    normalized_FAD = (FAD_array_cal - np.mean(FAD_array_cal)) /np.std(FAD_array_cal)
    normalized_NADH = (NADH_array_cal - np.mean(NADH_array_cal)) /np.std(NADH_array_cal)

    relation = correlate2d(normalized_NADH, normalized_FAD, mode='same', boundary='fill', fillvalue=0)
    return relation

def PrettyRedox(redox, total_intensity, lut=None, botlim=0, uplim=1):
    ImR = np.sort(total_intensity[total_intensity != 0].flatten())[::-1]
    maxFlr = np.percentile(ImR, 1)  # 99th percentile
    minFlr = np.percentile(ImR, 99)  # 1st percentile
    avgi2 = (total_intensity - minFlr) / (maxFlr - minFlr)
    avgi2 = np.where(avgi2 < 1, avgi2, 1)  # saturate top 1%
    avgi2 = np.where(avgi2 >= 0, avgi2, 0)  # saturate bottom 1%

    if lut is None:
        lut = plt.cm.jet(64)
        lut = np.array(lut)
    bitScale = lut.shape[0] - 1

    redox = (redox - botlim) / (uplim - botlim)
    redox = np.where(redox < 1, redox, 1)
    redox = np.round(bitScale * np.where(redox >= 0, redox, 0)) + 1

    redox_indices = np.clip(redox.astype(int), 0, bitScale)  # Clip indices to valid range
    redox2 = lut[redox_indices]
    
    return redox2





def script(fad_gain, nadh_gain, fad_power, nadh_power):
    os.chdir(findcurrentfolder())
    #os.mkdir('results')
    FAD_list = sorted(os.listdir('FAD'), key=lambda x: int(re.findall(r'\d+', x.split('.')[0])[-1]))
    NADH_list = sorted(os.listdir('NADH'), key=lambda x: int(re.findall(r'\d+', x.split('.')[0])[-1]))
    for i in range(len(FAD_list)):
        FAD_image_array = cv2.imread(f'FAD\{FAD_list[i]}', 0)
        NADH_image_array = cv2.imread(f'NADH\{NADH_list[i]}', 0)
        im_size = NADH_image_array.shape[0]
        calibrated_FAD_array = calibrate_image(FAD_image_array,fad_gain, fad_power)
        calibrated_NADH_array = calibrate_image(NADH_image_array,nadh_gain, nadh_power)
        correlation_map = Normalizedcorrelation(calibrated_FAD_array, calibrated_NADH_array)
        corr_max_y, corr_max_x = np.unravel_index(correlation_map.argmax(), correlation_map.shape)
        print(corr_max_y)
        print(corr_max_x)
        y_shift = corr_max_y - im_size/2
        x_shift = corr_max_x - im_size/2

        print(y_shift)
        print(x_shift)
        
        fad_image_calibrated_shifted = shift(calibrated_FAD_array, (y_shift, x_shift))
        #nadh_image_calibrated_adapt = exposure.equalize_adapthist(calibrated_NADH_array)

        redox_map = fad_image_calibrated_shifted / (fad_image_calibrated_shifted + calibrated_NADH_array)
        total_intensity = fad_image_calibrated_shifted + calibrated_NADH_array


        redox_pretty = PrettyRedox(redox_map, total_intensity )
        #np.set_printoptions(threshold=np.inf)
        plt.imshow(redox_pretty)  # Adjust spacing if needed
        plt.show()

        #plt.imsave('results/redox_image.png', redox_pretty)
        
       
        



script(12, 12, 500, 500)




