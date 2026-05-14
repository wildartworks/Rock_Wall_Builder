bl_info = {
    "name": "Rock Wall Builder v9",
    "author": "Wildartworks studio",
    "version": (9, 0, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > Rock Wall Builder",
    "description": "Procedural rock wall generator",
    "category": "Add Mesh",
}

import bpy
import os
import random
import math

class RWB_Props(bpy.types.PropertyGroup):

    mode: bpy.props.EnumProperty(
        name="Mode",
        items=[
            ('PREFAB', "Prefab", ""),
            ('PROCEDURAL', "Procedural", "")
        ],
        default='PREFAB'
    )

    prefab_folder: bpy.props.StringProperty(
        name="Prefab Folder",
        subtype='DIR_PATH'
    )

    wall_length: bpy.props.FloatProperty(
        name="Wall Length (m)",
        default=6.0,
        min=0.1
    )

    wall_height: bpy.props.FloatProperty(
        name="Wall Height (m)",
        default=2.5,
        min=0.1
    )

    spacing: bpy.props.FloatProperty(
        name="Spacing (m)",
        default=0.8,
        min=0.05
    )

    depth_random: bpy.props.FloatProperty(
        name="Depth Random",
        default=0.25,
        min=0.0
    )

    jitter: bpy.props.FloatProperty(
        name="Position Jitter",
        default=0.15,
        min=0.0
    )

    scale_min: bpy.props.FloatProperty(
        name="Scale Min",
        default=0.8,
        min=0.01
    )

    scale_max: bpy.props.FloatProperty(
        name="Scale Max",
        default=1.25,
        min=0.01
    )

    random_rotation: bpy.props.BoolProperty(
        name="Random Rotation",
        default=True
    )

    seed: bpy.props.IntProperty(
        name="Seed",
        default=1
    )

def get_wall_collection():

    if "RockWall" in bpy.data.collections:
        return bpy.data.collections["RockWall"]

    coll = bpy.data.collections.new("RockWall")
    bpy.context.scene.collection.children.link(coll)

    return coll

def clear_wall():

    if "RockWall" not in bpy.data.collections:
        return

    coll = bpy.data.collections["RockWall"]

    for obj in list(coll.objects):
        bpy.data.objects.remove(obj, do_unlink=True)

def load_prefab_meshes(folder):

    meshes = []

    folder = bpy.path.abspath(folder)

    if not os.path.exists(folder):
        return meshes

    blend_files = [
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.lower().endswith(".blend")
    ]

    for blend_file in blend_files:

        try:

            with bpy.data.libraries.load(blend_file, link=False) as (data_from, data_to):
                data_to.objects = data_from.objects

            for obj in data_to.objects:

                if obj and obj.type == 'MESH':
                    bpy.context.collection.objects.link(obj)
                    meshes.append(obj)

        except Exception as e:
            print(e)

    return meshes

def create_procedural_rock(location, rnd, props):

    bpy.ops.mesh.primitive_ico_sphere_add(
        subdivisions=2,
        radius=0.5,
        location=location
    )

    obj = bpy.context.active_object

    scale = rnd.uniform(props.scale_min, props.scale_max)

    obj.scale = (
        scale * rnd.uniform(0.8, 1.2),
        scale * rnd.uniform(0.8, 1.2),
        scale * rnd.uniform(0.7, 1.3),
    )

    return obj

def generate_wall(context):

    props = context.scene.rwb_props

    clear_wall()

    coll = get_wall_collection()

    rnd = random.Random(props.seed)

    cols = max(1, int(props.wall_length / props.spacing))
    rows = max(1, int(props.wall_height / props.spacing))

    cursor = context.scene.cursor.location.copy()

    start_x = cursor.x - ((cols - 1) * props.spacing) / 2

    prefab_pool = []

    if props.mode == 'PREFAB':
        prefab_pool = load_prefab_meshes(props.prefab_folder)

    created = []

    for r in range(rows):

        for c in range(cols):

            x = start_x + (c * props.spacing)
            y = cursor.y + rnd.uniform(-props.depth_random, props.depth_random)
            z = cursor.z + (r * props.spacing)

            x += rnd.uniform(-props.jitter, props.jitter)
            z += rnd.uniform(-props.jitter, props.jitter)

            pos = (x, y, z)

            if props.mode == 'PREFAB' and prefab_pool:

                source = rnd.choice(prefab_pool)

                obj = source.copy()
                obj.data = source.data.copy()

                bpy.context.collection.objects.link(obj)

                obj.location = pos

                scale = rnd.uniform(props.scale_min, props.scale_max)

                obj.scale = (scale, scale, scale)

                if props.random_rotation:
                    obj.rotation_euler = (
                        rnd.uniform(0, math.pi * 2),
                        rnd.uniform(0, math.pi * 2),
                        rnd.uniform(0, math.pi * 2),
                    )

            else:

                obj = create_procedural_rock(pos, rnd, props)

            created.append(obj)

    for obj in created:

        for c in obj.users_collection:
            c.objects.unlink(obj)

        coll.objects.link(obj)

    bpy.ops.object.select_all(action='DESELECT')

    for obj in created:
        obj.select_set(True)

    bpy.context.view_layer.objects.active = created[0]

    bpy.ops.object.join()

    wall = bpy.context.active_object
    wall.name = "RockWall"

    return wall

class RWB_OT_Generate(bpy.types.Operator):
    bl_idname = "rwb.generate_wall"
    bl_label = "Generate Wall"

    def execute(self, context):

        generate_wall(context)

        return {'FINISHED'}

class RWB_OT_Update(bpy.types.Operator):
    bl_idname = "rwb.update_wall"
    bl_label = "Update Wall"

    def execute(self, context):

        generate_wall(context)

        return {'FINISHED'}

class RWB_OT_Reseed(bpy.types.Operator):
    bl_idname = "rwb.reseed_wall"
    bl_label = "Reseed"

    def execute(self, context):

        props = context.scene.rwb_props
        props.seed = random.randint(0, 999999)

        generate_wall(context)

        return {'FINISHED'}

class RWB_OT_Reset(bpy.types.Operator):
    bl_idname = "rwb.reset_wall"
    bl_label = "Reset"

    def execute(self, context):

        props = context.scene.rwb_props

        props.wall_length = 6.0
        props.wall_height = 2.5
        props.spacing = 0.8
        props.depth_random = 0.25
        props.jitter = 0.15
        props.scale_min = 0.8
        props.scale_max = 1.25
        props.seed = 1

        return {'FINISHED'}

class RWB_PT_MainPanel(bpy.types.Panel):

    bl_label = "Rock Wall Builder v9"
    bl_idname = "RWB_PT_MainPanel"

    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Rock Wall Builder'

    def draw(self, context):

        layout = self.layout
        props = context.scene.rwb_props

        layout.prop(props, "mode")

        if props.mode == 'PREFAB':
            layout.prop(props, "prefab_folder")

        layout.prop(props, "wall_length")
        layout.prop(props, "wall_height")
        layout.prop(props, "spacing")

        layout.prop(props, "depth_random")
        layout.prop(props, "jitter")

        layout.prop(props, "scale_min")
        layout.prop(props, "scale_max")

        layout.prop(props, "random_rotation")

        layout.prop(props, "seed")

        row = layout.row(align=True)
        row.operator("rwb.generate_wall")
        row.operator("rwb.update_wall")

        row = layout.row(align=True)
        row.operator("rwb.reseed_wall")
        row.operator("rwb.reset_wall")

classes = (
    RWB_Props,
    RWB_OT_Generate,
    RWB_OT_Update,
    RWB_OT_Reseed,
    RWB_OT_Reset,
    RWB_PT_MainPanel,
)

def register():

    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.rwb_props = bpy.props.PointerProperty(type=RWB_Props)

def unregister():

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.rwb_props

if __name__ == "__main__":
    register()
