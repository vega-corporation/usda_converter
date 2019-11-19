
if "bpy" in locals():
    import importlib
    importlib.reload(utils)
    importlib.reload(create_shader_tree)
    importlib.reload(create_textures)
    importlib.reload(shader_function)
    importlib.reload(color_function)
else:
    from . import utils
    from . import create_shader_tree
    from . import create_textures
    from . import shader_function
    from . import color_function

import bpy
from .. import target
from ..target import Rename
from .. import usda_shader
import os




def ConvertMaterial():
    # make dir
    if target.keywords["make_new_textures"]:
        os.makedirs(target.asset_dir, exist_ok=True)
    
    # target materials
    materials = []
    for obj in target.objects:
        for mat in obj.material_slots:
            if mat.material and mat.material not in materials:
                materials.append(mat.material)

    # convert materials
    shader_data = {}
    for mat in materials:
        if not mat.use_nodes:
            shader = usda_shader.UsdaShader()
            shader.diffuseColor = mat.diffuse_color[:3]
            shader_data[mat.name] = shader
            continue
        # create PBR tree
        tree = create_shader_tree.CreateShaderTree(mat)
        
        # composit color
        shader_data[mat.name] = create_textures.CreateTexturesUsda(mat)
    
    return shader_data



def ConvertMaterialUsda():
    usda = """
    
def "Materials"
{"""

    shaders = ConvertMaterial()
    
    for mat_name in shaders:
        shader = shaders[mat_name]
        mat_name = Rename(mat_name)

        usda += """

    def Material """+'"'+mat_name+'"'+"""
    {
        token outputs:displacement.connect = </Materials/"""+mat_name+"""/PBRShader.outputs:displacement>
        token outputs:surface.connect = </Materials/"""+mat_name+"""/PBRShader.outputs:surface>
        token inputs:frame:stPrimvarName = "uv"
        
        def Shader "PBRShader"
        {
            uniform token info:id = "UsdPreviewSurface" """

        def GetUsdaShader(value, inputs_txt, texture_txt):
            usda = ""
            if type(value[0]) is usda_shader.UsdaTexture:
                usda = """
            """+inputs_txt+""".connect = </Materials/"""+mat_name+"""/"""+texture_txt
            else:
                color = value[0] if len(value) == 1 else tuple(value)
                usda = """
            """+inputs_txt+""" = """+str(color)
            
            return usda

        usda += GetUsdaShader(shader.diffuseColor, "color3f inputs:diffuseColor", "diffuse_map.outputs:rgb>")
        usda += GetUsdaShader(shader.emissiveColor, "color3f inputs:emissiveColor", "emission_map.outputs:rgb>")
        usda += GetUsdaShader(shader.metallic, "float inputs:metallic", "metalness_map.outputs:r>")
        usda += GetUsdaShader(shader.roughness, "float inputs:roughness", "roughness_map.outputs:r>")
        usda += GetUsdaShader(shader.clearcoat, "float inputs:clearcoat", "clearcoat_map.outputs:r>")
        usda += GetUsdaShader(shader.clearcoatRoughness, "float inputs:clearcoatRoughness", "clearcoatroughness_map.outputs:r>")
        usda += GetUsdaShader(shader.opacity, "float inputs:opacity", "opacity_map.outputs:r>")
        usda += GetUsdaShader(shader.ior, "float inputs:ior", "ior_map.outputs:r>")
        usda += GetUsdaShader(shader.normal, "normal3f inputs:normal", "normal_map.outputs:rgb>")
        usda += GetUsdaShader(shader.displacement, "float inputs:displacement", "displacement_map.outputs:r>")
        
        usda += """
            token outputs:displacement
            token outputs:surface
        }

        def Shader "PrimvarUv"
        {
            uniform token info:id = "UsdPrimvarReader_float2"
            float2 inputs:default = (0, 0)
            token inputs:varname.connect = </Materials/"""+mat_name+""".inputs:frame:stPrimvarName>
            float2 outputs:result
        }"""

        def GetUsdaShaderImage(usda_texture, shader_name, output):
            if type(usda_texture[0]) is not usda_shader.UsdaTexture:
                return ""
                
            usda = """
            
        def Shader """+'"'+shader_name+'"'+"""
        {
            uniform token info:id = "UsdUVTexture"
            float4 inputs:default = (0, 0, 0, 1)
            asset inputs:file = @"""+usda_texture[0].file+"""@
            float2 inputs:uv.connect = </Materials/"""+mat_name+"""/PrimvarUv.outputs:result>
            token inputs:wrapS = "repeat"
            token inputs:wrapT = "repeat"
            float3 outputs:"""+output+"""
        }"""
            return usda

        usda += GetUsdaShaderImage(shader.diffuseColor, "diffuse_map", "rgb")
        usda += GetUsdaShaderImage(shader.emissiveColor, "emission_map", "rgb")
        usda += GetUsdaShaderImage(shader.metallic, "metalness_map", "r")
        usda += GetUsdaShaderImage(shader.roughness, "roughness_map", "r")
        usda += GetUsdaShaderImage(shader.clearcoat, "clearcoat_map", "r")
        usda += GetUsdaShaderImage(shader.clearcoatRoughness, "clearcoatroughness_map", "r")
        usda += GetUsdaShaderImage(shader.opacity, "opacity_map", "r")
        usda += GetUsdaShaderImage(shader.ior, "ior_map", "r")
        usda += GetUsdaShaderImage(shader.normal, "normal_map", "rgb")
        usda += GetUsdaShaderImage(shader.displacement, "displacement_map", "r")
        
        usda += """
    }"""

    usda += """
}"""
    return usda
