# TagLab                                               
# A semi-automatic segmentation tool                                    
#
# Copyright(C) 2019                                         
# Visual Computing Lab                                           
# ISTI - Italian National Research Council                              
# All rights reserved.                                                      
                                                                          
# This program is free software; you can redistribute it and/or modify      
# it under the terms of the GNU General Public License as published by      
# the Free Software Foundation; either version 2 of the License, or         
# (at your option) any later version.                                       
                                                                           
# This program is distributed in the hope that it will be useful,           
# but WITHOUT ANY WARRANTY; without even the implied warranty of            
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the             
#GNU General Public License (http://www.gnu.org/licenses/gpl.txt)          
# for more details.                                               

# THIS FILE CONTAINS UTILITY FUNCTIONS, E.G. CONVERSION BETWEEN DATA TYPES, BASIC OPERATIONS, ETC.

import io
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap, qRgb, qRgba
import numpy as np
import cv2
from skimage.draw import line
import datetime

def clampCoords(x, y, W, H):

    if x < 0:
        x = 0
    if y < 0:
        y = 0
    if x > W:
        x = W
    if y > H:
        y = H

    return (x, y)


def isValidDate(txt):
    """
    Check if a date in the ISO format YYYY-MM-DD is valid.
    """

    valid = True
    try:
        datetime.datetime.strptime(txt, '%Y-%m-%d')
#        datetime.date.fromisoformat(txt)
    except:
        valid = False

    return valid

def draw_open_polygon(r, c):
    r = np.round(r).astype(int)
    c = np.round(c).astype(int)

    # Construct line segments
    rr, cc = [], []
    for i in range(len(r) - 1):
        line_r, line_c = line(r[i], c[i], r[i + 1], c[i + 1])
        rr.extend(line_r)
        cc.extend(line_c)

    rr = np.asarray(rr)
    cc = np.asarray(cc)

    return rr, cc


def showMaskAndCurve(mask, bbox, curve, fig_number):
    import matplotlib.pyplot as plt
    
    arr = mask.copy()

    if curve is not None:
        for i in range(curve.shape[0]):
            xx = curve[i, 0] - bbox[1]
            yy = curve[i, 1] - bbox[0]
            if xx >= 0 and yy >= 0 and xx < bbox[2] and yy < bbox[3]:
                arr[yy, xx] = 2

    plt.figure(fig_number)
    plt.imshow(arr)
    plt.show()

def maskToQImage(mask):

    maskrgb = np.zeros((mask.shape[0], mask.shape[1], 3))
    maskrgb[:,:,0] = mask
    maskrgb[:,:,1] = mask
    maskrgb[:,:,2] = mask
    maskrgb = maskrgb * 255
    maskrgb = maskrgb.astype(np.uint8)

    qimg = rgbToQImage(maskrgb)
    return qimg


def labelsToQImage(mask):

    h = mask.shape[0]
    w = mask.shape[1]
    qimg = QImage(w, h, QImage.Format_RGB32)
    qimg.fill(qRgb(0, 0, 0))

    for y in range(h):
        for x in range(w):
            c = mask[y, x]
            qimg.setPixel(x, y, qRgb(c*17, c*163, c*211))

    return qimg

def floatmapToQImage(floatmap, nodata = float('NaN')):

    h = floatmap.shape[0]
    w = floatmap.shape[1]

    fmap = floatmap.copy()
    max_value = np.max(fmap)
    fmap[fmap == nodata] = max_value
    min_value = np.min(fmap)

    fmap = (fmap - min_value) / (max_value - min_value)
    fmap = 255.0 * fmap
    fmap = fmap.astype(np.uint8)

    img = np.zeros([h, w, 3], dtype=np.uint8)
    img[:,:,0] = fmap
    img[:,:,1] = fmap
    img[:,:,2] = fmap

    qimg = rgbToQImage(img)

    del fmap

    return qimg

def rgbToQImage(image):

    h = image.shape[0]
    w = image.shape[1]
    ch = image.shape[2]

    imgdata = np.zeros([h, w, 4], dtype=np.uint8)

    if ch == 3:
        imgdata[:, :, 2] = image[:, :, 0]
        imgdata[:, :, 1] = image[:, :, 1]
        imgdata[:, :, 0] = image[:, :, 2]
        imgdata[:, :, 3] = 255
        qimg = QImage(imgdata.data, w, h, QImage.Format_RGB32)

    elif ch == 4:
        imgdata[:, :, 3] = image[:, :, 0]
        imgdata[:, :, 2] = image[:, :, 1]
        imgdata[:, :, 1] = image[:, :, 2]
        imgdata[:, :, 0] = image[:, :, 3]
        qimg = QImage(imgdata.data, w, h, QImage.Format_ARGB32)

    return qimg.copy()

def figureToQPixmap(fig, dpi, width, height):

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi)
    buf.seek(0)
    img_arr = np.frombuffer(buf.getvalue(), dtype=np.uint8)
    buf.close()
    im = cv2.imdecode(img_arr, 1)
    im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)

    # numpy array to QPixmap
    qimg = rgbToQImage(im)
    qimg = qimg.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    pxmap = QPixmap.fromImage(qimg)

    return pxmap

def cropQImage(qimage_map, bbox):

    left = bbox[1]
    top = bbox[0]
    h = bbox[3]
    w = bbox[2]

    qimage_cropped = qimage_map.copy(left, top, w, h)

    return qimage_cropped


def qimageToNumpyArray(qimg):

    w = qimg.width()
    h = qimg.height()

    fmt = qimg.format()
    assert (fmt == QImage.Format_RGB32)

    arr = np.zeros((h, w, 3), dtype=np.uint8)

    bits = qimg.bits()
    bits.setsize(int(h * w * 4))
    arrtemp = np.frombuffer(bits, np.uint8).copy()
    arrtemp = np.reshape(arrtemp, [h, w, 4])
    arr[:, :, 0] = arrtemp[:, :, 2]
    arr[:, :, 1] = arrtemp[:, :, 1]
    arr[:, :, 2] = arrtemp[:, :, 0]

    return arr

