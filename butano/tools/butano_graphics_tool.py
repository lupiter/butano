"""
Copyright (c) 2020-2022 Gustavo Valiente gustavo.valiente@protonmail.com
zlib License, see LICENSE file.
"""

import os
import json
import string
import sys
from multiprocessing import Pool

from file_info import FileInfo
from fixed_bg import FixedBgItem
from affine_bg import AffineBgItem
from bg_palette import BgPaletteItem
from regular_bg import RegularBgItem
from sprite_palette import SpritePaletteItem
from sprite_tiles import SpriteTilesItem
from sprite import SpriteItem


class GraphicsFileInfo:

    def __init__(self, json_file_path, file_path, file_name, file_name_no_ext, file_info_path):
        self.__json_file_path = json_file_path
        self.__file_path = file_path
        self.__file_name = file_name
        self.__file_name_no_ext = file_name_no_ext
        self.__file_info_path = file_info_path

    def print_file_name(self):
        print(self.__file_name)

    def process(self, build_folder_path):
        try:
            try:
                with open(self.__json_file_path) as json_file:
                    info = json.load(json_file)
            except Exception as exception:
                raise ValueError(self.__json_file_path + ' graphics json file parse failed: ' + str(exception))

            try:
                graphics_type = str(info['type'])
            except KeyError:
                raise ValueError('type field not found in graphics json file: ' + self.__json_file_path)

            if graphics_type == 'sprite':
                item = SpriteItem(self.__file_path, self.__file_name_no_ext, build_folder_path, info)
            elif graphics_type == 'sprite_tiles':
                item = SpriteTilesItem(self.__file_path, self.__file_name_no_ext, build_folder_path, info)
            elif graphics_type == 'sprite_palette':
                item = SpritePaletteItem(self.__file_path, self.__file_name_no_ext, build_folder_path, info)
            elif graphics_type == 'regular_bg':
                item = RegularBgItem(self.__file_path, self.__file_name_no_ext, build_folder_path, info)
            elif graphics_type == 'fixed_bg':
                item = FixedBgItem(self.__file_path, self.__file_name_no_ext, build_folder_path, info)
            elif graphics_type == 'affine_bg':
                item = AffineBgItem(self.__file_path, self.__file_name_no_ext, build_folder_path, info)
            elif graphics_type == 'bg_palette':
                item = BgPaletteItem(self.__file_path, self.__file_name_no_ext, build_folder_path, info)
            else:
                raise ValueError('Unknown graphics type "' + graphics_type +
                                 '" found in graphics json file: ' + self.__json_file_path)

            total_size, header_file_path = item.process()

            with open(self.__file_info_path, 'w') as file_info:
                file_info.write('')

            return [self.__file_name, header_file_path, total_size]
        except Exception as exc:
            return [self.__file_name, exc]


class GraphicsFileInfoProcessor:

    def __init__(self, build_folder_path):
        self.__build_folder_path = build_folder_path

    def __call__(self, graphics_file_info):
        return graphics_file_info.process(self.__build_folder_path)


def list_graphics_file_infos(graphics_folder_paths, build_folder_path):
    graphics_folder_path_list = graphics_folder_paths.split(' ')
    graphics_file_infos = []
    file_names_set = set()

    for graphics_folder_path in graphics_folder_path_list:
        graphics_file_names = os.listdir(graphics_folder_path)

        for graphics_file_name in graphics_file_names:
            graphics_file_path = graphics_folder_path + '/' + graphics_file_name

            if os.path.isfile(graphics_file_path) and FileInfo.validate(graphics_file_name):
                graphics_file_name_split = os.path.splitext(graphics_file_name)
                graphics_file_name_no_ext = graphics_file_name_split[0]
                graphics_file_name_ext = graphics_file_name_split[1]

                if graphics_file_name_ext == '.bmp' or graphics_file_name_ext == '.png':
                    if graphics_file_name_no_ext in file_names_set:
                        raise ValueError('There\'s two or more graphics files with the same name: ' +
                                         graphics_file_name_no_ext)

                    file_names_set.add(graphics_file_name_no_ext)
                    json_file_path = graphics_folder_path + '/' + graphics_file_name_no_ext + '.json'

                    if not os.path.isfile(json_file_path):
                        raise ValueError('Graphics json file not found: ' + json_file_path)

                    file_info_path = build_folder_path + '/_bn_' + graphics_file_name_no_ext + '_file_info.txt'

                    if not os.path.exists(file_info_path):
                        build = True
                    else:
                        file_info_mtime = os.path.getmtime(file_info_path)
                        graphics_file_mtime = os.path.getmtime(graphics_file_path)

                        if file_info_mtime < graphics_file_mtime:
                            build = True
                        else:
                            json_file_mtime = os.path.getmtime(json_file_path)
                            build = file_info_mtime < json_file_mtime

                    if build:
                        graphics_file_infos.append(GraphicsFileInfo(
                            json_file_path, graphics_file_path, graphics_file_name, graphics_file_name_no_ext,
                            file_info_path))

    return graphics_file_infos


def process_graphics(graphics_folder_paths, build_folder_path):
    graphics_file_infos = list_graphics_file_infos(graphics_folder_paths, build_folder_path)

    if len(graphics_file_infos) > 0:
        for graphics_file_info in graphics_file_infos:
            graphics_file_info.print_file_name()

        sys.stdout.flush()

        pool = Pool()
        process_results = pool.map(GraphicsFileInfoProcessor(build_folder_path), graphics_file_infos)
        pool.close()

        total_size = 0
        process_excs = []

        for process_result in process_results:
            if len(process_result) == 3:
                file_size = process_result[2]
                total_size += file_size
                print('    ' + str(process_result[0]) + ' item header written in ' + str(process_result[1]) +
                      ' (graphics size: ' + str(file_size) + ' bytes)')
            else:
                process_excs.append(process_result)

        sys.stdout.flush()

        if len(process_excs) > 0:
            for process_exc in process_excs:
                sys.stderr.write(str(process_exc[0]) + ' error: ' + str(process_exc[1]) + '\n')

            exit(-1)

        print('    ' + 'Processed graphics size: ' + str(total_size) + ' bytes')
