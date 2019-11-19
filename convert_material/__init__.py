
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
from .. import usda_shader
import os




def ConvertMaterialUsda(tex_dir):
    # make dir
    if target.keywords["make_new_textures"]:
        os.makedirs(tex_dir, exist_ok=True)
    
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
        shader_data[mat.name] = create_textures.CreateTexturesUsda(mat, tex_dir)
    
    return shader_data
