
import bpy
import os


def SetTargets(key):
    from bpy_extras.io_utils import axis_conversion
    global keywords
    global objects
    global asset_dir
    global global_matrix

    keywords = key

    scene = bpy.context.scene
    if key['selection_only']:
        objects = bpy.context.selected_objects
    else:
        objects = bpy.context.scene.objects[:]
    objects = tuple(objects)

    asset_dir = os.path.splitext(key["filepath"])[0] + '_assets'

    global_matrix = (axis_conversion(to_forward='Y', to_up='Z').to_4x4())


def Rename(name):
    usd_name = name.encode('utf-8', 'replace').hex()
    usd_name = usd_name.replace(",", "_").replace(".", "_").replace("-", "_").replace(" ", "")
    if usd_name and usd_name[0].isdecimal():
        usd_name = "_"+usd_name
    return usd_name