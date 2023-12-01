try:
    import javabridge
    import bioformats
    bf_avail = True
except Exception as E:
    print(E)
    print("continuing without bioformats library")
    bf_avail = False

import numpy as np
import os
import skimage.io as io

def read_bioformats_to_numpy(filepath, time_chunk_size=1):
    """
    Reads a bioformats compatible file into a numpy array.

    Dimensions are returned in the order [z, c, t, x, y].

    Args:
        filepath (str): Path to the bioformats file.
        time_chunk_size (int): Number of time points to read in one chunk.

    Returns:
        numpy.ndarray: A 5D numpy array representing the image data.
    """
    reader = bioformats.ImageReader(filepath)

    # Get dimensions
    x_size = reader.rdr.getSizeX()
    y_size = reader.rdr.getSizeY()
    z_size = reader.rdr.getSizeZ()
    t_size = reader.rdr.getSizeT()
    c_size = reader.rdr.getSizeC()

    # Initialize numpy array
    full_data = np.empty((z_size, c_size, t_size, x_size, y_size), dtype=np.uint16)

    # Read data in chunks for time dimension
    for z in range(z_size):
        for c in range(c_size):
            for t in range(0, t_size, time_chunk_size):
                end_t = min(t + time_chunk_size, t_size)
                for time in range(t, end_t):
                    data_chunk = reader.read(c=c, z=z, t=time, rescale=False)
                    try:
                        full_data[z, c, time] = data_chunk
                    except ValueError as e:
                        if "could not broadcast input array" in str(e):
                            full_data[z, c, time] = data_chunk.T
                        else:
                            raise

    return full_data

def convert_to_2Dplust(input_data):
    """
    Reduces dimensions of bioformats input.
    Args:
        input_data: array of shape [z, c, t, x, y]

    Returns:
        a list of arrays of shape [t, x, y]
        length of the list = number of channels
        !! z is assumed to be t if given, 3D stack is not supported !!

    """
    nb_channels = input_data.shape[1]
    sz_z = input_data.shape[0]
    sz_t = input_data.shape[2]
    if sz_z > 1 and sz_t > 1:
        print("too many dimensions, cannot process further")
        return None
    else:
        output_list = []
        for c in range(nb_channels):
            output = np.squeeze(input_data[:, c, :, :, :])
            if output.ndim < 3:
                print("too few dimensions, cannot handle 2D images yet")
                return None
            else:
                output_list.append(output)
        return output_list

def return_channels(input_data_list, input_format="two-in-one", channel=None):
    """
    Returns two channels from bioformats input.
    Args:
        input_data_list: list of arrays, each of shape [t, x, y], length=number of channels
        input_format:"two-in-one" = two channels are side-by-side within the same frame
                    "single" = each channel is separate image
        channel: None = return whole image, "both" = return both channels as tuple

    Returns:
        - either whole image or two channels in format [t, x, y]

    """
    nb_channels = len(input_data_list)
    if nb_channels > 2:
        print("too many channels, can only handle two")
        return
    elif nb_channels == 2:
        channel1 = input_data_list[0]
        channel2 = input_data_list[1]
    else:
        if input_format == "two-in-one":
            channel1, channel2 = np.split(input_data_list[0], 2, axis=2)
        else:
            channel1 = input_data_list[0]
            channel2 = None
    if channel == "both":
        return channel1, channel2
    elif channel == 1:
        return channel1
    elif channel == 2:
        return channel2
    else:
        return input_data_list[0]

def load_data(input_path, input_format, channel=None, **bf_kwargs):
    """
    Loads image data and returns an array of dimensions [t, x, y]

    Args:
        input_path: complete filename including file name + ending
        input_format: flag whether the channels are side-by-side or in single images;
                      "two-in-one" = side by side
                      "single" = one channel per image
        channel: optional, can be
                - None: entire image is returned
                - 1 or 2: single channel is returned accordingly
                - "both": channels are returned in a tuple (ch1, ch2)
        **bf_kwargs: additional arguments for bioformats input
                    - time_chunk_size: how many frames are read at once, defaults to 10

    Returns:
        img_data: either the whole image (if "channel" is None) or chosen channel

    """
    _, ext = os.path.splitext(input_path)
    if ext.lower() in ['.tif', '.tiff']:
        img_data = io.imread(input_path)
        assert img_data.ndim == 3, f"Only 2D+t data is supported at the moment"
        if channel:
            if input_format == "two-in-one":
                ch1, ch2 = np.split(img_data, 2, axis=2)
                if channel==1:
                    return ch1
                elif channel==2:
                    return ch2
                elif channel=="both":
                    return ch1, ch2
                else:
                    return img_data
            else:
                return img_data
        else:
            return img_data
    else:
        if bf_avail:
            time_chunk_size = bf_kwargs.get("time_chunk_size", 10)
            try:
                img_data = read_bioformats_to_numpy(input_path, time_chunk_size=time_chunk_size)
            except Exception as E:
                print(E)
                print("Problem with Java or Bioformat Library !")
                return
            data_2Dplust = convert_to_2Dplust(img_data) # reduce dimensions to [t, x, y]
            if channel == "both":
                ch1, ch2 = return_channels(data_2Dplust, channel="both")
                return ch1, ch2
            elif channel == 1:
                ch1, ch2 = return_channels(data_2Dplust, channel="both")
                return ch1
            elif channel == 2:
                ch1, ch2 = return_channels(data_2Dplust, channel="both")
                return ch2
            else:
                return return_channels(data_2Dplust, channel=None)
        else:
            print(f"File Format {ext} not supported. Try installing the bioformats library according to documentation.")
            return
