import bpy
import numpy as np

from . import utils
from .utils import Blend
from .. import target


def Handler(node):
    if node.node.bl_rna.identifier in globals():
        if node.node.mute:
            node.shader.Mute()
        else:
            eval(node.node.bl_rna.identifier)(node)




# MixRGBのパラメータを入力
def SetMixRGB(param, blend, fac, color1, color2):
    if color1[0] is None:
        color1 = color2
        if color2[0] is None:
            return
    if color2[0] is None:
        color2 = color1
    color1 = utils.GetColor(color1, len(param))
    color2 = utils.GetColor(color2, len(param))
    if type(fac) is float:
        fac = [fac]
    # ソケットに繋がない場合
    if type(fac) == type(color1) == type(color2) == list\
        and type(fac[0]) == type(color1[0]) == type(color2[0]) == float:
        param.clear()
        color = np.array(color1)
        fac = fac[0]
        if blend == Blend.MIX:
            color = np.array(color1) * (1-fac) + np.array(color2) * fac
        elif blend == Blend.ADD:
            color = np.array(color1) + np.array(color2) * fac
        elif blend == Blend.SUB:
            color = np.array(color1) - np.array(color2) * fac
        elif blend == Blend.MUL:
            color = np.array(color1) * (1 + fac*(np.array(color2)-1))
        elif blend == Blend.DIF:
            color = np.abs(np.array(color1) - np.array(color2) * fac)
        color = np.clip(color, 0.0, max(max(color1), max(color2)))
        color = color.astype(type('float', (float,), {}))
        param.extend(list(color))
    # 繋ぐ場合MixRGBを追加
    else:
        if type(param[0]) is not utils.ShaderMixRGB:
            param.clear()
        param.append(utils.ShaderMixRGB(blend, fac, color1, color2))





def ShaderNodeMixShader(node):
    fac = node.inputs["Fac"]
    shader1 = node.inputs['Shader']
    shader2 = node.inputs['Shader_001']
    if fac[0] == 0.0:
        node.shader.Copy(shader1)
        return
    elif fac[0] == 1.0:
        node.shader.Copy(shader2)
        return
    SetMixRGB(node.shader.base_color, Blend.MIX, fac, shader1.base_color, shader2.base_color)
    SetMixRGB(node.shader.subsurface, Blend.MIX, fac, shader1.subsurface, shader2.subsurface)
    SetMixRGB(node.shader.subsurface_radius, Blend.MIX, fac, shader1.subsurface_radius, shader2.subsurface_radius)
    SetMixRGB(node.shader.subsurface_color, Blend.MIX, fac, shader1.subsurface_color, shader2.subsurface_color)
    SetMixRGB(node.shader.metallic, Blend.MIX, fac, shader1.metallic, shader2.metallic)
    SetMixRGB(node.shader.specular, Blend.MIX, fac, shader1.specular, shader2.specular)
    SetMixRGB(node.shader.specular_tint, Blend.MIX, fac, shader1.specular_tint, shader2.specular_tint)
    SetMixRGB(node.shader.roughness, Blend.MIX, fac, shader1.roughness, shader2.roughness)
    SetMixRGB(node.shader.anisotropic, Blend.MIX, fac, shader1.anisotropic, shader2.anisotropic)
    SetMixRGB(node.shader.anisotropic_rotation, Blend.MIX, fac, shader1.anisotropic_rotation, shader2.anisotropic_rotation)
    SetMixRGB(node.shader.sheen, Blend.MIX, fac, shader1.sheen, shader2.sheen)
    SetMixRGB(node.shader.sheen_tint, Blend.MIX, fac, shader1.sheen_tint, shader2.sheen_tint)
    SetMixRGB(node.shader.clearcoat, Blend.MIX, fac, shader1.clearcoat, shader2.clearcoat)
    SetMixRGB(node.shader.clearcoat_roughness, Blend.MIX, fac, shader1.clearcoat_roughness, shader2.clearcoat_roughness)
    SetMixRGB(node.shader.ior, Blend.MIX, fac, shader1.ior, shader2.ior)
    SetMixRGB(node.shader.transmission, Blend.MIX, fac, shader1.transmission, shader2.transmission)
    SetMixRGB(node.shader.transmission_roughness, Blend.MIX, fac, shader1.transmission_roughness, shader2.transmission_roughness)
    SetMixRGB(node.shader.emission, Blend.MIX, fac, shader1.emission, shader2.emission)
    SetMixRGB(node.shader.alpha, Blend.MIX, fac, shader1.alpha, shader2.alpha)
    SetMixRGB(node.shader.normal, Blend.MIX, fac, shader1.normal, shader2.normal)
    SetMixRGB(node.shader.clearcoat_normal, Blend.MIX, fac, shader1.clearcoat_normal, shader2.clearcoat_normal)
    SetMixRGB(node.shader.tangent, Blend.MIX, fac, shader1.tangent, shader2.tangent)


