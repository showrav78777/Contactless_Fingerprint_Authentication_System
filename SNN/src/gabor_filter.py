"""
The principle of gabor filtering is to modify the value of the pixels of an image, generally in order to
improve its appearance. In practice, it is a matter of creating a new image using the pixel values
of the original image, in order to select in the Fourier domain the set of frequencies that make up
the region to be detected. The filter used is the Gabor filter with even symmetry and oriented at 0 degrees.

The resulting image will be the spatial convolution of the original (normalized) image and one of
the base filters in the direction and local frequency from the two directional and frequency maps
https://airccj.org/CSCP/vol7/csit76809.pdf pg.91
"""

import numpy as np
import scipy
def gabor_filter(im, orient, freq, kx=0.65, ky=0.65):
    """
    Gabor filter is a linear filter used for edge detection. Gabor filter can be viewed as a sinusoidal plane of
    particular frequency and orientation, modulated by a Gaussian envelope.
    :param im:
    :param orient:
    :param freq:
    :param kx:
    :param ky:
    :return:
    """
    angleInc = 3
    im = np.double(im)
    rows, cols = im.shape
    return_img = np.zeros((rows,cols))

    # Check if input arrays are valid
    if im.size == 0 or orient.size == 0 or freq.size == 0:
        return np.zeros_like(im, dtype=np.uint8)

    # Round the array of frequencies to the nearest 0.01 to reduce the
    # number of distinct frequencies we have to deal with.
    freq_1d = freq.flatten()
    frequency_ind = np.array(np.where(freq_1d>0))
    non_zero_elems_in_freq = freq_1d[frequency_ind]
    
    # Check if we have any non-zero frequencies
    if len(non_zero_elems_in_freq) == 0:
        return np.zeros_like(im, dtype=np.uint8)
    
    non_zero_elems_in_freq = np.double(np.round((non_zero_elems_in_freq*100)))/100
    unfreq = np.unique(non_zero_elems_in_freq)

    # Check if we have any unique frequencies
    if len(unfreq) == 0:
        return np.zeros_like(im, dtype=np.uint8)

    # Generate filters corresponding to these distinct frequencies and
    # orientations in 'angleInc' increments.
    sigma_x = 1/unfreq[0]*kx  # Use first unique frequency
    sigma_y = 1/unfreq[0]*ky  # Use first unique frequency
    block_size = int(np.round(3*np.max([sigma_x,sigma_y])))
    
    # Ensure block_size is at least 1
    block_size = max(1, block_size)
    
    array = np.linspace(-block_size,block_size,(2*block_size + 1))
    x, y = np.meshgrid(array, array)

    # gabor filter equation
    reffilter = np.exp(-(((np.power(x,2))/(sigma_x*sigma_x) + (np.power(y,2))/(sigma_y*sigma_y)))) * np.cos(2*np.pi*unfreq[0]*x)
    filt_rows, filt_cols = reffilter.shape
    gabor_filter = np.array(np.zeros((180//angleInc, filt_rows, filt_cols)))

    # Generate rotated versions of the filter.
    for degree in range(0,180//angleInc):
        rot_filt = scipy.ndimage.rotate(reffilter,-(degree*angleInc + 90),reshape = False)
        gabor_filter[degree] = rot_filt

    # Convert orientation matrix values from radians to an index value that corresponds to round(degrees/angleInc)
    maxorientindex = int(np.round(180/angleInc))
    orientindex = np.round(orient/np.pi*180/angleInc).astype(np.int64)
    
    # Ensure orientindex is within valid range
    orientindex = np.clip(orientindex, 0, maxorientindex-1)
    
    # Find indices of matrix points greater than maxsze from the image boundary
    valid_row, valid_col = np.where(freq>0)
    if len(valid_row) == 0 or len(valid_col) == 0:
        return np.zeros_like(im, dtype=np.uint8)
        
    finalind = np.where((valid_row>block_size) & (valid_row<rows - block_size) & 
                       (valid_col>block_size) & (valid_col<cols - block_size))

    # Check if we have any valid indices
    if len(finalind[0]) == 0:
        return np.zeros_like(im, dtype=np.uint8)

    for k in range(0, np.shape(finalind)[1]):
        r = int(valid_row[finalind[0][k]])
        c = int(valid_col[finalind[0][k]])
        img_block = im[r-block_size:r+block_size + 1][:,c-block_size:c+block_size + 1]
        return_img[r][c] = np.sum(img_block * gabor_filter[int(orientindex[r//16][c//16]) - 1])

    gabor_img = 255 - np.array((return_img < 0)*255).astype(np.uint8)

    return gabor_img
