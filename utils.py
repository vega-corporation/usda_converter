
import bpy
import os


def SetTargets(key):
    global keywords
    global objects
    global asset_dir
    global armatures
    global armature_obj

    keywords = key

    scene = bpy.context.scene
    if key['selection_only']:
        objects = bpy.context.selected_objects
    else:
        objects = bpy.context.scene.objects[:]
    objects = [obj for obj in objects if obj.type == 'MESH']
    objects = tuple(objects)

    asset_dir = os.path.splitext(key["filepath"])[0] + '_assets'

    armatures = []
    armature_obj = {obj.name:None for obj in objects}
    if key["include_armatures"]:
        for obj in objects:
            for mod in obj.modifiers:
                if mod.bl_rna.identifier == 'ArmatureModifier' and mod.object:
                    armature_obj[obj.name] = mod.object
                    armatures.append(mod.object)
                    break
    armatures = tuple(set(armatures))


def Rename(name):
    usd_name = name.encode("utf-8").decode("ascii","backslashreplace")
    usd_name = usd_name.replace(",", "_").replace(".", "_").replace("-", "_").replace(" ", "_").replace("\\", "_")
    if usd_name and usd_name[0].isdecimal():
        usd_name = "_"+usd_name
    return usd_name