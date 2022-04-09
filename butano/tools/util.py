import os

from bmp import BMP
from png_processor import PngProcessor

def remove_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)

def get_processor(file_path):
    if file_path.endswith(".png"):
        return PngProcessor(file_path)
    return BMP(file_path)


def validate_compression(compression):
    if compression != 'none' and compression != 'lz77' and compression != 'run_length' and compression != 'auto':
        raise ValueError('Unknown compression: ' + str(compression))


def compression_label(compression):
    if compression == 'none':
        return 'compression_type::NONE'

    if compression == 'lz77':
        return 'compression_type::LZ77'

    if compression == 'run_length':
        return 'compression_type::RUN_LENGTH'

    raise ValueError('Unknown compression: ' + str(compression))
