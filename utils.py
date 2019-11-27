
import bpy
import os


def SetTargets(key):
    from bpy_extras.io_utils import axis_conversion
    global keywords
    global global_matrix
    global asset_dir
    global objects
    global armatures

    keywords = key

    global_matrix = (axis_conversion(to_forward='Y', to_up='Z').to_4x4())

    asset_dir = os.path.splitext(key["filepath"])[0] + '_assets'

    if key['selection_only']:
        objects = bpy.context.selected_objects
    else:
        objects = bpy.context.scene.objects[:]
    objects = tuple(objects)


def Rename(name):
    usd_name = name.replace(",", "_").replace(".", "_").replace("-", "_").replace(" ", "")
    if len(name) > 0 and name[0].isdecimal():
        usd_name = "_"+usd_name
    return usd_name