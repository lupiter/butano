
import subprocess
import re

from util import get_processor, remove_file, compression_label, validate_compression

class SpriteTilesItem:

    @staticmethod
    def valid_sizes_message():
        return ' (valid sprite sizes: 8x8, 16x16, 32x32, 64x64, 16x8, 32x8, 32x16, 8x16, 8x32, 16x32, 32x64)'

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

        if bmp.height % height:
            raise ValueError('File height is not divisible by item height: ' + str(bmp.height) + ' - ' + str(height))

        self.__graphics = int(bmp.height / height)
        self.__shape, self.__size = SpriteItem.shape_and_size(bmp.width, height)

        try:
            self.__compression = info['compression']
            validate_compression(self.__compression)
        except KeyError:
            self.__compression = 'none'

    def process(self):
        compression = self.__compression

        if compression == 'auto':
            compression, file_size = self.__test_compression(compression, 'none', None)
            compression, file_size = self.__test_compression(compression, 'run_length', file_size)
            compression, file_size = self.__test_compression(compression, 'lz77', file_size)

        self.__execute_command(compression)
        return self.__write_header(compression, False)

    def __test_compression(self, best_compression, new_compression, best_file_size):
        self.__execute_command(new_compression)
        new_file_size = self.__write_header(new_compression, True)

        if best_file_size is None or new_file_size < best_file_size:
            return new_compression, new_file_size

        return best_compression, best_file_size

    def __write_header(self, compression, skip_write):
        name = self.__file_name_no_ext
        grit_file_path = self.__build_folder_path + '/' + name + '_bn_gfx.h'
        header_file_path = self.__build_folder_path + '/bn_sprite_tiles_items_' + name + '.h'

        with open(grit_file_path, 'r') as grit_file:
            grit_data = grit_file.read()
            grit_data = grit_data.replace('unsigned int', 'bn::tile')

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

        with open(header_file_path, 'w') as header_file:
            include_guard = 'BN_SPRITE_TILES_ITEMS_' + name.upper() + '_H'
            header_file.write('#ifndef ' + include_guard + '\n')
            header_file.write('#define ' + include_guard + '\n')
            header_file.write('\n')
            header_file.write('#include "bn_sprite_tiles_item.h"' + '\n')
            header_file.write('#include "bn_sprite_shape_size.h"' + '\n')
            header_file.write(grit_data)
            header_file.write('\n')
            header_file.write('namespace bn::sprite_tiles_items' + '\n')
            header_file.write('{' + '\n')
            header_file.write('    constexpr inline sprite_tiles_item ' + name + '(span<const tile>(' +
                              name + '_bn_gfxTiles, ' + str(tiles_count) + '), ' + '\n            ' +
                              bpp_mode_label + ', ' + compression_label(compression) + ', ' +
                              str(self.__graphics) + ');' + '\n')
            header_file.write('\n')
            header_file.write('    constexpr inline sprite_shape_size ' + name +
                              '_shape_size(sprite_shape::' + self.__shape + ', ' +
                              'sprite_size::' + self.__size + ');' + '\n')
            header_file.write('}' + '\n')
            header_file.write('\n')
            header_file.write('#endif' + '\n')
            header_file.write('\n')

        return total_size, header_file_path

    def __execute_command(self, compression):
        command = ['grit', self.__file_path, '-gt', '-p!']

        if self.__colors_count == 16:
            command.append('-gB4')
        else:
            command.append('-gB8')

        if compression == 'lz77':
            command.append('-gzl')
        elif compression == 'run_length':
            command.append('-gzr')

        command.append('-o' + self.__build_folder_path + '/' + self.__file_name_no_ext + '_bn_gfx')
        command = ' '.join(command)

        try:
            subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            raise ValueError('grit call failed (return code ' + str(e.returncode) + '): ' + str(e.output))
