import bpy
import numpy as np
import math
import os
import copy
import shutil
from mathutils import Matrix

from . import utils
from .utils import Rename



def SkelAnimationData(bones):
    translations = []
    rotations = []# quaternion
    scales = []

    scn = bpy.context.scene
    orig_frame = scn.frame_current

    for frame in range(scn.frame_start, scn.frame_end+1):
        scn.frame_set(frame)

        translations_old = []
        rotations_old = []
        scales_old = []
        for bone in bones:
            if bone.parent:
                par_inv = bone.parent.matrix_channel.inverted_safe()
            else:
                par_inv = Matrix()

            mat = par_inv @ bone.matrix_channel

            loc, rot, scale = mat.decompose()
            loc = tuple([round(n,5) for n in loc])
            rot = tuple([round(n,5) for n in rot])
            scale = tuple([round(n,5) for n in scale])
            translations_old.append(loc[:])
            rotations_old.append(rot[:])
            scales_old.append(scale[:])

        if not translations or translations[-1][1] != translations_old or frame == scn.frame_end:
            translations += [(frame, copy.copy(translations_old))]
            
        if not rotations or rotations[-1][1] != rotations_old or frame == scn.frame_end:
            rotations += [(frame, copy.copy(rotations_old))]

        if not scales or scales[-1][1] != scales_old or frame == scn.frame_end:
            scales += [(frame, copy.copy(scales_old))]
        
    scn.frame_set(orig_frame)

    return translations, rotations, scales



def ConvertSkel(obj_armature):
    armature = obj_armature.data

    usda = """
    def """+'"'+Rename(armature.name)+'"'+"""
    {
        rel skel:skeleton = </Armatures/"""+Rename(armature.name)+"""/skeleton>
        rel skel:animationSource = </Armatures/"""+Rename(armature.name)+"""/animation>"""
        
    # animation data
    usda += """

        def SkelAnimation "animation"
        {"""

    if utils.keywords["include_animation"]:
        translations, rotations, scales = SkelAnimationData(obj_armature.pose.bones)

        joints = []
        for bone in armature.bones:
            bone_name = bone.name
            bo = bone
            while bo.parent:
                bo = bo.parent
                bone_name = bo.name +'/'+ bone_name
            joints.append(Rename(bone_name))

        usda += """
            uniform token[] joints = """+str(joints).replace("'", '"')
            
        usda += """
            float3[] translations.timeSamples = {"""
        for frame, translation in translations:
            usda += """
                """+str(frame)+": "+str(translation)+","
        usda += """
            }
            quatf[] rotations.timeSamples = {"""
        for frame, rotation in rotations:
            usda += """
                """+str(frame)+": "+str(rotation)+","
        usda += """
            }
            half3[] scales.timeSamples = {"""
        for frame, scale in scales:
            usda += """
                """+str(frame)+": "+str(scale)+","
        usda += """
            }"""

    usda += """
        }
    }"""
    
    return usda



def ConvertArmatures():
    if not utils.keywords["include_armatures"]:
        return ""
    
    # get armatures
    armatures = []
    for obj in utils.objects:
        for mod in obj.modifiers:
            if mod.bl_rna.identifier == 'ArmatureModifier' and mod.object:
                armatures.append(mod.object)
    armatures = list(set(armatures))

    usda = """

def Scope "Armatures"
{"""

    for armature in armatures:
        usda += ConvertSkel(armature)
    
    usda += """
}"""

    return usda