def ShaderNodeAddShader(node):
    shader1 = node.inputs['Shader']
    shader2 = node.inputs['Shader_001']
    if shader1.mute:
        node.shader = shader2
        return
    if shader2.mute:
        node.shader = shader1
        return
    SetMixRGB(node.shader.base_color, Blend.ADD, 1.0, shader1.base_color, shader2.base_color)
    SetMixRGB(node.shader.subsurface, Blend.ADD, 1.0, shader1.subsurface, shader2.subsurface)
    SetMixRGB(node.shader.subsurface_radius, Blend.ADD, 1.0, shader1.subsurface_radius, shader2.subsurface_radius)
    SetMixRGB(node.shader.subsurface_color, Blend.ADD, 1.0, shader1.subsurface_color, shader2.subsurface_color)
    SetMixRGB(node.shader.metallic, Blend.MIX, 0.5, shader1.metallic, shader2.metallic)
    SetMixRGB(node.shader.specular, Blend.MIX, 0.5, shader1.specular, shader2.specular)
    SetMixRGB(node.shader.specular_tint, Blend.MIX, 0.5, shader1.specular_tint, shader2.specular_tint)
    SetMixRGB(node.shader.roughness, Blend.MIX, 0.5, shader1.roughness, shader2.roughness)
    SetMixRGB(node.shader.anisotropic, Blend.ADD, 1.0, shader1.anisotropic, shader2.anisotropic)
    SetMixRGB(node.shader.anisotropic_rotation, Blend.ADD, 1.0, shader1.anisotropic_rotation, shader2.anisotropic_rotation)
    SetMixRGB(node.shader.sheen, Blend.MIX, 0.5, shader1.sheen, shader2.sheen)
    SetMixRGB(node.shader.sheen_tint, Blend.MIX, 0.5, shader1.sheen_tint, shader2.sheen_tint)
    SetMixRGB(node.shader.clearcoat, Blend.ADD, 1.0, shader1.clearcoat, shader2.clearcoat)
    SetMixRGB(node.shader.clearcoat_roughness, Blend.ADD, 1.0, shader1.clearcoat_roughness, shader2.clearcoat_roughness)
    SetMixRGB(node.shader.ior, Blend.MIX, 0.5, shader1.ior, shader2.ior)
    SetMixRGB(node.shader.transmission, Blend.ADD, 1.0, shader1.transmission, shader2.transmission)
    SetMixRGB(node.shader.transmission_roughness, Blend.ADD, 1.0, shader1.transmission_roughness, shader2.transmission_roughness)
    SetMixRGB(node.shader.emission, Blend.ADD, 1.0, shader1.emission, shader2.emission)
    SetMixRGB(node.shader.alpha, Blend.MIX, 0.5, shader1.alpha, shader2.alpha)
    SetMixRGB(node.shader.normal, Blend.MIX, 0.5, shader1.normal, shader2.normal)
    SetMixRGB(node.shader.clearcoat_normal, Blend.MIX, 0.5, shader1.clearcoat_normal, shader2.clearcoat_normal)
    SetMixRGB(node.shader.tangent, Blend.MIX, 0.5, shader1.tangent, shader2.tangent)


