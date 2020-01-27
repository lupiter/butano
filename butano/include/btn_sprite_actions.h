#ifndef BTN_SPRITE_ACTIONS_H
#define BTN_SPRITE_ACTIONS_H

#include "btn_array.h"
#include "btn_vector.h"
#include "btn_optional.h"
#include "btn_sprite_ptr.h"
#include "btn_fixed_point.h"
#include "btn_sprite_item.h"
#include "btn_sprite_tiles_ptr.h"
#include "btn_template_actions.h"

namespace btn
{

// position

class sprite_position_manager
{

public:
    [[nodiscard]] static const fixed_point& get(const sprite_ptr& sprite)
    {
        return sprite.position();
    }

    static void set(const fixed_point& position, sprite_ptr& sprite)
    {
        sprite.set_position(position);
    }
};


class sprite_move_by_action : public by_template_action<sprite_ptr, fixed_point, sprite_position_manager>
{

public:
    template<class SpritePtr>
    sprite_move_by_action(SpritePtr&& sprite, fixed delta_x, fixed delta_y) :
        by_template_action(forward<SpritePtr>(sprite), fixed_point(delta_x, delta_y))
    {
    }

    template<class SpritePtr>
    sprite_move_by_action(SpritePtr&& sprite, const fixed_point& delta_position) :
        by_template_action(forward<SpritePtr>(sprite), delta_position)
    {
    }

    [[nodiscard]] const sprite_ptr& sprite() const
    {
        return value();
    }

    [[nodiscard]] const fixed_point& delta_position() const
    {
        return delta_property();
    }
};


class sprite_move_to_action : public to_template_action<sprite_ptr, fixed_point, sprite_position_manager>
{

public:
    template<class SpritePtr>
    sprite_move_to_action(SpritePtr&& sprite, int duration_frames, fixed final_x, fixed final_y) :
        to_template_action(forward<SpritePtr>(sprite), duration_frames, fixed_point(final_x, final_y))
    {
    }

    template<class SpritePtr>
    sprite_move_to_action(SpritePtr&& sprite, int duration_frames, const fixed_point& final_position) :
        to_template_action(forward<SpritePtr>(sprite), duration_frames, final_position)
    {
    }

    [[nodiscard]] const sprite_ptr& sprite() const
    {
        return value();
    }

    [[nodiscard]] const fixed_point& final_position() const
    {
        return final_property();
    }
};


class sprite_move_loop_action : public loop_template_action<sprite_ptr, fixed_point, sprite_position_manager>
{

public:
    template<class SpritePtr>
    sprite_move_loop_action(SpritePtr&& sprite, int duration_frames, fixed final_x, fixed final_y) :
        loop_template_action(forward<SpritePtr>(sprite), duration_frames, fixed_point(final_x, final_y))
    {
    }

    template<class SpritePtr>
    sprite_move_loop_action(SpritePtr&& sprite, int duration_frames, const fixed_point& final_position) :
        loop_template_action(forward<SpritePtr>(sprite), duration_frames, final_position)
    {
    }

    [[nodiscard]] const sprite_ptr& sprite() const
    {
        return value();
    }

    [[nodiscard]] const fixed_point& final_position() const
    {
        return final_property();
    }
};


// animation

template<size_t Size>
class sprite_animate_action : public action
{
    static_assert(Size);

public:
    template<class SpritePtr>
    [[nodiscard]] static sprite_animate_action once(
            SpritePtr&& sprite, int wait_frames, const sprite_tiles_item& tiles_item,
            const span<const uint16_t>& graphics_indexes)
    {
        return sprite_animate_action(forward<SpritePtr>(sprite), wait_frames, tiles_item, false, graphics_indexes);
    }

    template<class SpritePtr>
    [[nodiscard]] static sprite_animate_action once(
            SpritePtr&& sprite, int wait_frames, const sprite_item& item, const span<const uint16_t>& graphics_indexes)
    {
        return sprite_animate_action(forward<SpritePtr>(sprite), wait_frames, item.tiles_item(), false,
                                     graphics_indexes);
    }

