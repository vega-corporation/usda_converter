
if "bpy" in locals():
    import importlib
    importlib.reload(node_utils)
    importlib.reload(usda_shader)
    importlib.reload(create_shader_tree)
    importlib.reload(create_textures)
    importlib.reload(shader_function)
    importlib.reload(color_function)
else:
    from . import node_utils
    from . import usda_shader
    from . import create_shader_tree
    from . import create_textures
    from . import shader_function
    from . import color_function

import bpy
from .. import utils
from ..utils import Rename
import os




def ConvertMaterialShader():
    # make dir
    if utils.keywords["make_new_textures"]:
        os.makedirs(utils.asset_dir, exist_ok=True)
    
    # utils materials
    materials = []
    for obj in utils.objects:
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



def ConvertMaterials(usda):
    usda.append("""
    
def "Materials"
{""")

    shaders = ConvertMaterialShader()
    
    for mat_name in shaders:
        shader = shaders[mat_name]
        mat_name = Rename(mat_name)

        usda.append(f"""

    def Material "{mat_name}"
    {{
        token outputs:displacement.connect = </Materials/{mat_name}/PBRShader.outputs:displacement>
        token outputs:surface.connect = </Materials/{mat_name}/PBRShader.outputs:surface>
        
        def Shader "PBRShader"
        {{
            uniform token info:id = "UsdPreviewSurface\""""
        )

        def GetUsdaShader(usda, value, inputs_txt, texture_txt):
            if type(value[0]) is usda_shader.UsdaTexture:
                usda.append(f"""
            {inputs_txt}.connect = </Materials/{mat_name}/{texture_txt}"""
                )
            else:
                color = value[0] if len(value) == 1 else tuple(value)
                usda.append(f"""
            {inputs_txt} = {color}"""
                )

        GetUsdaShader(usda, shader.diffuseColor, "color3f inputs:diffuseColor", "diffuse_map.outputs:rgb>")
        GetUsdaShader(usda, shader.emissiveColor, "color3f inputs:emissiveColor", "emission_map.outputs:rgb>")
        GetUsdaShader(usda, shader.metallic, "float inputs:metallic", "metalness_map.outputs:r>")
        GetUsdaShader(usda, shader.roughness, "float inputs:roughness", "roughness_map.outputs:r>")
        GetUsdaShader(usda, shader.clearcoat, "float inputs:clearcoat", "clearcoat_map.outputs:r>")
        GetUsdaShader(usda, shader.clearcoatRoughness, "float inputs:clearcoatRoughness", "clearcoatroughness_map.outputs:r>")
        GetUsdaShader(usda, shader.opacity, "float inputs:opacity", "opacity_map.outputs:r>")
        GetUsdaShader(usda, shader.ior, "float inputs:ior", "ior_map.outputs:r>")
        GetUsdaShader(usda, shader.normal, "normal3f inputs:normal", "normal_map.outputs:rgb>")
        GetUsdaShader(usda, shader.displacement, "float inputs:displacement", "displacement_map.outputs:r>")
        
        usda.append("""
            token outputs:displacement
            token outputs:surface
        }

        def Shader "PrimvarUv"
        {
            uniform token info:id = "UsdPrimvarReader_float2"
            float2 inputs:fallback = (0, 0)
            token inputs:varname = "uv"
            float2 outputs:result
        }"""
        )

        def GetUsdaShaderImage(usda, usda_texture, shader_name, output):
            if type(usda_texture[0]) is usda_shader.UsdaTexture:
                usda.append(f"""
            
        def Shader "{shader_name}"
        {{
            uniform token info:id = "UsdUVTexture"
            float4 inputs:default = (0, 0, 0, 1)
            asset inputs:file = @{usda_texture[0].file}@
            float2 inputs:st.connect = </Materials/{mat_name}/PrimvarUv.outputs:result>
            token inputs:wrapS = "repeat"
            token inputs:wrapT = "repeat"
            float3 outputs:{output}
        }}"""
                )

        GetUsdaShaderImage(usda, shader.diffuseColor, "diffuse_map", "rgb")
        GetUsdaShaderImage(usda, shader.emissiveColor, "emission_map", "rgb")
        GetUsdaShaderImage(usda, shader.metallic, "metalness_map", "r")
        GetUsdaShaderImage(usda, shader.roughness, "roughness_map", "r")
        GetUsdaShaderImage(usda, shader.clearcoat, "clearcoat_map", "r")
        GetUsdaShaderImage(usda, shader.clearcoatRoughness, "clearcoatroughness_map", "r")
        GetUsdaShaderImage(usda, shader.opacity, "opacity_map", "r")
        GetUsdaShaderImage(usda, shader.ior, "ior_map", "r")
        GetUsdaShaderImage(usda, shader.normal, "normal_map", "rgb")
        GetUsdaShaderImage(usda, shader.displacement, "displacement_map", "r")
        
        usda.append("""
    }""")

    usda.append("""
}""")
