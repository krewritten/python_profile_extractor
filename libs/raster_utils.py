# script for raster specific functions
from osgeo import gdal


def offset(x, y, x_origin, y_origin, pix_width, pix_height):
    """
    function for getting x,y offset from raster. This is a modified version of the offset function used in assignment 9.
    :param x: x of desired pixel offset
    :param y: y of desired pixel offset
    :param x_origin: x origin of input raster
    :param y_origin: y origin of input raster
    :param pix_width: pixel width of input raster
    :param pix_height: pixel height of input raster
    :return: x,y offset values
    """
    x_offset = int((x - x_origin) / pix_width)
    y_offset = int((y - y_origin) / pix_height)
    return [x_offset, y_offset]


def pixel_values(x, y, source):
    """
    function to get pixel values from raster
    :param x: x-coordinate
    :param y: y-coordinate
    :param source: target raster (GDAL raster object, need to gdal.Open() raster before inputting into function)
    :return: pixel value at (x, y)
    """
    gdal.PushErrorHandler('CPLQuietErrorHandler')
    # above code silences the GDAl error for the vector extending off the image and
    # instead uses the native python IndexError and TypeError exceptions for error handling (see below)
    pixel_val = []
    geo_trans = source.GetGeoTransform()
    x_org = geo_trans[0]
    y_org = geo_trans[3]
    pix_w = geo_trans[1]
    pix_h = geo_trans[5]
    band = source.GetRasterBand(1)

    px_offset = offset(x, y, x_org, y_org, pix_w, pix_h)

    val = band.ReadAsArray(px_offset[0], px_offset[1], 1, 1)

    try:
        pixel_val.append(*val)
    #  both of the exceptions deal with shapefiles that extend beyond the raster imagery and are handled in
    #  native python rather than in the GDAL specific library
    except TypeError:
        print("No data for point ({}, {})".format(px_offset[0], px_offset[1]))
    except IndexError:
        print("No data for point ({}, {})".format(px_offset[0], px_offset[1]))
    else:
        return pixel_val
