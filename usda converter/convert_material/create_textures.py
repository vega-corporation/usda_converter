import bpy
import numpy as np
import shutil
import os

from .. import keywords
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



def CompositeTree(tex_dir, scn, mat, socket, name, make_image_flag = True):
    if not socket.links or not keywords.key["use_composite"]:
        return
    from_node = socket.links[0].from_node
    from_socket = socket.links[0].from_socket
    tex_path = None

    # make output path
    mat_name = mat.name.replace("/", "_").replace(" ", "")
    name = name.replace("/", "_").replace(" ", "")
    mat_dir = os.path.join(tex_dir, mat_name)

    # copy texture if no change
    if from_node.type == 'TEX_IMAGE':
        filepath = from_node.image.filepath_from_user()
        if os.path.exists(filepath):
            ext = os.path.splitext(filepath)[1]
            tex_path = os.path.join(mat_dir, name+ext)
            os.makedirs(mat_dir, exist_ok=True)
            shutil.copy(filepath, tex_path)
        else:
            return None
    # make composite texture
    else:
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
            tex_path = os.path.join(mat_dir, name+".png")
            scn.render.filepath = tex_path
            bpy.ops.render.render(scene=scn.name, write_still=True)
        # delete composite tree
        extree.DeleteNodes()
            
    # link mat socket to image
    if make_image_flag:
        mat.node_tree.links.remove(socket.links[0])
        if tex_path:
            image_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
            image = bpy.data.images.load(tex_path)
            image_node.image = image
            mat.node_tree.links.new(image_node.outputs['Color'], socket)

    return tex_path



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



def CreateTexturesPrincipled(mat, output_dir):
    # create new scene
    scn = CreateSceneComposite()
    principled = GetPrincipledShader(mat)

    CompositeTree(output_dir, scn, mat, principled.inputs['Base Color'], 'Base_Color')
    CompositeTree(output_dir, scn, mat, principled.inputs['Subsurface'], 'Subsurface')
    CompositeTree(output_dir, scn, mat, principled.inputs['Subsurface Radius'], 'Subsurface_Radius')
    CompositeTree(output_dir, scn, mat, principled.inputs['Subsurface Color'], 'Subsurface_Color')
    CompositeTree(output_dir, scn, mat, principled.inputs['Metallic'], 'Metallic')
    CompositeTree(output_dir, scn, mat, principled.inputs['Specular'], 'Specular')
    CompositeTree(output_dir, scn, mat, principled.inputs['Specular Tint'], 'Specular_Tint')
    CompositeTree(output_dir, scn, mat, principled.inputs['Roughness'], 'Roughness')
    CompositeTree(output_dir, scn, mat, principled.inputs['Anisotropic'], 'Anisotropic')
    CompositeTree(output_dir, scn, mat, principled.inputs['Anisotropic Rotation'], 'Anisotropic_Rotation')
    CompositeTree(output_dir, scn, mat, principled.inputs['Sheen'], 'Sheen')
    CompositeTree(output_dir, scn, mat, principled.inputs['Sheen Tint'], 'Sheen_Tint')
    CompositeTree(output_dir, scn, mat, principled.inputs['Clearcoat'], 'Clearcoat')
    CompositeTree(output_dir, scn, mat, principled.inputs['Clearcoat Roughness'], 'Clearcoat_Roughness')
    CompositeTree(output_dir, scn, mat, principled.inputs['IOR'], 'IOR')
    CompositeTree(output_dir, scn, mat, principled.inputs['Transmission'], 'Transmission')
    CompositeTree(output_dir, scn, mat, principled.inputs['Transmission Roughness'], 'Transmission_Roughness')
    CompositeTree(output_dir, scn, mat, principled.inputs['Emission'], 'Emission')
    CompositeTree(output_dir, scn, mat, principled.inputs['Alpha'], 'Alpha')
    CompositeTree(output_dir, scn, mat, principled.inputs['Normal'], 'Normal')
    CompositeTree(output_dir, scn, mat, principled.inputs['Clearcoat Normal'], 'Clearcoat_Normal')
    CompositeTree(output_dir, scn, mat, principled.inputs['Tangent'], 'Tangent')

    # delete scene
    bpy.data.scenes.remove(scn)



def CreateTexturesUsda(mat, tex_dir):
    # create new scene
    scn = CreateSceneComposite()
    principled = GetPrincipledShader(mat)
    mat_name = mat.name.replace("/", "_").replace(" ", "")
    usd_tex_dir = os.path.basename(tex_dir)+'/'+mat_name

    # shader parameter
    shader = usda_shader.UsdaShader()
    def SetUsdaColor(color, socket, name):
        _color = None
        path = CompositeTree(tex_dir, scn, mat, socket, name, False)
        if path:
            _color = [usda_shader.UsdaTexture()]
            _color[0].file = usd_tex_dir+'/'+name+os.path.splitext(path)[1]
        else:
            _color = utils.GetColor(socket.default_value, len(color))
        color.clear()
        color.extend(_color)
    
    SetUsdaColor(shader.diffuseColor, principled.inputs['Base Color'], 'diffuseColor')
    SetUsdaColor(shader.emissiveColor, principled.inputs['Emission'], 'emissiveColor')
    SetUsdaColor(shader.metallic, principled.inputs['Metallic'], 'metallic')
    SetUsdaColor(shader.roughness, principled.inputs['Roughness'], 'roughness')
    SetUsdaColor(shader.clearcoat, principled.inputs['Clearcoat'], 'clearcoat')
    SetUsdaColor(shader.clearcoatRoughness, principled.inputs['Clearcoat Roughness'], 'clearcoatRoughness')
    SetUsdaColor(shader.opacity, principled.inputs['Alpha'], 'opacity')
    SetUsdaColor(shader.ior, principled.inputs['IOR'], 'ior')
    SetUsdaColor(shader.normal, principled.inputs['Normal'], 'normal')
    SetUsdaColor(shader.displacement, principled.outputs['BSDF'].links[0].to_node.inputs['Displacement'], 'displacement')

    # delete scene
    bpy.data.scenes.remove(scn)

    return shader
