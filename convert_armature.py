import bpy
import copy
from mathutils import Matrix

from bpy_extras.io_utils import axis_conversion
from . import utils
from .utils import Rename




def ConvertSkeleton(usda, obj_armature):
    armature = obj_armature.data
    joints = []
    restTransforms = []
    bindTransforms = []
    armature.pose_position = 'REST'

    for bone in armature.bones:
        bone_name = bone.name
        bo = bone
        while bo.parent:
            bo = bo.parent
            bone_name = bo.name +'/'+ bone_name
        joints.append(Rename(bone_name))

        global_matrix = (axis_conversion(to_forward='-Z', to_up='Y').to_4x4())
    
        # Specifies the rest-pose transforms of each joint in local space
        mat = global_matrix @ obj_armature.pose.bones[bone.name].matrix
        for i in range(3):
            mat[i][3] *= 0.01
        matrix = [tuple(v) for v in mat]
        restTransforms.append(tuple(matrix)) 

        # Specifies the bind-pose transforms of each joint in world space
        mat = obj_armature.matrix_world @ global_matrix @ armature.bones[bone.name].matrix_local
        for i in range(3):
            mat[i][3] *= 0.01
        matrix = [tuple(v) for v in mat]
        bindTransforms.append(tuple(matrix))
    
    armature.pose_position = 'POSE'

    usda.append(f"""
        def Skeleton "skeleton"
        {{
            uniform token[] joints = {str(joints).replace("'", '"')}
            uniform matrix4d[] restTransforms = {restTransforms}
            uniform matrix4d[] bindTransforms = {bindTransforms}
        }}"""
    )



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



def ConvertSkelAnim(usda, obj_armature):
    armature = obj_armature.data

    usda.append(f"""

        def SkelAnimation "animation"
        {{"""
    )

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

        usda.append(f"""
            uniform token[] joints = {str(joints).replace("'", '"')}
            float3[] translations.timeSamples = {{"""
        )
        for frame, translation in translations:
            usda.append(f"""
                {frame}: {translation},"""
            )
        usda.append("""
            }
            quatf[] rotations.timeSamples = {"""
        )
        for frame, rotation in rotations:
            usda.append(f"""
                {frame}: {rotation},"""
            )
        usda.append("""
            }
            half3[] scales.timeSamples = {"""
        )
        for frame, scale in scales:
            usda.append(f"""
                {frame}: {scale},"""
            )
        usda.append("""
            }"""
        )
    usda.append("""
        }"""
    )




def ConvertArmatures(usda):
    if not utils.keywords["include_armatures"]:
        return

    usda.append("""

def Scope "Armatures"
{""")

    for armature in utils.armatures:
        usda.append(f"""
    def "{Rename(armature.name)}"
    {{
        rel skel:skeleton = </Armatures/{Rename(armature.name)}/skeleton>
        rel skel:animationSource = </Armatures/{Rename(armature.name)}/animation>"""
        )
        ConvertSkeleton(usda, armature)
        ConvertSkelAnim(usda, armature)

        usda.append("""
    }"""
        )
    
    usda.append("""
}""")
