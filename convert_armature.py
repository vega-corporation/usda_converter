import bpy
import numpy as np
import math
import os
import shutil

from . import target
from .target import Rename



def ConvertSkeletonUsda():
    usda = ""
    return usda

def ConvertSkelAnimationUsda():
    usda = ""
    return usda



def ConvertArmatureUsda():
    if not target.keywords["include_armatures"]:
        return ""

    usda = """

def Scope "Armatures"
{"""

    # get armatures
    armatures = []
    for obj in D.objects:
        for mod in obj.modifiers:
            if mod.bl_rna.identifier == 'ArmatureModifier' and mod.object:
                armatures.append(mod.object.data)
    armatures = list(set(armatures))

    for armature in armatures:
        usda += """
    def """+'"'+Rename(armature.name)+'"'+"""
    {
        rel skel:animationSource = </Armatures/"""+Rename(armature.name)+"""/animation>
        rel skel:skeleton = </Armatures/"""+Rename(armature.name)+"""/skeleton>"""
        
        usda += ConvertSkeletonUsda()
        usda += ConvertSkelAnimationUsda()
        usda += """
    }"""
    
    usda += """
}"""

    return usda

