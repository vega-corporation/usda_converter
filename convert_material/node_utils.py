import bpy
import copy




class PBRShader():
    def __init__(self):
        self.base_color = [None, None, None, None]
        self.subsurface = [None]
        self.subsurface_radius = [None, None, None]
        self.subsurface_color = [None, None, None, None]
        self.metallic = [None]
        self.specular = [None]
        self.specular_tint = [None]
        self.roughness = [None]
        self.anisotropic = [None]
        self.anisotropic_rotation = [None]
        self.sheen = [None]
        self.sheen_tint = [None]
        self.clearcoat = [None]
        self.clearcoat_roughness = [None]
        self.ior = [None]
        self.transmission = [None]
        self.transmission_roughness = [None]
        self.emission = [None, None, None, None]
        self.alpha = [None]
        self.normal = [None, None, None]
        self.clearcoat_normal = [None, None, None]
        self.tangent = [None, None, None]
        self.mute = False

    def Copy(self, shader):
        self.__dict__ = copy.deepcopy(shader.__dict__)

    def Mute(self):
        self.base_color = [0.0, 0.0, 0.0, 1.0]
        self.emission = [0.0, 0.0, 0.0, 1.0]
        self.specular = [0.0]
        self.mute = True


class Blend():
    MIX = 'MIX'
    ADD = 'ADD'
    SUB = 'SUBTRACT'
    MUL = 'MULTIPLY'
    DIF = 'DIFFERENCE'


class ShaderMixRGB():
    def __init__(self, blend, fac, color1, color2):
        self.blend = blend
        self.fac = fac
        self.color1 = color1
        self.color2 = color2


class ShaderNode():
    def __init__(self, node):
        self.node = node
        self.shader = PBRShader()
        self.inputs = {}


class CompositeSocketParam():
    def __init__(self, comp_socket, comp_id, mat_socket, mat_id):
        self.comp_socket = comp_socket
        self.comp_id = comp_id
        self.mat_socket = mat_socket
        self.mat_id = mat_id


class CompositeNode():
    render_resolution = [32, 32]
    
    def __init__(self, node):
        self.node = node
        self.outputs = []
        self.inputs = []
    
    def AddInputs(self, comp_socket, mat_socket):
        comp_socket.default_value = mat_socket.default_value
        socket = CompositeSocketParam(comp_socket, comp_socket.identifier, mat_socket, mat_socket.identifier)
        self.inputs.append(socket)

    def AddOutputs(self, comp_socket, mat_socket):
        socket = CompositeSocketParam(comp_socket, comp_socket.identifier, mat_socket, mat_socket.identifier)
        self.outputs.append(socket)



class NodeTreeEx():
    def __init__(self, tree):
        self.tree = tree
        self.nodes = []# append node
        self.original_output = None

    def __del__(self):
        # remove nodes
        for node in self.nodes:
            node.id_data.nodes.remove(node)
        if self.original_output:
            self.original_output.is_active_output = True
        
    def AddNode(self, node_id):
        node = self.tree.nodes.new(node_id)
        self.nodes.append(node)
        return node





# returns color array of the specified lenth
def GetColor(color, lenth):
    # color to list
    if type(color) is bpy.types.bpy_prop_array:
        color = list(color)
    elif type(color) is float:
        color = [color]
    elif type(color) is not list:
        return [color]

    if type(color[0]) is int:
        color = [float(a) for a in color]
    if type(color[0]) is not float:
        return color
        
    # fix length
    if lenth == 1:
        if len(color) == 1:
            return color
        return [sum(color[:3])/3]
    elif lenth == 3:
        if len(color) == 1:
            return [color[0], color[0], color[0]]
        return color[:3]
    else:# len(param) == 4
        if len(color) == 1:
            return [color[0], color[0], color[0], 1.0]
        if len(color) == 3:
            return [color[0], color[1], color[2], 1.0]
        return color
