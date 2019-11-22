import bpy
import numpy as np
import os
import copy
import shutil

from . import target
from .target import Rename
from . import convert_material
from . import convert_mesh
from . import convert_armature




def UsdaInit():
    scn = bpy.context.scene
    usda = """#usda 1.0
(
    defaultPrim = "Objects"""+'"'
    if target.keywords["include_animation"]:
        usda += """
    startTimeCode = """+str(scn.frame_start)+"""
    endTimeCode = """+str(scn.frame_end)+"""
    timeCodesPerSecond = """+str(scn.render.fps*scn.render.frame_map_old/scn.render.frame_map_new)

    usda += """
    upAxis = """+'"'+target.keywords["up_axis"]+'"'+"""
)"""
    return usda



def ObjectAnimationData():
    obj_mats = {}
    for obj in target.objects:
        obj_mats[obj.name] = []

    scn = bpy.context.scene
    orig_frame = scn.frame_current

    for frame in range(scn.frame_start, scn.frame_end+1):
        scn.frame_set(frame)

        for obj in target.objects:
            if obj_mats[obj.name] and obj_mats[obj.name][-1][1] == obj.matrix_world and frame != scn.frame_end:
                continue

            obj_mats[obj.name] += [(frame, copy.copy(obj.matrix_world))]
        
    scn.frame_set(orig_frame)

    return obj_mats



def ConvertObjects():
    usda = """

def Scope "Objects"
{"""
    scn = bpy.context.scene

    # keyflame animation
    if target.keywords["include_animation"]:
        animation_data = ObjectAnimationData()

    for obj in target.objects:
        usda += """
    def Xform """+'"'+Rename(obj.name)+'"'+"""
    {"""

        if target.keywords["include_animation"]:
            usda += """
        double3 xformOp:translate.timeSamples = {"""
            for frame, mat in animation_data[obj.name]:
                usda += """
            """+str(frame)+": "+str(tuple(np.array(mat.to_translation())*100))+","
            usda += """
        }
        float3 xformOp:rotateXYZ.timeSamples = {"""
            for frame, mat in animation_data[obj.name]:
                usda += """
            """+str(frame)+": "+str(tuple(np.array(mat.to_euler())*180/np.pi))+","
            usda += """
        }
        float3 xformOp:scale.timeSamples = {"""
            for frame, mat in animation_data[obj.name]:
                usda += """
            """+str(frame)+": "+str(tuple(np.array(mat.to_scale())*100))+","
            usda += """
        }"""

        else:
            mat = obj.matrix_world
            usda += """
        double3 xformOp:translate = """+str(tuple(np.array(mat.to_translation())*100))+"""
        float3 xformOp:rotateXYZ = """+str(tuple(np.array(mat.to_euler())*180/np.pi))+"""
        float3 xformOp:scale = """+str(tuple(np.array(mat.to_scale())*100))

        usda += """
        uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:rotateXYZ", "xformOp:scale"]
        def SkelRoot "skelroot"""+'"'

        # references skel and mesh
        # payload or references other files are not supported by usdzconverter 0.61
        if target.keywords["include_armatures"]:
            for mod in obj.modifiers:
                if mod.bl_rna.identifier == 'ArmatureModifier' and mod.object:
                    usda += """(
            references = </Armatures/"""+Rename(mod.object.name)+""">
        )"""
                    break
        
        mesh_name = obj.name if target.keywords["apply_modifiers"] else obj.data.name
        
        usda += """
        {
            def Mesh "mesh"(
                references = </Meshes/"""+Rename(mesh_name)+""">
            )
            {"""

        for i, material_slot in enumerate(obj.material_slots):
            if material_slot.material:
                usda += """
                def GeomSubset """+'"'+"mat_"+str(i).zfill(4)+'"'+"""
                {
                    rel material:binding = </Materials/"""+Rename(material_slot.name)+""">
                }"""
        usda += """
            }
        }
    }"""
    usda += """
}"""

    return usda



def ExportUsda():
    usda = "#usda 1.0"
    usda += UsdaInit()
    usda += ConvertObjects()
    usda += convert_armature.ConvertArmatures()
    usda += convert_mesh.ConvertMeshes()
    usda += convert_material.ConvertMaterials()

    with open(target.keywords["filepath"], mode="w", encoding="utf-8") as f:
        f.write(usda)
    