def ShaderNodeBsdfPrincipled(node):
    node.shader.base_color = node.inputs['Base Color']
    node.shader.subsurface = node.inputs['Subsurface']
    node.shader.subsurface_radius = node.inputs['Subsurface Radius']
    node.shader.subsurface_color = node.inputs['Subsurface Color']
    node.shader.metallic = node.inputs['Metallic']
    node.shader.specular = node.inputs['Specular']
    node.shader.specular_tint = node.inputs['Specular Tint']
    node.shader.roughness = node.inputs['Roughness']
    node.shader.anisotropic = node.inputs['Anisotropic']
    node.shader.anisotropic_rotation = node.inputs['Anisotropic Rotation']
    node.shader.sheen = node.inputs['Sheen']
    node.shader.sheen_tint = node.inputs['Sheen Tint']
    node.shader.clearcoat = node.inputs['Clearcoat']
    node.shader.clearcoat_roughness = node.inputs['Clearcoat Roughness']
    node.shader.ior = node.inputs['IOR']
    node.shader.transmission = node.inputs['Transmission']
    node.shader.transmission_roughness = node.inputs['Transmission Roughness']
    node.shader.emission = node.inputs['Emission']
    node.shader.alpha = node.inputs['Alpha']
    node.shader.normal = node.inputs['Normal']
    node.shader.clearcoat_normal = node.inputs['Clearcoat Normal']
    node.shader.tangent = node.inputs['Tangent']


def ShaderNodeBsdfDiffuse(node):
    node.shader.base_color = node.inputs['Color']
    node.shader.metallic = [0.0]
    # node.shader.roughness = node.inputs['Roughness']
    node.shader.transmission = [0.0]
    node.shader.normal = node.inputs['Normal']
    node.shader.emission = [0.0, 0.0, 0.0, 1.0]
    node.shader.alpha = [1.0]


def ShaderNodeEmission(node):
    node.shader.base_color = node.inputs['Color']
    node.shader.emission = node.inputs['Color']
    node.shader.alpha = [1.0]


def ShaderNodeBsdfGlossy(node):
    node.shader.base_color = node.inputs['Color']
    node.shader.metallic = [1.0]
    node.shader.roughness = node.inputs['Roughness']
    node.shader.transmission = [0.0]
    node.shader.emission = [0.0, 0.0, 0.0, 1.0]
    node.shader.alpha = [1.0]
    node.shader.normal = node.inputs['Normal']


def ShaderNodeBsdfRefraction(node):
    node.shader.base_color = node.inputs['Color']
    node.shader.metallic = [0.0]
    node.shader.specular = [0.0]
    node.shader.specular_tint = [1.0]
    node.shader.roughness = [0.0]
    node.shader.ior = node.inputs['IOR']
    node.shader.transmission = [1.0]
    node.shader.transmission_roughness = node.inputs['Roughness']
    node.shader.emission = [0.0, 0.0, 0.0, 1.0]
    node.shader.alpha = [1.0]
    node.shader.normal = node.inputs['Normal']


def ShaderNodeBsdfGlass(node):
    node.shader.base_color = node.inputs['Color']
    node.shader.metallic = [0.0]
    node.shader.specular_tint = [1.0]
    node.shader.roughness = [0.0]
    node.shader.ior = node.inputs['IOR']
    node.shader.transmission = [1.0]
    node.shader.transmission_roughness = node.inputs['Roughness']
    node.shader.emission = [0.0, 0.0, 0.0, 1.0]
    node.shader.alpha = [1.0]
    node.shader.normal = node.inputs['Normal']
    # for usda convert
    if "filepath" in target.keywords:
        SetMixRGB(node.shader.alpha, Blend.DIF, 1.0, node.inputs['Color'], [1.0, 1.0, 1.0])


def ShaderNodeBsdfTransparent(node):
    node.shader.base_color = node.inputs['Color']
    node.shader.specular = [0.0]
    node.shader.roughness = [1.0]
    node.shader.emission = [0.0, 0.0, 0.0, 1.0]
    SetMixRGB(node.shader.alpha, utils.Blend.SUB, 1.0, [1, 1, 1], node.inputs['Color'])
    # for usda convert
    if "filepath" in target.keywords:
        SetMixRGB(node.shader.alpha, Blend.DIF, 1.0, node.inputs['Color'], [1.0, 1.0, 1.0])


