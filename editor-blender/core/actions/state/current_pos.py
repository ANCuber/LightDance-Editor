import bpy

from ....properties.types import PositionPropertyType
from ...states import state
from ...utils.algorithms import binary_search


def calculate_current_pos_index() -> int:
    if not bpy.context:
        return 0  # Won't actually happen
    return binary_search(state.pos_start_record, bpy.context.scene.frame_current)


def update_current_pos_by_index():
    """Update current position by index and set ld_position"""
    if not bpy.context:
        return
    index = state.current_pos_index

    pos_map = state.pos_map
    pos_id = state.pos_record[index]

    current_pos_map = pos_map.get(pos_id)
    if current_pos_map is None:
        return

    state.current_pos = current_pos_map.pos
    current_pos = state.current_pos

    if index == len(state.pos_record) - 1:
        for dancer_name in state.dancer_names:
            dancer_pos = current_pos.get(dancer_name)
            if dancer_pos is None:
                continue

            obj: bpy.types.Object | None = bpy.data.objects.get(dancer_name)
            if obj is not None:
                ld_position: PositionPropertyType = getattr(obj, "ld_position")
                # This also sets the actual location by update handler
                ld_position.location = (
                    dancer_pos.location.x,
                    dancer_pos.location.y,
                    dancer_pos.location.z,
                )
                ld_position.rotation = (
                    dancer_pos.rotation.rx,
                    dancer_pos.rotation.ry,
                    dancer_pos.rotation.rz,
                )

    else:
        next_pos_id = state.pos_record[index + 1]
        next_pos_map = pos_map.get(next_pos_id)
        if next_pos_map is None:
            return

        next_pos = next_pos_map.pos

        frame = bpy.context.scene.frame_current
        current_start = current_pos_map.start
        next_start = next_pos_map.start

        for dancer_name in state.dancer_names:
            dancer_pos = current_pos.get(dancer_name)
            next_dancer_pos = next_pos.get(dancer_name)
            if dancer_pos is None or next_dancer_pos is None:
                continue

            obj: bpy.types.Object | None = bpy.data.objects.get(dancer_name)
            ratio = (frame - current_start) / (next_start - current_start)
            if obj is not None:
                ld_position: PositionPropertyType = getattr(obj, "ld_position")
                # This also sets the actual location by update handler
                ld_position.location = (  # NOTE: Linear interpolation
                    dancer_pos.location.x
                    + (next_dancer_pos.location.x - dancer_pos.location.x) * ratio,
                    dancer_pos.location.y
                    + (next_dancer_pos.location.y - dancer_pos.location.y) * ratio,
                    dancer_pos.location.z
                    + (next_dancer_pos.location.z - dancer_pos.location.z) * ratio,
                )
