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




def UsdaInit(usda):
    scn = bpy.context.scene
    
    usda.append("""#usda 1.0
(
    defaultPrim = "Objects\""""
    )

    if utils.keywords["include_animation"]:
        usda.append(f"""
    startTimeCode = {scn.frame_start}
    endTimeCode = {scn.frame_end}
    timeCodesPerSecond = {scn.render.fps*scn.render.frame_map_old/scn.render.frame_map_new}"""
        )
    usda.append(f"""
    upAxis = "{utils.keywords["up_axis"]}"
)""")



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




def ConvertSkeleton(usda, obj):
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
            joints[bone.name] = Rename(bone_name)
        
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
                    names.append(invalid_names.pop())
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

        usda.append(f"""
            def Skeleton "skeleton"
            {{
                uniform token[] joints = {str(names).replace("'", '"')}
                uniform matrix4d[] restTransforms = {restTransforms}
                uniform matrix4d[] bindTransforms = {bindTransforms}
            }}"""
        )




def ConvertObjects(usda):
    scn = bpy.context.scene
    usda.append("""

def Scope "Objects"
{"""
    )

    # keyflame animation
    if utils.keywords["include_animation"]:
        animation_data = ObjectAnimation()

    for obj in utils.objects:
        usda.append(f"""
    def Xform "{Rename(obj.name)}"
    {{"""
    )

        if utils.keywords["include_animation"]:
            usda.append("""
        double3 xformOp:translate.timeSamples = {"""
            )
            for frame, mat in animation_data[obj.name]:
                usda.append(f"""
            {frame}: {tuple(np.array(mat.to_translation())*100)},"""
                )
            usda.append("""
        }
        float3 xformOp:rotateXYZ.timeSamples = {"""
            )
            for frame, mat in animation_data[obj.name]:
                usda.append(f"""
            {frame}: {tuple(np.array(mat.to_euler())*180/np.pi)},"""
                )
            usda.append("""
        }
        float3 xformOp:scale.timeSamples = {"""
            )
            for frame, mat in animation_data[obj.name]:
                usda.append(f"""
            {frame}: {tuple(np.array(mat.to_scale())*100)},"""
                )
            usda.append("""
        }"""
        )

        else:
            mat = obj.matrix_world
            usda.append(f"""
        double3 xformOp:translate = {tuple(np.array(mat.to_translation())*100)}
        float3 xformOp:rotateXYZ = {tuple(np.array(mat.to_euler())*180/np.pi)}
        float3 xformOp:scale = {tuple(np.array(mat.to_scale())*100)}"""
        )

        usda.append("""
        uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:rotateXYZ", "xformOp:scale"]
        def SkelRoot "skelroot\""""
        )

        # references skel and mesh
        # payload or references other files are not supported by usdzconverter 0.61
        if utils.keywords["include_armatures"]:
            for mod in obj.modifiers:
                if mod.bl_rna.identifier == 'ArmatureModifier' and mod.object:
                    usda.append(f"""(
            references = </Armatures/{Rename(mod.object.name)}>
        )"""
                    )
                    break
        usda.append("""
        {"""
        )
        
        # joints
        if utils.keywords["include_armatures"]:
            ConvertSkeleton(usda, obj)

        mesh_name = obj.name if utils.keywords["apply_modifiers"] else obj.data.name
        
        usda.append(f"""
            def Mesh "mesh"(
                references = </Meshes/{Rename(mesh_name)}>
            )
            {{"""
        )

        # bind materials
        for i, material_slot in enumerate(obj.material_slots):
            if material_slot.material:
                usda.append(f"""
                def GeomSubset "mat_{str(i).zfill(4)}"
                {{
                    rel material:binding = </Materials/{Rename(material_slot.name)}>
                }}"""
                )

        usda.append("""
            }
        }
    }"""
        )
    usda.append("""
}"""
    )



def ExportUsda():
    usda = []
    UsdaInit(usda)
    ConvertObjects(usda)
    convert_armature.ConvertArmatures(usda)
    convert_mesh.ConvertMeshes(usda)
    convert_material.ConvertMaterials(usda)
    usda = ''.join(usda)
    
    with open(utils.keywords["filepath"], mode="w", encoding="utf-8") as f:
        f.write(usda)
    