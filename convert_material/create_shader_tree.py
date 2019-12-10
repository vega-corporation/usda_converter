
import bpy


from . import node_utils
from . import shader_function



def GetDefaultValue(socket):
    if socket.type == 'SHADER':
        shader = node_utils.PBRShader()
        shader.Mute()
        return shader
    if type(socket.default_value) == bpy.types.bpy_prop_array:
        return list(socket.default_value)
    else:
        return [socket.default_value]


def ShaderTraversal(node):
    # set inputs value
    for node_input in node.node.inputs:
        name = node_input.identifier
        node.inputs[name] = None
        if node_input.links and node_input.links[0].is_valid:
            link = node_input.links[0]
            if node_input.type == 'SHADER':
                if link.from_socket.type == 'SHADER':
                    new_node = node_utils.ShaderNode(link.from_node)
                    ShaderTraversal(new_node)
                    node.inputs[name] = new_node.shader
                else:
                    out = []
                    node.inputs[name] = node_utils.PBRShader()
                    node.inputs[name].base_color = [link.from_socket]
            else:
                node.inputs[name] = [link.from_socket]
        else:
            node.inputs[name] = GetDefaultValue(node_input)

    # set shader value
    shader_function.Handler(node)


def GenerateShaderData(mat):
    # get output node
    output_node = None
    for node in mat.node_tree.nodes:
        if node.type == 'OUTPUT_MATERIAL' and node.is_active_output:
            output_node = node
            break
    else:
        return None

    # generate pbr shader from node tree
    output_shader = node_utils.ShaderNode(output_node)
    ShaderTraversal(output_shader)
    
    return output_shader




def CreateColor(pbrtree, socket, color):
    if color[0] is None:
        return
    # mixrgb
    if type(color[0]) is node_utils.ShaderMixRGB:
        for col in color:
            mix_node = pbrtree.AddNode('ShaderNodeMixRGB')
            pbrtree.tree.links.new(mix_node.outputs['Color'], socket)
            mix_node.blend_type = col.blend
            CreateColor(pbrtree, mix_node.inputs['Fac'], col.fac)
            CreateColor(pbrtree, mix_node.inputs['Color1'], col.color1)
            CreateColor(pbrtree, mix_node.inputs['Color2'], col.color2)
    # value
    elif type(color[0]) is float or type(color[0]) is int:
        if type(socket.default_value) is float:
            socket.default_value = color[0]
        else:
            col = node_utils.GetColor(color, len(socket.default_value))
            socket.default_value = node_utils.GetColor(color, len(socket.default_value))
    # socket
    else:
        pbrtree.tree.links.new(color[0], socket)


def DeriveFromPrincipled(pbrtree, inputs, shader):
    CreateColor(pbrtree, inputs['Base Color'], shader.base_color)
    CreateColor(pbrtree, inputs['Subsurface'], shader.subsurface)
    CreateColor(pbrtree, inputs['Subsurface Radius'], shader.subsurface_radius)
    CreateColor(pbrtree, inputs['Subsurface Color'], shader.subsurface_color)
    CreateColor(pbrtree, inputs['Metallic'], shader.metallic)
    CreateColor(pbrtree, inputs['Specular'], shader.specular)
    CreateColor(pbrtree, inputs['Specular Tint'], shader.specular_tint)
    CreateColor(pbrtree, inputs['Roughness'], shader.roughness)
    CreateColor(pbrtree, inputs['Anisotropic'], shader.anisotropic)
    CreateColor(pbrtree, inputs['Anisotropic Rotation'], shader.anisotropic_rotation)
    CreateColor(pbrtree, inputs['Sheen'], shader.sheen)
    CreateColor(pbrtree, inputs['Sheen Tint'], shader.sheen_tint)
    CreateColor(pbrtree, inputs['Clearcoat'], shader.clearcoat)
    CreateColor(pbrtree, inputs['Clearcoat Roughness'], shader.clearcoat_roughness)
    CreateColor(pbrtree, inputs['IOR'], shader.ior)
    CreateColor(pbrtree, inputs['Transmission'], shader.transmission)
    CreateColor(pbrtree, inputs['Transmission Roughness'], shader.transmission_roughness)
    CreateColor(pbrtree, inputs['Emission'], shader.emission)
    CreateColor(pbrtree, inputs['Alpha'], shader.alpha)
    CreateColor(pbrtree, inputs['Normal'], shader.normal)
    CreateColor(pbrtree, inputs['Clearcoat Normal'], shader.clearcoat_normal)
    CreateColor(pbrtree, inputs['Tangent'], shader.tangent)




def AlignNode(tree, node, location, calc_f):
    # 計算済みならx軸方向のみ移動
    if calc_f[node.name]:
        node.location.x = location[0]
    else:
        node.location = location
        calc_f[node.name] = True
    loc = list(location)
    loc[0] -= 300
    calc_f[node.name] = True
    for socket in node.inputs:
        for link in socket.links:
            if link.from_node in tree.nodes:
                AlignNode(tree, link.from_node, loc, calc_f)
                loc[1] -= 200


def AlignNodes(tree, output):
    # outputから左に整列する
    if not output:
        return
    calc_f = {node.name:False for node in tree.nodes}
    AlignNode(tree, output, output.location, calc_f)


def AlignNodesRight(tree, output):
    AlignNodes(tree, output)
    # 全体を右側に配置する
    move = [0,0]
    locations_x = [node.location.x for node in tree.nodes]
    locations_y = [node.location.y for node in tree.nodes]
    move = [min(locations_x), max(locations_y)] # 左上の座標
    locations_x = [node.location.x for node in tree.tree.nodes if not node in tree.nodes]
    locations_y = [node.location.y for node in tree.tree.nodes if not node in tree.nodes]
    if locations_x:
        move = [max(locations_x)-move[0], max(locations_y)-move[1]] # 右上の座標 - 左上の座標
    else:
        mode = [0, 0]
    for node in tree.nodes:
        node.location.x += move[0] + 300
        node.location.y += move[1]




def CreateShaderTree(mat):
    data = GenerateShaderData(mat)
    
    # make output, principled shader
    tree = mat.node_tree
    pbrtree = node_utils.NodeTreeEx(tree)
    output = pbrtree.AddNode('ShaderNodeOutputMaterial')
    principled = pbrtree.AddNode('ShaderNodeBsdfPrincipled')
    tree.links.new(principled.outputs['BSDF'], output.inputs['Surface'])

    # activate output
    for node in tree.nodes:
        if node.type == 'OUTPUT_MATERIAL' and node.is_active_output:
            pbrtree.original_output = node
            node.is_active_output = False
            break
    output.is_active_output = True

    # link derivation
    if not data:
        AlignNodesRight(pbrtree, output)
        return pbrtree
        
    DeriveFromPrincipled(pbrtree, principled.inputs, data.inputs['Surface'])

    if data.node.inputs['Volume'].links:
        tree.links.new(data.node.inputs['Volume'].links[0].from_socket, output.inputs['Volume'])
    if data.node.inputs['Displacement'].links:
        tree.links.new(data.node.inputs['Displacement'].links[0].from_socket, output.inputs['Displacement'])

    # alignment
    AlignNodesRight(pbrtree, output)
    return pbrtree
