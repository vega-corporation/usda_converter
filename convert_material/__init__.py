
if "bpy" in locals():
    import imp
    imp.reload(utils)
    imp.reload(create_shader_tree)
    imp.reload(create_textures)
    imp.reload(shader_function)
    imp.reload(color_function)
else:
    from . import utils
    from . import create_shader_tree
    from . import create_textures
    from . import shader_function
    from . import color_function

import bpy
from .. import keywords
from .. import usda_shader
import os




def ConvertMaterialUsda(tex_dir, objects):
    # make dir
    os.makedirs(tex_dir, exist_ok=True)
    
    # target materials
    materials = []
    for obj in objects:
        for mat in obj.material_slots:
            if mat.material not in materials:
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
        shader_data[mat.name] = create_textures.CreateTexturesUsda(mat, tex_dir)

        # delete PBR nodes
        tree.DeleteNodes()
    
    return shader_data



def ConvertMaterial(tex_dir):
    data = {}
    for mat in bpy.data.materials:
        # create PBR tree
        tree = create_shader_tree.CreateShaderTree(mat)

        # composit color
        composit_flag = False
        if composit_flag:
            create_textures.CreateTexturesPrincipled(mat, tex_dir)

        # remove inactive nodes
        remove_original_flag = False
        if remove_original_flag:
            create_shader_tree.RegenerateShaderTree(tree)
