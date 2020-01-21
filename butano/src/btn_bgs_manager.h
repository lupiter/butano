#ifndef BTN_BGS_MANAGER_H
#define BTN_BGS_MANAGER_H

#include "btn_limits.h"
#include "btn_optional_fwd.h"

namespace btn
{

class size;
class bg_builder;
class bg_map_ptr;
class fixed_point;
class bg_tiles_ptr;
class bg_palette_ptr;

namespace bgs_manager
{
    [[nodiscard]] BTN_CODE_CONST int max_priority();

    [[nodiscard]] optional<int> create(bg_builder&& builder);

    void increase_usages(int id);

    void decrease_usages(int id);

    [[nodiscard]] size dimensions(int id);

    [[nodiscard]] const bg_tiles_ptr& tiles_ptr(int id);

    void set_tiles_ptr(int id, bg_tiles_ptr tiles_ptr);

    [[nodiscard]] const bg_map_ptr& map_ptr(int id);

    void set_map_ptr(int id, bg_map_ptr map_ptr);

    [[nodiscard]] const bg_palette_ptr& palette_ptr(int id);

    void set_palette_ptr(int id, bg_palette_ptr palette_ptr);

    [[nodiscard]] const fixed_point& position(int id);

    void set_position(int id, const fixed_point& position);

    [[nodiscard]] int priority(int id);

    void set_priority(int id, int priority);

    [[nodiscard]] bool mosaic_enabled(int id);

    void set_mosaic_enabled(int id, bool mosaic_enabled);

    [[nodiscard]] bool visible(int id);

    void set_visible(int id, bool visible);

    [[nodiscard]] bool ignore_camera(int id);

    void set_ignore_camera(int id, bool ignore_camera);

    void update_camera();

    void commit();
}

}

#endif