    template<class SpritePtr>
    [[nodiscard]] static sprite_animate_action forever(
            SpritePtr&& sprite, int wait_frames, const sprite_tiles_item& tiles_item,
            const span<const uint16_t>& graphics_indexes)
    {
        return sprite_animate_action(forward<SpritePtr>(sprite), wait_frames, tiles_item, true, graphics_indexes);
    }

    template<class SpritePtr>
    [[nodiscard]] static sprite_animate_action forever(
            SpritePtr&& sprite, int wait_frames, const sprite_item& item, const span<const uint16_t>& graphics_indexes)
    {
        return sprite_animate_action(forward<SpritePtr>(sprite), wait_frames, item.tiles_item(), true,
                                     graphics_indexes);
    }

    void reset()
    {
        _current_graphics_index_index = 0;
        _current_wait_frames = 0;
    }

    void update() override
    {
        BTN_ASSERT(! done(), "Action is done");

        if(_current_wait_frames)
        {
            --_current_wait_frames;
        }
        else
        {
            _current_wait_frames = _wait_frames;
            _sprite.set_tiles(_tiles_item, _graphics_indexes[_current_graphics_index_index]);
            ++_current_graphics_index_index;

            if(_forever && _current_graphics_index_index == _graphics_indexes.size())
            {
                _current_graphics_index_index = 0;
            }
        }
    }

    [[nodiscard]] bool done() const override
    {
        return _current_graphics_index_index == _graphics_indexes.size();
    }

    [[nodiscard]] const sprite_ptr& sprite() const
    {
        return _sprite;
    }

    [[nodiscard]] int wait_frames() const
    {
        return _wait_frames;
    }

    [[nodiscard]] const sprite_tiles_item& tiles_item() const
    {
        return _tiles_item;
    }

    [[nodiscard]] const vector<uint16_t, Size>& graphics_indexes() const
    {
        return _graphics_indexes;
    }

    [[nodiscard]] bool update_forever() const
    {
        return _forever;
    }

private:
    bool _forever = true;
    uint16_t _wait_frames = 0;
    sprite_ptr _sprite;
    sprite_tiles_item _tiles_item;
    vector<uint16_t, Size> _graphics_indexes;
    uint16_t _current_graphics_index_index = 0;
    uint16_t _current_wait_frames = 0;

    template<class SpritePtr>
    sprite_animate_action(SpritePtr&& sprite, int wait_frames, const sprite_tiles_item& tiles_item, bool forever,
                          const span<const uint16_t>& graphics_indexes) :
        _forever(forever),
        _wait_frames(uint16_t(wait_frames)),
        _sprite(forward<SpritePtr>(sprite)),
        _tiles_item(tiles_item)
    {
        BTN_ASSERT(wait_frames >= 0, "Invalid wait frames: ", wait_frames);
        BTN_ASSERT(wait_frames <= numeric_limits<decltype(_wait_frames)>::max(), "Too much wait frames: ", wait_frames);
        BTN_ASSERT(graphics_indexes.size() > 1 && graphics_indexes.size() <= Size, "Invalid graphics indexes: ",
                   graphics_indexes.size());
    }
};

template<class SpritePtr, typename ...Args>
[[nodiscard]] inline auto create_sprite_animate_action_once(
        SpritePtr&& sprite, int wait_frames, const sprite_tiles_item& tiles_item, Args ...graphics_indexes)
{
    return sprite_animate_action<sizeof...(Args)>::once(
                forward<SpritePtr>(sprite), wait_frames, tiles_item,
                array<uint16_t, sizeof...(Args)>{{ uint16_t(graphics_indexes)... }});
}

template<class SpritePtr, typename ...Args>
[[nodiscard]] inline auto create_sprite_animate_action_once(
        SpritePtr&& sprite, int wait_frames, const sprite_item& item, Args ...graphics_indexes)
{
    return sprite_animate_action<sizeof...(Args)>::once(
                forward<SpritePtr>(sprite), wait_frames, item,
                array<uint16_t, sizeof...(Args)>{{ uint16_t(graphics_indexes)... }});
}

template<class SpritePtr, typename ...Args>
[[nodiscard]] inline auto create_sprite_animate_action_forever(
        SpritePtr&& sprite, int wait_frames, const sprite_tiles_item& tiles_item, Args ...graphics_indexes)
{
    return sprite_animate_action<sizeof...(Args)>::forever(
                forward<SpritePtr>(sprite), wait_frames, tiles_item,
                array<uint16_t, sizeof...(Args)>{{ uint16_t(graphics_indexes)... }});
}

template<class SpritePtr, typename ...Args>
[[nodiscard]] inline auto create_sprite_animate_action_forever(
        SpritePtr&& sprite, int wait_frames, const sprite_item& item, Args ...graphics_indexes)
{
    return sprite_animate_action<sizeof...(Args)>::forever(
                forward<SpritePtr>(sprite), wait_frames, item,
                array<uint16_t, sizeof...(Args)>{{ uint16_t(graphics_indexes)... }});
}


// cached animation

template<size_t Size>
class sprite_cached_animate_action : public action
{
    static_assert(Size);

public:
    template<class SpritePtr>
    [[nodiscard]] static sprite_cached_animate_action once(
            SpritePtr&& sprite, int wait_frames, const sprite_tiles_item& tiles_item,
            const span<const uint16_t>& graphics_indexes)
    {
        return sprite_cached_animate_action(forward<SpritePtr>(sprite), wait_frames, tiles_item, false,
                                            graphics_indexes);
    }

