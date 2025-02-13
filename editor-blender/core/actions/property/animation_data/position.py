"""
position.py

- This file contains functions to update position keyframes in Blender.
"""

from typing import cast

import bpy

from .....properties.types import RevisionPropertyItemType
from ....models import MapID, PosMapElement
from ....states import state
from ....utils.convert import PosModifyAnimationData
from .utils import ensure_action, ensure_curve, get_keyframe_points


def reset_pos_frames():
    if not bpy.context:
        return
    scene = bpy.context.scene
    action = ensure_action(scene, "SceneAction")
    curve = ensure_curve(
        action,
        "ld_pos_frame",
        keyframe_points=len(state.pos_start_record),
        clear=True,
    )

    _, kpoints_list = get_keyframe_points(curve)
    for i, start in enumerate(state.pos_start_record):
        point = kpoints_list[i]
        point.co = start, start

        point.interpolation = "LINEAR"
        point.select_control_point = False


def reset_pos_rev(sorted_pos_map: list[tuple[MapID, PosMapElement]]):
    if not bpy.context:
        return
    getattr(bpy.context.scene, "ld_pos_rev").clear()
    for _, (id, pos_map_element) in enumerate(sorted_pos_map):
        frame_start = pos_map_element.start
        rev = pos_map_element.rev

        pos_rev_item: RevisionPropertyItemType = getattr(
            bpy.context.scene, "ld_pos_rev"
        ).add()

        pos_rev_item.data = rev.data if rev else -1
        pos_rev_item.meta = rev.meta if rev else -1

        pos_rev_item.frame_id = id
        pos_rev_item.frame_start = frame_start


def update_pos_frames(
    delete_frames: list[int],
    update_frames: list[tuple[int, int]],
    add_frames: list[int],
):
    if not bpy.context:
        return
    scene = bpy.context.scene
    action = ensure_action(scene, "SceneAction")

    curve = ensure_curve(action, "ld_pos_frame")
    _, kpoints_list = get_keyframe_points(curve)

    # Delete frames
    kpoints_len = len(kpoints_list)
    curve_index = 0

    for old_start in delete_frames:
        while (
            curve_index < kpoints_len
            and int(kpoints_list[curve_index].co[0]) != old_start
        ):
            curve_index += 1

        if curve_index < kpoints_len:
            point = kpoints_list[curve_index]
            curve.keyframe_points.remove(point)

    # Update frames
    kpoints_len = len(kpoints_list)
    curve_index = 0
    points_to_update: list[tuple[int, bpy.types.Keyframe]] = []

    for old_start, frame_start in update_frames:
        while (
            curve_index < kpoints_len
            and int(kpoints_list[curve_index].co[0]) != old_start
        ):
            curve_index += 1

        if curve_index < kpoints_len:
            point = kpoints_list[curve_index]
            points_to_update.append((frame_start, point))

    for frame_start, point in points_to_update:
        point.co = frame_start, frame_start

    # Add frames
    kpoints_len = len(kpoints_list)
    curve.keyframe_points.add(len(add_frames))

    for i, frame_start in enumerate(add_frames):
        point = kpoints_list[kpoints_len + i]
        point.co = frame_start, frame_start
        point.interpolation = "LINEAR"
        point.select_control_point = False

    curve.keyframe_points.sort()


"""
setups & update colormap(===setups)
"""


