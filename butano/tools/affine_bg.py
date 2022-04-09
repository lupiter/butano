
import subprocess
import re

from util import get_processor, remove_file, compression_label, validate_compression

class AffineBgItem:

    def __init__(self, file_path, file_name_no_ext, build_folder_path, info):
        bmp = get_processor(file_path)
        self.__file_path = file_path
        self.__file_name_no_ext = file_name_no_ext
        self.__build_folder_path = build_folder_path

        width = bmp.width
        height = bmp.height

        if width != 128 and width % 256 != 0:
            raise ValueError('Affine BGs width must be 128 or divisible by 256: ' + str(width))

        if height != 128 and height % 256 != 0:
            raise ValueError('Affine BGs height must be 128 or divisible by 256: ' + str(height))

        self.__width = int(width / 8)
        self.__height = int(height / 8)

        try:
            self.__repeated_tiles_reduction = bool(info['repeated_tiles_reduction'])
        except KeyError:
            self.__repeated_tiles_reduction = True

        try:
            palette_item = str(info['palette_item'])

            if len(palette_item) == 0:
                raise ValueError('Empty palette item')

            if palette_item[0] not in string.ascii_lowercase:
                raise ValueError('Invalid palette item: ' + palette_item +
                                 ' (invalid character: \'' + palette_item[0] + '\')')

            valid_characters = '_%s%s' % (string.ascii_lowercase, string.digits)

            for palette_item_character in palette_item:
                if palette_item_character not in valid_characters:
                    raise ValueError('Invalid palette item: ' + palette_item +
                                     ' (invalid character: \'' + palette_item_character + '\')')

            self.__palette_item = palette_item
            self.__colors_count = 0
        except KeyError:
            self.__palette_item = None
            self.__colors_count = bmp.colors_count

        try:
            self.__tiles_compression = info['tiles_compression']
            validate_compression(self.__tiles_compression)
        except KeyError:
            try:
                self.__tiles_compression = info['compression']
                validate_compression(self.__tiles_compression)
            except KeyError:
                self.__tiles_compression = 'none'

        if self.__palette_item is not None:
            self.__palette_compression = 'none'
        else:
            try:
                self.__palette_compression = info['palette_compression']
                validate_compression(self.__palette_compression)
            except KeyError:
                try:
                    self.__palette_compression = info['compression']
                    validate_compression(self.__palette_compression)
                except KeyError:
                    self.__palette_compression = 'none'

        try:
            self.__map_compression = info['map_compression']
            validate_compression(self.__map_compression)
        except KeyError:
            try:
                self.__map_compression = info['compression']
                validate_compression(self.__map_compression)
            except KeyError:
                self.__map_compression = 'none'

    def process(self):
        tiles_compression = self.__tiles_compression
        palette_compression = self.__palette_compression
        map_compression = self.__map_compression

        if tiles_compression == 'auto':
            tiles_compression, file_size = self.__test_tiles_compression(tiles_compression, 'none', None)
            tiles_compression, file_size = self.__test_tiles_compression(tiles_compression, 'run_length', file_size)
            tiles_compression, file_size = self.__test_tiles_compression(tiles_compression, 'lz77', file_size)

        if palette_compression == 'auto':
            palette_compression, file_size = self.__test_palette_compression(palette_compression, 'none', None)
            palette_compression, file_size = self.__test_palette_compression(palette_compression, 'run_length',
                                                                             file_size)
            palette_compression, file_size = self.__test_palette_compression(palette_compression, 'lz77', file_size)

        if map_compression == 'auto':
            map_compression, file_size = self.__test_map_compression(map_compression, 'none', None)
            map_compression, file_size = self.__test_map_compression(map_compression, 'run_length', file_size)
            map_compression, file_size = self.__test_map_compression(map_compression, 'lz77', file_size)

        self.__execute_command(tiles_compression, palette_compression, map_compression)
        return self.__write_header(tiles_compression, palette_compression, map_compression, False)

    def __test_tiles_compression(self, best_tiles_compression, new_tiles_compression, best_file_size):
        self.__execute_command(new_tiles_compression, 'none', 'none')
        new_file_size = self.__write_header(new_tiles_compression, 'none', 'none', True)

        if best_file_size is None or new_file_size < best_file_size:
            return new_tiles_compression, new_file_size

        return best_tiles_compression, best_file_size

    def __test_palette_compression(self, best_palette_compression, new_palette_compression, best_file_size):
        self.__execute_command('none', new_palette_compression, 'none')
        new_file_size = self.__write_header('none', new_palette_compression, 'none', True)

        if best_file_size is None or new_file_size < best_file_size:
            return new_palette_compression, new_file_size

        return best_palette_compression, best_file_size

    def __test_map_compression(self, best_map_compression, new_map_compression, best_file_size):
        self.__execute_command('none', 'none', new_map_compression)
        new_file_size = self.__write_header('none', 'none', new_map_compression, True)

        if best_file_size is None or new_file_size < best_file_size:
            return new_map_compression, new_file_size

        return best_map_compression, best_file_size

    def __write_header(self, tiles_compression, palette_compression, map_compression, skip_write):
        name = self.__file_name_no_ext
        grit_file_path = self.__build_folder_path + '/' + name + '_bn_gfx.h'
        header_file_path = self.__build_folder_path + '/bn_affine_bg_items_' + name + '.h'

        with open(grit_file_path, 'r') as grit_file:
            grit_data = grit_file.read()
            grit_data = grit_data.replace('unsigned int', 'bn::tile', 1)
            grit_data = grit_data.replace('unsigned char', 'bn::affine_bg_map_cell', 1)

            if self.__palette_item is None:
                grit_data = grit_data.replace('unsigned short', 'bn::color', 1)

            for grit_line in grit_data.splitlines():
                if ' tiles ' in grit_line:
                    for grit_word in grit_line.split():
                        try:
                            tiles_count = int(grit_word)
                            break
                        except ValueError:
                            pass

                    if tiles_count > 256:
                        raise ValueError('Affine BGs with more than 256 tiles not supported: ' + str(tiles_count))

                if 'Total size:' in grit_line:
                    total_size = int(grit_line.split()[-1])

                    if skip_write:
                        return total_size
                    else:
                        break

        remove_file(grit_file_path)

        tiles_count *= 2
        grit_data = re.sub(r'Tiles\[([0-9]+)]', 'Tiles[' + str(tiles_count) + ']', grit_data)
        grit_data = re.sub(r'Pal\[([0-9]+)]', 'Pal[' + str(self.__colors_count) + ']', grit_data)

        with open(header_file_path, 'w') as header_file:
            include_guard = 'BN_AFFINE_BG_ITEMS_' + name.upper() + '_H'
            header_file.write('#ifndef ' + include_guard + '\n')
            header_file.write('#define ' + include_guard + '\n')
            header_file.write('\n')
            header_file.write('#include "bn_affine_bg_item.h"' + '\n')
            header_file.write(grit_data)
            header_file.write('\n')

            if self.__palette_item is not None:
                header_file.write('#include "bn_bg_palette_items_' + self.__palette_item + '.h"' + '\n')
                header_file.write('\n')

            header_file.write('namespace bn::affine_bg_items' + '\n')
            header_file.write('{' + '\n')
            header_file.write('    constexpr inline affine_bg_item ' + name + '(' + '\n            ' +
                              'affine_bg_tiles_item(span<const tile>(' + name + '_bn_gfxTiles, ' +
                              str(tiles_count) + '), ' + compression_label(tiles_compression) +
                              '), ' + '\n            ')

            if self.__palette_item is None:
                header_file.write('bg_palette_item(span<const color>(' + name + '_bn_gfxPal, ' +
                                  str(self.__colors_count) + '), bpp_mode::BPP_8, ' +
                                  compression_label(palette_compression) + '),' + '\n            ')
            else:
                header_file.write('bn::bg_palette_items::' + self.__palette_item + ',' + '\n            ')

            header_file.write('affine_bg_map_item(' + name + '_bn_gfxMap[0], ' +
                              'size(' + str(self.__width) + ', ' + str(self.__height) + '), ' +
                              compression_label(map_compression) + '));' + '\n')
            header_file.write('}' + '\n')
            header_file.write('\n')
            header_file.write('#endif' + '\n')
            header_file.write('\n')

        return total_size, header_file_path

    def __execute_command(self, tiles_compression, palette_compression, map_compression):
        command = ['grit', self.__file_path, '-gB8', '-mLa', '-mu8']

        if self.__colors_count > 0:
            command.append('-pe' + str(self.__colors_count))
        else:
            command.append('-p!')

        if self.__repeated_tiles_reduction:
            command.append('-mRt')
        else:
            command.append('-mR!')

        if tiles_compression == 'lz77':
            command.append('-gzl')
        elif tiles_compression == 'run_length':
            command.append('-gzr')

        if palette_compression == 'lz77':
            command.append('-pzl')
        elif palette_compression == 'run_length':
            command.append('-pzr')

        if map_compression == 'lz77':
            command.append('-mzl')
        elif map_compression == 'run_length':
            command.append('-mzr')

        command.append('-o' + self.__build_folder_path + '/' + self.__file_name_no_ext + '_bn_gfx')
        command = ' '.join(command)

        try:
            subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            raise ValueError('grit call failed (return code ' + str(e.returncode) + '): ' + str(e.output))