    template<class SpritePtr>
    [[nodiscard]] static sprite_cached_animate_action once(
            SpritePtr&& sprite, int wait_frames, const sprite_item& item, const span<const uint16_t>& graphics_indexes)
    {
        return sprite_cached_animate_action(forward<SpritePtr>(sprite), wait_frames, item.tiles_item(), false,
                                            graphics_indexes);
    }

    template<class SpritePtr>
    [[nodiscard]] static sprite_cached_animate_action once(
            SpritePtr&& sprite, int wait_frames, span<sprite_tiles_ptr> tiles_ptrs)
    {
        return sprite_cached_animate_action(forward<SpritePtr>(sprite), wait_frames, false, tiles_ptrs);
    }

    template<class SpritePtr>
    [[nodiscard]] static sprite_cached_animate_action forever(
            SpritePtr&& sprite, int wait_frames, const sprite_tiles_item& tiles_item,
            const span<const uint16_t>& graphics_indexes)
    {
        return sprite_cached_animate_action(forward<SpritePtr>(sprite), wait_frames, tiles_item, true,
                                            graphics_indexes);
    }

    template<class SpritePtr>
    [[nodiscard]] static sprite_cached_animate_action forever(
            SpritePtr&& sprite, int wait_frames, const sprite_item& item, const span<const uint16_t>& graphics_indexes)
    {
        return sprite_cached_animate_action(forward<SpritePtr>(sprite), wait_frames, item.tiles_item(), true,
                                            graphics_indexes);
    }

    template<class SpritePtr>
    [[nodiscard]] static sprite_cached_animate_action forever(
            SpritePtr&& sprite, int wait_frames, span<sprite_tiles_ptr> tiles_ptrs)
    {
        return sprite_cached_animate_action(forward<SpritePtr>(sprite), wait_frames, true, tiles_ptrs);
    }

    void reset()
    {
        _current_tiles_ptr_index = 0;
        _current_wait_frames = 0;
    }

    void update() override
    {
        BTN_ASSERT(! done(), "Action is done");

        if(_current_wait_frames)
        {
            --_current_wait_frames;
        }
        else
        {
            _current_wait_frames = _wait_frames;
            _sprite.set_tiles(_tiles_ptrs[_current_tiles_ptr_index]);
            ++_current_tiles_ptr_index;

            if(_forever && _current_tiles_ptr_index == _tiles_ptrs.size())
            {
                _current_tiles_ptr_index = 0;
            }
        }
    }

    [[nodiscard]] bool done() const override
    {
        return _current_tiles_ptr_index == _tiles_ptrs.size();
    }

    [[nodiscard]] const sprite_ptr& sprite() const
    {
        return _sprite;
    }

    [[nodiscard]] int wait_frames() const
    {
        return _wait_frames;
    }

    [[nodiscard]] const vector<sprite_tiles_ptr, Size>& tiles_ptrs() const
    {
        return _tiles_ptrs;
    }

    [[nodiscard]] bool update_forever() const
    {
        return _forever;
    }

private:
    bool _forever = true;
    uint16_t _wait_frames = 0;
    sprite_ptr _sprite;
    vector<sprite_tiles_ptr, Size> _tiles_ptrs;
    uint16_t _current_tiles_ptr_index = 0;
    uint16_t _current_wait_frames = 0;

