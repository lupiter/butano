/*
 * Copyright (c) 2020-2022 Gustavo Valiente gustavo.valiente@protonmail.com
 * zlib License, see LICENSE file.
 */

#include "../include/bn_hw_sram.h"

namespace bn::hw::sram
{

void _copy(const uint8_t* source, int size, uint8_t* destination)
{
    // This code *maybe* should be in WRAM:
    // http://problemkaputt.de/gbatek.htm#gbacartbackupsramfram (Reading and Writing section)

    volatile const uint8_t* source_ptr = source;
    volatile uint8_t* destination_ptr = destination;

    for(int index = 0; index < size; ++index)
    {
        destination_ptr[index] = source_ptr[index];
    }
}

void _fill(uint8_t value, int size, uint8_t* destination)
{
    // This code *maybe* should be in WRAM:
    // http://problemkaputt.de/gbatek.htm#gbacartbackupsramfram (Reading and Writing section)

    volatile uint8_t* destination_ptr = destination;

    for(int index = 0; index < size; ++index)
    {
        destination_ptr[index] = value;
    }
}

}
