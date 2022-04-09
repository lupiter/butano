"""
Copyright (c) 2020-2022 Gustavo Valiente gustavo.valiente@protonmail.com
zlib License, see LICENSE file.
"""

import shutil
import struct
from img_processor import ImageProcessor

class BMP(ImageProcessor):

    def __init__(self, file_path):
        super().__init__(file_path)

        with open(file_path, 'rb') as file:
            def read_int():
                return struct.unpack('I', file.read(4))[0]

            def read_short():
                return struct.unpack('H', file.read(2))[0]

            file.read(10)
            self.__pixels_offset = read_int()
            header_size = read_int()

            if header_size == 108:
                raise ValueError('Invalid header size: ' + str(header_size) +
                                 ' (BMP files with color space information are not supported)')

            if header_size != 40:
                raise ValueError('Invalid header size: ' + str(header_size))

            self.width = read_int()

            if self.width == 0 or self.width % 8 != 0:
                raise ValueError('Invalid width: ' + str(self.width))

            self.height = read_int()

            if self.height == 0 or self.height % 8 != 0:
                raise ValueError('Invalid height: ' + str(self.height))

            file.read(2)
            bits_per_pixel = read_short()

            if bits_per_pixel != 4 and bits_per_pixel != 8:
                raise ValueError('Invalid bits per pixel: ' + str(bits_per_pixel))

            compression_method = read_int()

            if compression_method != 0:
                raise ValueError('Compression method not supported: ' + str(compression_method))

            file.read(20)
            self.__colors_offset = file.tell()

            if bits_per_pixel == 4:
                colors_count = 16
            else:
                colors_count = 256
                self.__colors = struct.unpack(str(colors_count) + 'I', file.read(colors_count * 4))

                file.seek(self.__pixels_offset)
                pixels_count = self.width * self.height  # no padding, multiple of 8.
                self.__pixels = [ord(pixel) for pixel in
                                 struct.unpack(str(pixels_count) + 'c', file.read(pixels_count))]

                colors_count = max(self.__pixels) + 1
                extra_colors = colors_count % 16

                if extra_colors > 0:
                    colors_count += 16 - extra_colors

                if colors_count > 256:
                    raise ValueError('Invalid calculated colors count: ' + str(colors_count))

            self.colors_count = colors_count
