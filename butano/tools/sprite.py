import subprocess
import re

from util import get_processor, remove_file, compression_label, validate_compression


class SpriteItem:

    @staticmethod
    def valid_sizes_message():
        return ' (valid sprite sizes: 8x8, 16x16, 32x32, 64x64, 16x8, 32x8, 32x16, 8x16, 8x32, 16x32, 32x64)'

    @staticmethod
    def shape_and_size(width, height):
        if width == 8:
            if height == 8:
                return 'SQUARE', 'SMALL'
            elif height == 16:
                return 'TALL', 'SMALL'
            elif height == 32:
                return'TALL', 'NORMAL'
            elif height == 64:
                raise ValueError('Invalid sprite size: (' + str(width) + 'x' + str(height) + ')' +
                                 SpriteItem.valid_sizes_message())
            else:
                raise ValueError('Invalid sprite height: ' + str(height) + SpriteItem.valid_sizes_message())
        elif width == 16:
            if height == 8:
                return 'WIDE', 'SMALL'
            elif height == 16:
                return 'SQUARE',  'NORMAL'
            elif height == 32:
                return 'TALL', 'BIG'
            elif height == 64:
                raise ValueError('Invalid sprite size: (: ' + str(width) + 'x' + str(height) + ')' +
                                 SpriteItem.valid_sizes_message())
            else:
                raise ValueError('Invalid sprite height: ' + str(height) + SpriteItem.valid_sizes_message())
        elif width == 32:
            if height == 8:
                return 'WIDE', 'NORMAL'
            elif height == 16:
                return 'WIDE', 'BIG'
            elif height == 32:
                return 'SQUARE', 'BIG'
            elif height == 64:
                return 'TALL', 'HUGE'
            else:
                raise ValueError('Invalid sprite height: ' + str(height) + SpriteItem.valid_sizes_message())
        elif width == 64:
            if height == 8:
                raise ValueError('Invalid sprite size: (' + str(width) + 'x' + str(height) + ')' +
                                 SpriteItem.valid_sizes_message())
            elif height == 16:
                raise ValueError('Invalid sprite size: (' + str(width) + 'x' + str(height) + ')' +
                                 SpriteItem.valid_sizes_message())
            elif height == 32:
                return 'WIDE', 'HUGE'
            elif height == 64:
                return 'SQUARE', 'HUGE'
            else:
                raise ValueError('Invalid sprite height: ' + str(height) + SpriteItem.valid_sizes_message())
        else:
            raise ValueError('Invalid sprite width: ' + str(width) + SpriteItem.valid_sizes_message())

    def __init__(self, file_path, file_name_no_ext, build_folder_path, info):
        bmp = get_processor(file_path)
        self.__file_path = file_path
        self.__file_name_no_ext = file_name_no_ext
        self.__build_folder_path = build_folder_path
        self.__colors_count = bmp.colors_count

        try:
            height = int(info['height'])
        except KeyError:
            raise ValueError('height field not found in graphics json file: ' + file_name_no_ext + '.json')
        try:
            width = int(info['width'])
        except KeyError:
            width = height

        if bmp.height % height:
            raise ValueError('File height is not divisible by item height: ' + str(bmp.height) + ' - ' + str(height))

        if bmp.width % width:
            raise ValueError('File width is not divisible by item width: ' + str(bmp.width) + ' - ' + str(width))

        self.__graphics = int(bmp.height / height) * int(bmp.width / width)
        self.__shape, self.__size = SpriteItem.shape_and_size(width, height)

        try:
            self.__tiles_compression = info['tiles_compression']
            validate_compression(self.__tiles_compression)
        except KeyError:
            try:
                self.__tiles_compression = info['compression']
                validate_compression(self.__tiles_compression)
            except KeyError:
                self.__tiles_compression = 'none'

        try:
            self.__palette_compression = info['palette_compression']
            validate_compression(self.__palette_compression)
        except KeyError:
            try:
                self.__palette_compression = info['compression']
                validate_compression(self.__palette_compression)
            except KeyError:
                self.__palette_compression = 'none'

    def process(self):
        tiles_compression = self.__tiles_compression
        palette_compression = self.__palette_compression

        if tiles_compression == 'auto':
            tiles_compression, file_size = self.__test_tiles_compression(tiles_compression, 'none', None)
            tiles_compression, file_size = self.__test_tiles_compression(tiles_compression, 'run_length', file_size)
            tiles_compression, file_size = self.__test_tiles_compression(tiles_compression, 'lz77', file_size)

        if palette_compression == 'auto':
            palette_compression, file_size = self.__test_palette_compression(palette_compression, 'none', None)
            palette_compression, file_size = self.__test_palette_compression(palette_compression, 'run_length',
                                                                             file_size)
            palette_compression, file_size = self.__test_palette_compression(palette_compression, 'lz77', file_size)

        self.__execute_command(tiles_compression, palette_compression)
        return self.__write_header(tiles_compression, palette_compression, False)

    def __test_tiles_compression(self, best_tiles_compression, new_tiles_compression, best_file_size):
        self.__execute_command(new_tiles_compression, 'none')
        new_file_size = self.__write_header(new_tiles_compression, 'none', True)

        if best_file_size is None or new_file_size < best_file_size:
            return new_tiles_compression, new_file_size

        return best_tiles_compression, best_file_size

    def __test_palette_compression(self, best_palette_compression, new_palette_compression, best_file_size):
        self.__execute_command('none', new_palette_compression)
        new_file_size = self.__write_header('none', new_palette_compression, True)

        if best_file_size is None or new_file_size < best_file_size:
            return new_palette_compression, new_file_size

        return best_palette_compression, best_file_size

    def __write_header(self, tiles_compression, palette_compression, skip_write):
        name = self.__file_name_no_ext
        grit_file_path = self.__build_folder_path + '/' + name + '_bn_gfx.h'
        header_file_path = self.__build_folder_path + '/bn_sprite_items_' + name + '.h'

        with open(grit_file_path, 'r') as grit_file:
            grit_data = grit_file.read()
            grit_data = grit_data.replace('unsigned int', 'bn::tile')
            grit_data = grit_data.replace('unsigned short', 'bn::color')

            for grit_line in grit_data.splitlines():
                if ' tiles ' in grit_line:
                    for grit_word in grit_line.split():
                        try:
                            tiles_count = int(grit_word)
                            break
                        except ValueError:
                            pass

                if 'Total size:' in grit_line:
                    total_size = int(grit_line.split()[-1])

                    if skip_write:
                        return total_size
                    else:
                        break

        remove_file(grit_file_path)

        if self.__colors_count == 16:
            bpp_mode_label = 'bpp_mode::BPP_4'
        else:
            bpp_mode_label = 'bpp_mode::BPP_8'
            tiles_count *= 2

        grit_data = re.sub(r'Tiles\[([0-9]+)]', 'Tiles[' + str(tiles_count) + ']', grit_data)
        grit_data = re.sub(r'Pal\[([0-9]+)]', 'Pal[' + str(self.__colors_count) + ']', grit_data)

        with open(header_file_path, 'w') as header_file:
            include_guard = 'BN_SPRITE_ITEMS_' + name.upper() + '_H'
            header_file.write('#ifndef ' + include_guard + '\n')
            header_file.write('#define ' + include_guard + '\n')
            header_file.write('\n')
            header_file.write('#include "bn_sprite_item.h"' + '\n')
            header_file.write(grit_data)
            header_file.write('\n')
            header_file.write('namespace bn::sprite_items' + '\n')
            header_file.write('{' + '\n')
            header_file.write('    constexpr inline sprite_item ' + name + '(' +
                              'sprite_shape_size(sprite_shape::' + self.__shape + ', ' +
                              'sprite_size::' + self.__size + '), ' + '\n            ' +
                              'sprite_tiles_item(span<const tile>(' + name + '_bn_gfxTiles, ' +
                              str(tiles_count) + '), ' + bpp_mode_label + ', ' + compression_label(tiles_compression) +
                              ', ' + str(self.__graphics) + '), ' + '\n            ' +
                              'sprite_palette_item(span<const color>(' + name + '_bn_gfxPal, ' +
                              str(self.__colors_count) + '), ' + bpp_mode_label + ', ' +
                              compression_label(palette_compression) + '));\n')
            header_file.write('}' + '\n')
            header_file.write('\n')
            header_file.write('#endif' + '\n')
            header_file.write('\n')

        return total_size, header_file_path

    def __execute_command(self, tiles_compression, palette_compression):
        command = ['grit', self.__file_path, '-gt', '-pe' + str(self.__colors_count)]

        if self.__colors_count == 16:
            command.append('-gB4')
        else:
            command.append('-gB8')

        if tiles_compression == 'lz77':
            command.append('-gzl')
        elif tiles_compression == 'run_length':
            command.append('-gzr')

        if palette_compression == 'lz77':
            command.append('-pzl')
        elif palette_compression == 'run_length':
            command.append('-pzr')

        command.append('-o' + self.__build_folder_path + '/' + self.__file_name_no_ext + '_bn_gfx')
        command = ' '.join(command)

        try:
            subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            raise ValueError('grit call failed (return code ' + str(e.returncode) + '): ' + str(e.output))
