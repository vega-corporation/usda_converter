

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
    importlib.reload(target)
    importlib.reload(usda_shader)
    importlib.reload(convert_material)
    importlib.reload(convert_mesh)
    importlib.reload(export_usda)
else:
    from . import target
    from . import usda_shader
    from . import convert_material
    from . import convert_mesh
    from . import export_usda

import bpy
from bpy.props import (
        BoolProperty,
        StringProperty,
        FloatProperty,
        EnumProperty,
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
    include_animation: BoolProperty(
            name="Include　Animation",
            description="Write out an OBJ for each frame",
            default=True,
            )
    apply_modifiers: BoolProperty(
            name="Apply Modifiers",
            description="Apply modifiers",
            default=True,
            )
    include_uvs: BoolProperty(
            name="Include UVs",
            description="Write out the active UV coordinates",
            default=True,
            )
    use_new_textures: BoolProperty(
            name="Write Textures",
            description="Write out the textures file",
            default=True,
            )
    up_axis: EnumProperty(
            name="Axis",# USD can specify Y or Z axis
            items=( ('Z', "Z Up Y Forward", ""),
                    ('Y', "Y Up -Z Forward", ""),
                  ),
            default='Z',
            )

    def draw(self, context):
        layout = self.layout
        main_col = self.layout.box().column()
        main_col.prop(self, "use_selection")
        main_col.prop(self, "up_axis")
        mesh_col = self.layout.box().column()
        mesh_col.label(text="Mesh:", icon='MESH_DATA')
        mesh_col.prop(self, "include_animation")
        mesh_col.prop(self, "apply_modifiers")
        mesh_col.prop(self, "include_uvs")
        tex_col = self.layout.box().column()
        tex_col.label(text="Texture:", icon='TEXTURE_DATA')
        tex_col.prop(self, "use_new_textures")
    

    check_extension = True

    def execute(self, context):
        target.SetTargets(self.as_keywords())

        # get usda shader and mesh
        tex_dir = os.path.splitext(target.keywords["filepath"])[0] + '_assets'
        usda_meshes = convert_mesh.GetMeshDataAll()
        usda_shaders = convert_material.ConvertMaterialUsda(tex_dir)
        
        # export usda
        export_usda.ExportUsda(usda_meshes, usda_shaders)

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

