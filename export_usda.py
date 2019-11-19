import bpy
import numpy as np
import os
import shutil

from . import usda_shader
from . import target



def Rename(name):
    usd_name = name.replace(",", "_").replace(".", "_").replace("-", "_").replace(" ", "")
    if len(name) > 0 and name[0].isdecimal():
        usd_name = "_"+usd_name
    return usd_name



def UsdaInit():
    scn = bpy.context.scene
    usda = """#usda 1.0
(
    defaultPrim = "Objects"""+'"'

    if target.keywords["include_armatures"]:
        usda += """
    startTimeCode = """+str(scn.frame_start)+"""
    endTimeCode = """+str(scn.frame_end)+"""
    timeCodesPerSecond = """+str(60.0*scn.render.frame_map_old/scn.render.frame_map_new)

    usda += """
    upAxis = """+'"'+target.keywords["up_axis"]+'"'+"""
)"""
    return usda



def UsdaObjects():
    usda = """

def Scope "Objects"
{"""
    for obj in target.objects:
        usda += """
    def Xform """+'"'+Rename(obj.name)+'"'+"""
    {
        double3 xformOp:translate = """+str(tuple(obj.location))+"""
        float3 xformOp:rotateXYZ = """+str(tuple(np.array(obj.rotation_euler)*180/np.pi))+"""
        float3 xformOp:scale = """+str(tuple(obj.scale))+"""
        uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:rotateXYZ", "xformOp:scale"]
        def SkelRoot "skelroot"""+'"'

        # references skel and mesh
        # payload is not supported by usdzconverter 0.61
        for mod in obj.modifiers:
            if mod.bl_rna.identifier == 'ArmatureModifier':
                usda += """(
            references = </Armatures/"""+Rename(mod.object.name)+""">
        )"""
                break
        
        usda += """
        {
            def Mesh "mesh"(
                references = </Meshes/"""+Rename(obj.data.name)+""">
            )
            {"""

        mat_names = [ms.material.name for ms in obj.material_slots]
        mat_names = tuple(set(mat_names))
        for mat_name in mat_names:
            usda += """
                def GeomSubset """+'"'+Rename(mat_name)+'"'+"""
                {
                    uniform token elementType = "face"
                    uniform token familyName = "materialBind"
                    int[] indices = """+str(usda_meshes[obj.data.name].mat_indices[mat_name])+"""
                    rel material:binding = </Materials/"""+Rename(mat_name)+""">
                }"""
        usda += """
            }
        }
    }"""
    usda += """
}"""
    return usda



def ConvertUsdaMeshes(usda_meshes):
    usda = """

def Scope "Meshes"
{"""

    for obj in target.objects:
        usda_mesh = usda_meshes[obj.data.name]
        mesh_name = Rename(obj.data.name)

        extent = [tuple(np.array(obj.bound_box[0])*100), tuple(np.array(obj.bound_box[6])*100)]

        faceVertexCounts = usda_mesh.faceVertexCounts
        faceVertexIndices = usda_mesh.faceVertexIndices
        points = usda_mesh.points
        normals = usda_mesh.normal
        normals_indices = usda_mesh.normal_indices

        usda += """

    def """+'"'+mesh_name+'"'+"""
    {
        float3[] extent = """+str(extent)+"""
        int[] faceVertexCounts = """+str(faceVertexCounts)+"""
        int[] faceVertexIndices = """+str(faceVertexIndices)+"""
        point3f[] points = """+points+"""
        normal3f[] primvars:normals = """+normals+""" (
            interpolation = "faceVarying"
        )
        int[] primvars:normals:indices = """+normals_indices
        
        if usda_mesh.uv:
            usda += """
        texCoord2f[] primvars:uv = """+usda_mesh.uv+""" (
            interpolation = "faceVarying"
        )
        int[] primvars:uv:indices = """+usda_mesh.uv_indices

        usda += """
    }"""

    usda += """
}"""
    return usda



def ConvertUsdaMaterials(usda_shaders):
    usda = """
    
def "Materials"
{"""
    for mat_name in usda_shaders:
        shader = usda_shaders[mat_name]
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



def ExportUsda(usda_meshes, usda_shaders):
    usda = "#usda 1.0"
    usda += UsdaInit()
    usda += UsdaObjects()
    usda += usda_meshes
    usda += ConvertUsdaMaterials(usda_shaders)

    with open(target.keywords["filepath"], mode="w", encoding="utf-8") as f:
        f.write(usda)
    