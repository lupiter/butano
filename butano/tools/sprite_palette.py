
import subprocess
import re

from util import get_processor, remove_file, compression_label, validate_compression

class SpritePaletteItem:

    def __init__(self, file_path, file_name_no_ext, build_folder_path, info):
        bmp = get_processor(file_path)
        self.__file_path = file_path
        self.__file_name_no_ext = file_name_no_ext
        self.__build_folder_path = build_folder_path

        try:
            colors_count = int(info['colors_count'])

            if colors_count < 1 or colors_count > 256:
                raise ValueError('Invalid colors count: ' + str(colors_count))

            extra_colors = colors_count % 16

            if extra_colors > 0:
                colors_count += 16 - extra_colors

            self.__colors_count = colors_count
        except KeyError:
            self.__colors_count = bmp.colors_count

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
        header_file_path = self.__build_folder_path + '/bn_sprite_palette_items_' + name + '.h'

        with open(grit_file_path, 'r') as grit_file:
            grit_data = grit_file.read()
            grit_data = grit_data.replace('unsigned short', 'bn::color')

            for grit_line in grit_data.splitlines():
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

        grit_data = re.sub(r'Pal\[([0-9]+)]', 'Pal[' + str(self.__colors_count) + ']', grit_data)

        with open(header_file_path, 'w') as header_file:
            include_guard = 'BN_SPRITE_PALETTE_ITEMS_' + name.upper() + '_H'
            header_file.write('#ifndef ' + include_guard + '\n')
            header_file.write('#define ' + include_guard + '\n')
            header_file.write('\n')
            header_file.write('#include "bn_sprite_palette_item.h"' + '\n')
            header_file.write(grit_data)
            header_file.write('\n')
            header_file.write('namespace bn::sprite_palette_items' + '\n')
            header_file.write('{' + '\n')
            header_file.write('    constexpr inline sprite_palette_item ' + name + '(' +
                              'span<const color>(' + name + '_bn_gfxPal, ' +
                              str(self.__colors_count) + '), ' + '\n            ' +
                              bpp_mode_label + ', ' + compression_label(compression) + ');' + '\n')
            header_file.write('}' + '\n')
            header_file.write('\n')
            header_file.write('#endif' + '\n')
            header_file.write('\n')

        return total_size, header_file_path

    def __execute_command(self, compression):
        command = ['grit', self.__file_path, '-g!', '-pe' + str(self.__colors_count)]

        if compression == 'lz77':
            command.append('-pzl')
        elif compression == 'run_length':
            command.append('-pzr')

        command.append('-o' + self.__build_folder_path + '/' + self.__file_name_no_ext + '_bn_gfx')
        command = ' '.join(command)

        try:
            subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            raise ValueError('grit call failed (return code ' + str(e.returncode) + '): ' + str(e.output))