def init_pos_keyframes_from_state(dancers_reset: list[bool] | None = None):
    if not bpy.context:
        return
    data_objects = cast(dict[str, bpy.types.Object], bpy.data.objects)

    pos_map = state.pos_map
    pos_frame_number = len(pos_map)

    sorted_pos_map = sorted(pos_map.items(), key=lambda item: item[1].start)

    for i, (id, pos_map_element) in enumerate(sorted_pos_map):
        frame_start = pos_map_element.start
        pos_status = pos_map_element.pos

        for dancer_name, pos in pos_status.items():
            dancer_index = state.dancer_part_index_map[dancer_name].index
            if dancers_reset and not dancers_reset[dancer_index]:
                continue

            dancer_location = (pos.x, pos.y, pos.z)

            dancer_obj = data_objects[dancer_name]
            action = ensure_action(dancer_obj, dancer_name + "Action")

            for d in range(3):
                curve = ensure_curve(
                    action,
                    "location",
                    index=d,
                    keyframe_points=pos_frame_number,
                    clear=i == 0,
                )

                _, kpoints_list = get_keyframe_points(curve)
                point = kpoints_list[i]
                point.co = frame_start, dancer_location[d]

                point.interpolation = "LINEAR"

                point.select_control_point = False

        # insert fake frame
        scene = bpy.context.scene
        action = ensure_action(scene, "SceneAction")

        curve = ensure_curve(
            action, "ld_pos_frame", keyframe_points=pos_frame_number, clear=i == 0
        )
        _, kpoints_list = get_keyframe_points(curve)

        point = kpoints_list[i]
        point.co = frame_start, frame_start
        point.interpolation = "CONSTANT"

        point.select_control_point = False

        # set revision
        rev = pos_map_element.rev

        pos_rev_item: RevisionPropertyItemType = getattr(
            bpy.context.scene, "ld_pos_rev"
        ).add()

        pos_rev_item.data = rev.data if rev else -1
        pos_rev_item.meta = rev.meta if rev else -1

        pos_rev_item.frame_id = id
        pos_rev_item.frame_start = frame_start


"""
update position keyframes
"""


def modify_partial_pos_keyframes(modify_animation_data: PosModifyAnimationData):
    data_objects = cast(dict[str, bpy.types.Object], bpy.data.objects)

    for dancer_item in state.dancers_array:
        dancer_name = dancer_item.name
        dancer_obj = data_objects[dancer_name]

        frames = modify_animation_data[dancer_name]

        delete = len(frames[0]) > 0
        update = len(frames[1]) > 0
        add = len(frames[2]) > 0

        action = ensure_action(dancer_obj, dancer_name + "Action")
        curves = [ensure_curve(action, "location", index=d) for d in range(3)]
        kpoints_lists = [get_keyframe_points(curve)[1] for curve in curves]

        kpoints_len = len(kpoints_lists[0])

        if delete:
            curve_index = 0

            for old_start in frames[0]:
                while (
                    curve_index < kpoints_len
                    and int(kpoints_lists[0][curve_index].co[0]) != old_start
                ):
                    curve_index += 1

                if curve_index < kpoints_len:
                    for d in range(3):
                        point = kpoints_lists[d][curve_index]
                        curves[d].keyframe_points.remove(point)

        kpoints_len = len(kpoints_lists[0])

        update_reorder = False
        if update:
            curve_index = 0
            points_to_update: list[tuple[int, bpy.types.Keyframe, float]] = []

            for old_start, frame_start, pos in frames[1]:
                if old_start != frame_start:
                    update_reorder = True

                while (
                    curve_index < kpoints_len
                    and int(kpoints_lists[0][curve_index].co[0]) != old_start
                ):
                    curve_index += 1

                if curve_index < kpoints_len:
                    for d in range(3):
                        point = kpoints_lists[d][curve_index]
                        points_to_update.append((frame_start, point, pos[d]))

            for frame_start, point, pos in points_to_update:
                point.co = frame_start, pos
                point.interpolation = "LINEAR"
                point.select_control_point = False

        kpoints_len = len(kpoints_lists[0])

        # Add frames
        if add:
            for d in range(3):
                curves[d].keyframe_points.add(len(frames[2]))

                for i, (frame_start, pos) in enumerate(frames[2]):
                    point = kpoints_lists[d][kpoints_len + i]

                    point.co = frame_start, pos[d]
                    point.interpolation = "LINEAR"
                    point.select_control_point = True

        if update_reorder or add:
            for curve in curves:
                curve.keyframe_points.sort()
