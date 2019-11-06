

bl_info = {
	"name" : "usda converter",
    "author" : "Nobuo Moritake",
    "version" : (1,0),
    "blender" : (2, 80, 0),
    "location" : "File > Import-Export",
    "description" : "export models (.usda)",
    "warning" : "",
    "wiki_url" : "",
    "tracker_url" : "",
    "category" : "Import-Export"
}


import os
import shutil

if "bpy" in locals():
    import importlib
    importlib.reload(keywords)
    importlib.reload(usda_shader)
    importlib.reload(convert_material)
    importlib.reload(convert_mesh)
    importlib.reload(export_usda)
else:
    from . import keywords
    from . import usda_shader
    from . import convert_material
    from . import convert_mesh
    from . import export_usda

import bpy
from bpy.props import (
        BoolProperty,
        StringProperty,
        )
from bpy_extras.io_utils import (
        ExportHelper,
        )



class ExportUsda(bpy.types.Operator, ExportHelper):
    bl_idname = 'export_usda.usda'
    bl_label = 'Export Usda'
    bl_description = 'Export Usda file (.usda)'
    bl_options = {'PRESET'}

    filename_ext = ".usda"
    filter_glob: StringProperty(
            default="*.usda",
            options={'HIDDEN'},
            )

    use_selection: BoolProperty(
            name="Selection Only",
            description="Export selected objects only",
            default=False,
            )
    # use_animation: BoolProperty(
    #         name="Animation",
    #         description="Write out an OBJ for each frame",
    #         default=False,
    #         )
    use_mesh_modifiers: BoolProperty(
            name="Apply Modifiers",
            description="Apply modifiers",
            default=True,
            )
    use_uvs: BoolProperty(
            name="Include UVs",
            description="Write out the active UV coordinates",
            default=True,
            )
    use_composite: BoolProperty(
            name="Write Textures",
            description="Write out the textures file",
            default=True,
            )

    check_extension = True


    def execute(self, context):
        keywords.SetKeywords(self.as_keywords())

        # target objects
        objects = [obj for obj in bpy.data.objects if obj.type == 'MESH']
        if keywords.key['use_selection']:
            objects = [obj for obj in objects if obj.select_get()]

        # get usda shader and mesh
        tex_dir = os.path.splitext(keywords.key["filepath"])[0] + '_textures'
        usda_shaders = convert_material.ConvertMaterialUsda(tex_dir, objects)
        usda_meshes = convert_mesh.GetMeshDataAll(objects)
        
        # export usda
        export_usda.ExportUsda(objects, usda_meshes, usda_shaders)

        return {'FINISHED'}



classes = (
    ExportUsda,
)

def menu_usda_export(self, context):
    self.layout.operator(ExportUsda.bl_idname, text="Usda (.usda)")

def register():
    for clas in classes:
        bpy.utils.register_class(clas)

    bpy.types.TOPBAR_MT_file_export.append(menu_usda_export)

def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(menu_usda_export)

    for clas in reversed(classes):
        bpy.utils.unregister_class(clas)


if __name__ == "__main__":
    register()
