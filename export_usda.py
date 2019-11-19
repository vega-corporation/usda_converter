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
        double3 xformOp:translate = """+str(tuple(np.array(obj.location)*100))+"""
        float3 xformOp:rotateXYZ = """+str(tuple(np.array(obj.rotation_euler)*180/np.pi))+"""
        float3 xformOp:scale = """+str(tuple(obj.scale))+"""
        uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:rotateXYZ", "xformOp:scale"]
        def SkelRoot "skelroot"""+'"'

        # references skel and mesh
        # payload or references other files are not supported by usdzconverter 0.61
        for mod in obj.modifiers:
            if mod.bl_rna.identifier == 'ArmatureModifier':
                usda += """(
            references = </Armatures/"""+Rename(mod.object.name)+""">
        )"""
                break
        
        mesh_name = obj.name if target.keywords["apply_modifiers"] else obj.data.name
        
        usda += """
        {
            def Mesh "mesh"(
                references = </Meshes/"""+Rename(mesh_name)+""">
            )
            {"""

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



def ExportUsda(usda_meshes, usda_materials):
    usda = "#usda 1.0"
    usda += UsdaInit()
    usda += UsdaObjects()
    usda += usda_meshes
    usda += usda_materials

    with open(target.keywords["filepath"], mode="w", encoding="utf-8") as f:
        f.write(usda)
    