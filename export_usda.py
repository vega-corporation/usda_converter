import bpy
import numpy as np
import os
import copy
import shutil
from mathutils import Matrix

from . import utils
from .utils import Rename
from . import convert_material
from . import convert_mesh
from . import convert_armature




def UsdaInit():
    scn = bpy.context.scene
    usda = """#usda 1.0
(
    defaultPrim = "Objects"""+'"'
    if utils.keywords["include_animation"]:
        usda += """
    startTimeCode = """+str(scn.frame_start)+"""
    endTimeCode = """+str(scn.frame_end)+"""
    timeCodesPerSecond = """+str(scn.render.fps*scn.render.frame_map_old/scn.render.frame_map_new)

    usda += """
    upAxis = """+'"'+utils.keywords["up_axis"]+'"'+"""
)"""
    return usda



def ObjectAnimation():
    obj_mats = {}
    for obj in utils.objects:
        obj_mats[obj.name] = []

    scn = bpy.context.scene
    orig_frame = scn.frame_current

    for frame in range(scn.frame_start, scn.frame_end+1):
        scn.frame_set(frame)

        for obj in utils.objects:
            if obj_mats[obj.name] and obj_mats[obj.name][-1][1] == obj.matrix_world and frame != scn.frame_end:
                continue

            obj_mats[obj.name] += [(frame, copy.copy(obj.matrix_world))]
        
    scn.frame_set(orig_frame)

    return obj_mats



def ConvertSkeleton(obj):
    usda = ""
    obj_armature = None
    for mod in obj.modifiers:
        if mod.bl_rna.identifier == 'ArmatureModifier' and mod.object:
            obj_armature = mod.object
            break

    if obj_armature:
        armature = obj_armature.data
        joints = {}
        for bone in armature.bones:
            bone_name = bone.name
            bo = bone
            while bo.parent:
                bo = bo.parent
                bone_name = bo.name +'/'+ bone_name
            joints[bone.name] = bone_name
        
        bone_names = [bone.name for bone in armature.bones]
        group_names = [g.name for g in obj.vertex_groups]
        valid_names = [name for name in bone_names if name in group_names]
        invalid_names = [name for name in bone_names if name not in group_names]
        names = []
        for i, group in enumerate(obj.vertex_groups):
            if i == len(joints):
                break
            if group.name in valid_names:
                names.append(joints[group.name])
                valid_names.remove(group.name)
            else:
                if invalid_names:
                    names.append(invalid_names.pop(0))
                else:
                    names.append(" ")
        names += valid_names + invalid_names

        restTransforms = []
        bindTransforms = []
        for i, group in enumerate(obj.vertex_groups):
            if i == len(joints):
                break

            # Specifies the rest-pose transforms of each joint in local space
            if group.name in valid_names:
                matrix = [tuple(v) for v in obj_armature.pose.bones[group.name].matrix]
            else:
                matrix = [tuple(v) for v in Matrix()]
            restTransforms.append(tuple(matrix))

            # Specifies the bind-pose transforms of each joint in world space
            if group.name in valid_names:
                matrix = [tuple(v) for v in armature.bones[group.name].matrix_local]
            else:
                matrix = [tuple(v) for v in Matrix()]
            bindTransforms.append(tuple(matrix))

        while len(restTransforms) < len(names):
            matrix = [tuple(v) for v in Matrix()]
            restTransforms.append(tuple(matrix))
            bindTransforms.append(tuple(matrix))

        usda += """
            def Skeleton "skeleton"
            {
                uniform token[] joints = """+str(names).replace("'", '"')+"""
                uniform matrix4d[] restTransforms = """+str(restTransforms)+"""
                uniform matrix4d[] bindTransforms = """+str(bindTransforms)+"""
            }"""

    return usda


            

def ConvertObjects():
    usda = """

def Scope "Objects"
{"""
    scn = bpy.context.scene

    # keyflame animation
    if utils.keywords["include_animation"]:
        animation_data = ObjectAnimation()

    for obj in utils.objects:
        usda += """
    def Xform """+'"'+Rename(obj.name)+'"'+"""
    {"""

        if utils.keywords["include_animation"]:
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
        if utils.keywords["include_armatures"]:
            for mod in obj.modifiers:
                if mod.bl_rna.identifier == 'ArmatureModifier' and mod.object:
                    usda += """(
            references = </Armatures/"""+Rename(mod.object.name)+""">
        )"""
                    break
        usda += """
        {"""
        
        # joints
        if utils.keywords["include_armatures"]:
            usda += ConvertSkeleton(obj)

        mesh_name = obj.name if utils.keywords["apply_modifiers"] else obj.data.name
        
        usda += """
            def Mesh "mesh"(
                references = </Meshes/"""+Rename(mesh_name)+""">
            )
            {"""

        # bind materials
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

    with open(utils.keywords["filepath"], mode="w", encoding="utf-8") as f:
        f.write(usda)
    