import png
from itertools import zip_longest

from img_processor import ImageProcessor

class PngProcessor(ImageProcessor):
    def __init__(self, file_path):
        super().__init__(file_path)
        with open(file_path, 'rb') as file:
            r = png.Reader(file)
            width, height, rows, info = r.read()
            self.width = width
            self.height = height
            self.__pixels = rows
            try:
                self.__colors = r.palette()
            except png.FormatError as e: # no palette built in, calculate
                channels = 3
                if info["greyscale"]:
                    channels = 1
                if info["alpha"]:
                    channels += 1
                self.calculate_palette(rows, channels)
            self.colors_count = len(self.__colors)

    def calculate_palette(self, rows, channels):
        colors = set()
        for row in rows:
            args = [iter(row)] * channels
            for color in zip_longest(*args):
                colors.add(color)
        self.__colors = list(colors)
