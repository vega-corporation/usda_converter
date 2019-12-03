

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
    importlib.reload(utils)
    importlib.reload(convert_material)
    importlib.reload(convert_mesh)
    importlib.reload(convert_armature)
    importlib.reload(export_usda)
else:
    from . import utils
    from . import convert_material
    from . import convert_mesh
    from . import convert_armature
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

    selection_only: BoolProperty(
            name="Selection Only",
            description="Export selected objects only",
            default=False,
            )
    up_axis: EnumProperty(
            name="Axis",# USD can specify Y or Z axis
            items=( ('Z', "Z Up Y Forward", ""),
                    ('Y', "Y Up -Z Forward", ""),
                  ),
            default='Z',
            )
    apply_modifiers: BoolProperty(
            name="Apply Modifiers",
            description="Apply modifiers: may conflict with armature or animation",
            default=False,
            )
    include_uvs: BoolProperty(
            name="Include UVs",
            description="Write out the active UV coordinates",
            default=True,
            )
    mesh_triangulate: BoolProperty(
            name="Triangulate Faces",
            description="Convert all faces to triangles",
            default=True,
            )
    include_animation: BoolProperty(
            name="Include Animation",
            description="Write out Animations",
            default=True,
            )
    include_armatures: BoolProperty(
            name="Include Armatures",
            description="Write out the Armatures",
            default=True,
            )
    make_new_textures: BoolProperty(
            name="Make New Textures",
            description="Generate the new textures from shader data",
            default=True,
            )
            

    def draw(self, context):
        layout = self.layout
        main_col = self.layout.box().column()
        main_col.prop(self, "selection_only")
        main_col.prop(self, "up_axis")

        mesh_col = self.layout.box().column()
        mesh_col.label(text="Mesh:", icon='MESH_DATA')
        mesh_col.prop(self, "apply_modifiers")
        mesh_col.prop(self, "include_uvs")
        mesh_col.prop(self, "mesh_triangulate")

        anim_col = self.layout.box().column()
        anim_col.label(text="Animation:", icon='ANIM_DATA')
        anim_col.prop(self, "include_animation")

        arm_col = self.layout.box().column()
        arm_col.label(text="Armature:", icon='ARMATURE_DATA')
        arm_col.prop(self, "include_armatures")

        tex_col = self.layout.box().column()
        tex_col.label(text="Texture:", icon='TEXTURE_DATA')
        tex_col.prop(self, "make_new_textures")
    

    check_extension = True

    def execute(self, context):
        utils.SetTargets(self.as_keywords())
        
        # export usda
        export_usda.ExportUsda()

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

