import bpy
import numpy as np
import os
import shutil

from . import usda_shader
from . import target
from .target import Rename
from . import convert_material
from . import convert_mesh




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



def ConvertObjectUsda():
    usda = """

def Scope "Objects"
{"""
    scn = bpy.context.scene
    orig_frame = bpy.context.scene.frame_current

    for obj in target.objects:
        usda += """
    def Xform """+'"'+Rename(obj.name)+'"'+"""
    {"""
        
        mat = obj.matrix_world if target.keywords["apply_modifiers"] else obj.matrix_local

        anim_location_f = False
        anim_rotation_f = False
        anim_scale_f = False

        # keyflame animation
        if target.keywords["include_animation"] and obj.animation_data and obj.animation_data.action:
            action = obj.animation_data.action
            # animation frames
            start = min(round(action.frame_range[0]), scn.frame_start)
            end = max(round(action.frame_range[1]), scn.frame_end)
            frames = list(range(start, end+1))
            if scn.frame_end not in frames:
                frames.append(scn.frame_end)
            if scn.frame_start not in frames:
                frames.insert(0, scn.frame_start)

            # types :'location' or 'scale' or 'rotation_euler'
            act_types = [cur.data_path for cur in action.fcurves]
            anim_location_f = 'location' in act_types
            anim_rotation_f = 'location' in act_types
            anim_scale_f = 'location' in act_types
            anim_location = []
            anim_rotation = []
            anim_scale = []

            for frame in frames:
                scn.frame_set(frame)
                mat = obj.matrix_world if target.keywords["apply_modifiers"] else obj.matrix_local

                if anim_location_f:
                    anim_location += [(frame, mat.to_translation())]
                if anim_rotation_f:
                    anim_rotation += [(frame, mat.to_euler())]
                if anim_scale_f:
                    anim_scale += [(frame, mat.to_scale())]

        if anim_location_f:
            usda += """
        double3 xformOp:translate.timeSamples = {"""
            for frame, location in anim_location:
                usda += """
            """+str(frame)+": "+str(tuple(np.array(location)*100))+","
            usda += """
        }"""
        else:
            usda += """
        double3 xformOp:translate = """+str(tuple(np.array(mat.translation)*100))
        
        if anim_rotation_f:
            usda += """
        float3 xformOp:rotateXYZ.timeSamples = {"""
            for frame, rotation in anim_rotation:
                usda += """
            """+str(frame)+": "+str(tuple(np.array(rotation)*180/np.pi))+","
            usda += """
        }"""
        else:
            usda += """
        float3 xformOp:rotateXYZ = """+str(tuple(np.array(mat.to_euler())*180/np.pi))
        
        if anim_scale_f:
            usda += """
        float3 xformOp:scale.timeSamples = {"""
            for frame, scale in anim_scale:
                usda += """
            """+str(frame)+": "+str(tuple(scale))+","
            usda += """
        }"""
        else:
            usda += """
        float3 xformOp:scale = """+str(tuple(mat.to_scale()))

        usda += """
        uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:rotateXYZ", "xformOp:scale"]
        def SkelRoot "skelroot"""+'"'

        # references skel and mesh
        # payload or references other files are not supported by usdzconverter 0.61
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

    bpy.context.scene.frame_set(orig_frame)

    return usda



def ExportUsda():
    usda = "#usda 1.0"
    usda += UsdaInit()
    usda += ConvertObjectUsda()
    usda += convert_mesh.ConvertMeshUsda()
    usda += convert_material.ConvertMaterialUsda()

    with open(target.keywords["filepath"], mode="w", encoding="utf-8") as f:
        f.write(usda)
    