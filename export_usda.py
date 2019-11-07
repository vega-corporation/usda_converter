import bpy
import numpy as np
import os
import shutil

from . import usda_shader
from . import usda_mesh
from . import keywords



def usd_obj_name(name):
    usd_name = name.replace(",", "_").replace(".", "_").replace("-", "_").replace(" ", "")
    if len(name) > 0 and name[0].isdecimal():
        usd_name = "_"+usd_name
    return usd_name


def ConvertUsdaMeshes(objects, usda_meshes):
    usda = ""
    for obj in objects:
        usda_mesh = usda_meshes[obj.data.name]
        mesh_name = usd_obj_name(obj.name)

        extent = [tuple(np.array(obj.bound_box[0])*100), tuple(np.array(obj.bound_box[6])*100)]

        faceVertexCounts = usda_mesh.faceVertexCounts
        faceVertexIndices = usda_mesh.faceVertexIndices
        points = usda_mesh.points
        normals = usda_mesh.normal
        normals_indices = usda_mesh.normal_indices

        # translate object for usda
        # translate = tuple(np.array([obj.location[0], obj.location[1], obj.location[2]])*100)
        # rotateXYZ = (obj.rotation_euler[0]*180/np.pi, obj.rotation_euler[1]*180/np.pi, obj.rotation_euler[2]*180/np.pi)
        # scale = tuple(obj.scale)

        usda += """

def Mesh """+'"'+mesh_name+'"'+"""
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

#         usda += """
#     double3 xformOp:translate = """+str(translate)+"""
#     float3 xformOp:rotateXYZ = """+str(rotateXYZ)+"""
#     float3 xformOp:scale = """+str(scale)+"""
#     uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:rotateXYZ", "xformOp:scale"]

#     uniform token subdivisionScheme = "none"

# """
    # Parameters not reflected in usdz
    # uniform bool doubleSided = 1
    # uint ambientOcclusionSamples = 5
    # float cameraLightIntensity = 10

        for i, mat in enumerate(obj.material_slots):
            # deduplication
            for ii in range(i):
                if mat.name == obj.material_slots[ii].name:
                    break
            else:
                mat_name = usd_obj_name(mat.name)
                usda += """
    def GeomSubset """+'"'+mat_name+'"'+"""
    {
        uniform token elementType = "face"
        uniform token familyName = "materialBind"
        int[] indices = """+str(usda_mesh.mat_indices[mat.name])+"""
        rel material:binding = </Materials/"""+mat_name+""">
    }"""

        usda += """
}


"""
    return usda



def ConvertUsdaMaterials(usda_shaders):
    usda = ""
    usda += """
def "Materials"
{"""

    for mat_name in usda_shaders:
        shader = usda_shaders[mat_name]
        mat_name = usd_obj_name(mat_name)

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



def ExportUsda(objects, usda_meshes, usda_shaders):
    # export usda
    scn = bpy.context.scene
    usda = """#usda 1.0
("""
    if keywords.key["use_animation"]:
        usda += """
    startTimeCode = """+str(scn.frame_start)+"""
    endTimeCode = """+str(scn.frame_end)+"""
    timeCodesPerSecond = """+str(60.0*scn.render.frame_map_new/scn.render.frame_map_old)

    usda += """
    upAxis = "Z"
)"""
    usda += ConvertUsdaMeshes(objects, usda_meshes)
    usda += ConvertUsdaMaterials(usda_shaders)

    with open(keywords.key["filepath"], mode="w", encoding="utf-8") as f:
        f.write(usda)
    