def ShaderNodeBsdfTranslucent(node):
    node.shader.base_color = node.inputs['Color']
    node.shader.specular = [0.0]
    node.shader.roughness = [1.0]
    node.shader.transmission = [0.0]
    node.shader.emission = [0.0, 0.0, 0.0, 1.0]
    node.shader.alpha = [1.0]
    node.shader.normal = node.inputs['Normal']


def ShaderNodeBsdfVelvet(node):
    SetMixRGB(node.shader.base_color, utils.Blend.MUL, 1.0, node.inputs['Color'], node.inputs['Sigma'])
    node.shader.specular = [0.0]
    node.shader.roughness = [1.0]
    node.shader.transmission = [0.0]
    node.shader.emission = [0.0, 0.0, 0.0, 1.0]
    node.shader.alpha = [1.0]
    node.shader.normal = node.inputs['Normal']


def ShaderNodeBsdfHairPrincipled(node):
    node.shader.base_color = node.inputs['Color']
    node.shader.specular = [0.0]
    node.shader.roughness = node.inputs['Roughness']
    node.shader.ior = node.inputs['IOR']
    node.shader.transmission = [0.0]
    node.shader.emission = [0.0, 0.0, 0.0, 1.0]
    node.shader.alpha = [1.0]


def ShaderNodeBsdfAnisotropic(node):
    node.shader.base_color = node.inputs['Color']
    node.shader.metallic = [1.0]
    node.shader.roughness = node.inputs['Roughness']
    ani = node.inputs['Anisotropy']
    if type(ani) is float:
        if ani > 0.0:
            SetMixRGB(node.shader.anisotropic, Blend.ADD, 1.0, ani, [0.2])
            SetMixRGB(node.shader.anisotropic_rotation, Blend.ADD, 1.0, node.inputs['Rotation'], [0.25])
        else:
            SetMixRGB(node.shader.anisotropic, Blend.ADD, 1.0, -ani, [0.2])
            node.shader.anisotropic_rotation = node.inputs['Rotation']
    else:
        node.shader.anisotropic = node.inputs['Anisotropy']
        node.shader.anisotropic_rotation = node.inputs['Rotation']
    node.shader.transmission = [0.0]
    node.shader.emission = [0.0, 0.0, 0.0, 1.0]
    node.shader.alpha = [1.0]
    node.shader.normal = node.inputs['Normal']
    node.shader.tangent = node.inputs['Tangent']


def ShaderNodeBsdfHair(node):
    node.shader.base_color = node.inputs['Color']
    node.shader.transmission = [0.0]
    node.shader.emission = [0.0, 0.0, 0.0, 1.0]
    node.shader.alpha = [1.0]
    node.shader.tangent = node.inputs['Tangent']


def ShaderNodeBsdfToon(node):
    if type(node.inputs['Size']) is float and node.inputs['Size'] == 0.0:
        node.shader.base_color = [0.0, 0.0, 0.0, 1.0]
    else:
        node.shader.base_color = node.inputs['Color']
    node.shader.metallic = [1.0]
    node.shader.specular = [0.0]
    rough = node.shader.roughness[:]
    SetMixRGB(rough, Blend.ADD, 2.0, node.inputs['Smooth'], node.inputs['Size'])
    node.shader.transmission = [0.0]
    node.shader.emission = [0.0, 0.0, 0.0, 1.0]
    node.shader.alpha = [1.0]


def ShaderNodeSubsurfaceScattering(node):
    node.shader.base_color = [0.0, 0.0, 0.0, 1.0]
    node.shader.subsurface = [0.0]
    node.shader.subsurface_radius = node.inputs['Radius']
    node.shader.subsurface_color = node.inputs['Color']
    node.shader.metallic = [0.0]
    node.shader.specular = [0.0]
    node.shader.transmission = [0.0]
    node.shader.emission = [0.0, 0.0, 0.0, 1.0]
    node.shader.alpha = [1.0]
    node.shader.normal = node.inputs['Normal']


def ShaderNodeHoldout(node):
    node.shader.alpha = [0.0]
