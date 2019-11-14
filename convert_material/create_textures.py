import bpy
import numpy as np
import shutil
import os

from .. import target
from .. import usda_shader
from . import utils
from . import color_function
    


def CompositeColor(extree, mat_socket):
    # make composite node correspond to mat
    comp = color_function.Handler(extree, mat_socket.node)
    if comp is None:
        return None

    # link inputs
    for socket in comp.inputs:
        if socket.mat_socket.links:
            from_mat_socket = socket.mat_socket.links[0].from_socket
            from_socket = CompositeColor(extree, from_mat_socket)
            # new link
            if from_socket:
                extree.tree.links.new(from_socket, socket.comp_socket)

    # return output socket
    node_output = None
    for socket in comp.outputs:
        if socket.mat_socket == mat_socket:
            node_output = socket.comp_socket
            break

    return node_output



def CompositeTree(tex_dir, scn, mat, color, socket, name):
    color_ = utils.GetColor(socket.default_value, len(color))
    color.clear()
    if not socket.links:
        color.extend(color_)
        return
        
    from_node = socket.links[0].from_node
    from_socket = socket.links[0].from_socket

    # make output path
    mat_name = mat.name.replace("/", "_").replace(" ", "")
    usd_tex_dir = os.path.basename(tex_dir)+'/'+mat_name
    name = name.replace("/", "_").replace(" ", "")
    mat_dir = os.path.join(tex_dir, mat_name)

    # copy texture if no change
    if from_node.type == 'TEX_IMAGE':
        filepath = from_node.image.filepath_from_user()
        if os.path.exists(filepath):
            if target.keywords["use_new_textures"]:
                ext = os.path.splitext(filepath)[1]
                tex_path = os.path.join(mat_dir, name+ext)
                os.makedirs(mat_dir, exist_ok=True)
                shutil.copy(filepath, tex_path)
                color_ = [usda_shader.UsdaTexture()]
                color_[0].file = usd_tex_dir+'/'+name+os.path.splitext(tex_path)[1]
            else:
                color_ = [usda_shader.UsdaTexture()]
                color_[0].file = filepath

    # make composite texture
    elif target.keywords["use_new_textures"]:
        # default render size
        utils.CompositeNode.render_resolution = [32, 32]
        # make composite tree
        extree = utils.NodeTreeEx(scn.node_tree)
        comp_socket = CompositeColor(extree, from_socket)
        if comp_socket:
            output_comp = extree.AddNode('CompositorNodeComposite')
            scn.node_tree.links.new(comp_socket, output_comp.inputs['Image'])
            # render
            scn.render.resolution_x = utils.CompositeNode.render_resolution[0]
            scn.render.resolution_y = utils.CompositeNode.render_resolution[1]
            scn.render.filepath = os.path.join(mat_dir, name+".png")
            bpy.ops.render.render(scene=scn.name, write_still=True)
    
            color_ = [usda_shader.UsdaTexture()]
            color_[0].file = usd_tex_dir+'/'+name+".png"

    color.extend(color_)
            



def CreateSceneComposite():
    scn = bpy.data.scenes.new("Scene")
    # composite setting
    scn.render.use_compositing = True
    scn.use_nodes = True
    scn.node_tree.nodes.clear()
    # render setting
    scn.view_settings.view_transform = 'Standard'
    scn.render.image_settings.file_format = 'PNG'
    return scn


def GetPrincipledShader(mat):
    principled = None
    for node in mat.node_tree.nodes:
        if node.type == 'OUTPUT_MATERIAL' and node.is_active_output:
            principled = node
            break
    principled = principled.inputs['Surface'].links[0].from_node
    return principled



def CreateTexturesUsda(mat, tex_dir):
    # create new scene
    scn = CreateSceneComposite()
    principled = GetPrincipledShader(mat)
    shader = usda_shader.UsdaShader()

    # shader parameter
    CompositeTree(tex_dir, scn, mat, shader.diffuseColor, principled.inputs['Base Color'], 'diffuseColor')
    CompositeTree(tex_dir, scn, mat, shader.emissiveColor, principled.inputs['Emission'], 'emissiveColor')
    CompositeTree(tex_dir, scn, mat, shader.metallic, principled.inputs['Metallic'], 'metallic')
    CompositeTree(tex_dir, scn, mat, shader.roughness, principled.inputs['Roughness'], 'roughness')
    CompositeTree(tex_dir, scn, mat, shader.clearcoat, principled.inputs['Clearcoat'], 'clearcoat')
    CompositeTree(tex_dir, scn, mat, shader.clearcoatRoughness, principled.inputs['Clearcoat Roughness'], 'clearcoatRoughness')
    CompositeTree(tex_dir, scn, mat, shader.opacity, principled.inputs['Alpha'], 'opacity')
    CompositeTree(tex_dir, scn, mat, shader.ior, principled.inputs['IOR'], 'ior')
    if principled.outputs['BSDF'].links[0].to_node.inputs['Displacement'].links:
        CompositeTree(tex_dir, scn, mat, shader.normal, principled.outputs['BSDF'].links[0].to_node.inputs['Displacement'], 'displacement')
    else:
        CompositeTree(tex_dir, scn, mat, shader.normal, principled.inputs['Normal'], 'normal')

    # delete scene
    bpy.data.scenes.remove(scn)

    return shader