    template<class SpritePtr>
    sprite_cached_animate_action(SpritePtr&& sprite, int wait_frames, const sprite_tiles_item& tiles_item,
                                 bool forever, const span<const uint16_t>& graphics_indexes) :
        _forever(forever),
        _wait_frames(uint16_t(wait_frames)),
        _sprite(forward<SpritePtr>(sprite))
    {
        BTN_ASSERT(wait_frames >= 0, "Invalid wait frames: ", wait_frames);
        BTN_ASSERT(wait_frames <= numeric_limits<decltype(_wait_frames)>::max(), "Too much wait frames: ", wait_frames);
        BTN_ASSERT(graphics_indexes.size() > 1 && graphics_indexes.size() <= Size, "Invalid graphics indexes: ",
                   graphics_indexes.size());

        for(int graphics_index : graphics_indexes)
        {
            optional<sprite_tiles_ptr> tiles_ptr = tiles_item.create_tiles(
                        graphics_index, create_mode::FIND_OR_CREATE);
            BTN_ASSERT(tiles_ptr, "Tiles create failed");

            _tiles_ptrs.push_back(move(*tiles_ptr));
        }
    }

    template<class SpritePtr>
    sprite_cached_animate_action(SpritePtr&& sprite, int wait_frames, bool forever, span<sprite_tiles_ptr> tiles_ptrs) :
        _forever(forever),
        _wait_frames(uint16_t(wait_frames)),
        _sprite(forward<SpritePtr>(sprite))
    {
        BTN_ASSERT(wait_frames >= 0, "Invalid wait frames: ", wait_frames);
        BTN_ASSERT(wait_frames <= numeric_limits<decltype(_wait_frames)>::max(), "Too much wait frames: ", wait_frames);
        BTN_ASSERT(tiles_ptrs.size() > 1 && tiles_ptrs.size() <= Size, "Invalid tiles ptrs: ", tiles_ptrs.size());

        for(sprite_tiles_ptr& tiles_ptr : tiles_ptrs)
        {
            _tiles_ptrs.push_back(move(tiles_ptr));
        }
    }
};

template<class SpritePtr, typename ...Args>
[[nodiscard]] inline auto create_sprite_cached_animate_action_once(
        SpritePtr&& sprite, int wait_frames, const sprite_tiles_item& tiles_item, Args ...graphics_indexes)
{
    return sprite_cached_animate_action<sizeof...(Args)>::once(
                forward<SpritePtr>(sprite), wait_frames, tiles_item,
                array<uint16_t, sizeof...(Args)>{{ uint16_t(graphics_indexes)... }});
}

template<class SpritePtr, typename ...Args>
[[nodiscard]] inline auto create_sprite_cached_animate_action_once(
        SpritePtr&& sprite, int wait_frames, const sprite_item& item, Args ...graphics_indexes)
{
    return sprite_cached_animate_action<sizeof...(Args)>::once(
                forward<SpritePtr>(sprite), wait_frames, item,
                array<uint16_t, sizeof...(Args)>{{ uint16_t(graphics_indexes)... }});
}

template<class SpritePtr, typename ...Args>
[[nodiscard]] inline auto create_sprite_cached_animate_action_forever(
        SpritePtr&& sprite, int wait_frames, const sprite_tiles_item& tiles_item, Args ...graphics_indexes)
{
    return sprite_cached_animate_action<sizeof...(Args)>::forever(
                forward<SpritePtr>(sprite), wait_frames, tiles_item,
                array<uint16_t, sizeof...(Args)>{{ uint16_t(graphics_indexes)... }});
}

template<class SpritePtr, typename ...Args>
[[nodiscard]] inline auto create_sprite_cached_animate_action_forever(
        SpritePtr&& sprite, int wait_frames, const sprite_item& item, Args ...graphics_indexes)
{
    return sprite_cached_animate_action<sizeof...(Args)>::forever(
                forward<SpritePtr>(sprite), wait_frames, item,
                array<uint16_t, sizeof...(Args)>{{ uint16_t(graphics_indexes)... }});
}

}

#endif
