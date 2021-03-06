import bpy

from . import node_utils


def Handler(extree, mat_node):
    # create composite node and return socket
    if mat_node.bl_rna.identifier in globals():
        if mat_node.mute:
            return None
        else:
            return eval(mat_node.bl_rna.identifier)(extree, mat_node)
    else:
        return None


# input

def ShaderNodeTexImage(extree, mat_node):
    node = extree.AddNode('CompositorNodeImage')
    node.image = mat_node.image
    comp = node_utils.CompositeNode(node)
    comp.AddOutputs(node.outputs['Image'], mat_node.outputs['Color'])
    comp.AddOutputs(node.outputs['Alpha'], mat_node.outputs['Alpha'])
    node_utils.CompositeNode.render_resolution = mat_node.image.size[:]
    return comp


def ShaderNodeRGB(extree, mat_node):
    node = extree.AddNode('CompositorNodeRGB')
    comp = node_utils.CompositeNode(node)
    comp.AddOutputs(node.outputs['RGBA'], mat_node.outputs['Color'])
    return comp


def ShaderNodeValue(extree, mat_node):
    node = extree.AddNode('CompositorNodeValue')
    comp = node_utils.CompositeNode(node)
    comp.AddOutputs(node.outputs['Value'], mat_node.outputs['Value'])
    return comp


# color

def ShaderNodeMixRGB(extree, mat_node):
    node = extree.AddNode('CompositorNodeMixRGB')
    node.blend_type = mat_node.blend_type
    node.use_clamp = mat_node.use_clamp
    comp = node_utils.CompositeNode(node)
    for i in range(len(node.inputs)):
        comp.AddInputs(node.inputs[i], mat_node.inputs[i])
    for i in range(len(node.outputs)):
        comp.AddOutputs(node.outputs[i], mat_node.outputs[i])
    return comp


def ShaderNodeBrightContrast(extree, mat_node):
    node = extree.AddNode('CompositorNodeBrightContrast')
    comp = node_utils.CompositeNode(node)
    for i in range(len(node.inputs)):
        comp.AddInputs(node.inputs[i], mat_node.inputs[i])
    for i in range(len(node.outputs)):
        comp.AddOutputs(node.outputs[i], mat_node.outputs[i])
    return comp


def ShaderNodeInvert(extree, mat_node):
    node = extree.AddNode('CompositorNodeInvert')
    comp = node_utils.CompositeNode(node)
    for i in range(len(node.inputs)):
        comp.AddInputs(node.inputs[i], mat_node.inputs[i])
    for i in range(len(node.outputs)):
        comp.AddOutputs(node.outputs[i], mat_node.outputs[i])
    return comp


def ShaderNodeGamma(extree, mat_node):
    node = extree.AddNode('CompositorNodeGamma')
    comp = node_utils.CompositeNode(node)
    for i in range(len(node.inputs)):
        comp.AddInputs(node.inputs[i], mat_node.inputs[i])
    for i in range(len(node.outputs)):
        comp.AddOutputs(node.outputs[i], mat_node.outputs[i])
    return comp


def ShaderNodeHueSaturation(extree, mat_node):
    node = extree.AddNode('CompositorNodeHueSat')
    comp = node_utils.CompositeNode(node)
    comp.AddInputs(node.inputs['Image'], mat_node.inputs['Color'])
    comp.AddInputs(node.inputs['Hue'], mat_node.inputs['Hue'])
    comp.AddInputs(node.inputs['Saturation'], mat_node.inputs['Saturation'])
    comp.AddInputs(node.inputs['Value'], mat_node.inputs['Value'])
    comp.AddInputs(node.inputs['Fac'], mat_node.inputs['Fac'])
    for i in range(len(node.outputs)):
        comp.AddOutputs(node.outputs[i], mat_node.outputs[i])
    return comp


def ShaderNodeRGBCurve(extree, mat_node):
    node = extree.AddNode('CompositorNodeCurveRGB')
    node.mapping.tone = mat_node.mapping.tone
    for i, mat_curve in enumerate(mat_node.mapping.curves):
        comp_curve = node.mapping.curves[i]
        for i, mat_point in enumerate(mat_curve.points):
            if len(comp_curve.points) == i:
                comp_curve.points.new(mat_point.location.x, mat_point.location.y)
            comp_curve.points[i].location = mat_point.location
    comp = node_utils.CompositeNode(node)
    comp.AddInputs(node.inputs['Fac'], mat_node.inputs['Fac'])
    comp.AddInputs(node.inputs['Image'], mat_node.inputs['Color'])
    for i in range(len(node.outputs)):
        comp.AddOutputs(node.outputs[i], mat_node.outputs[i])
    return comp


# vector

def ShaderNodeNormalMap(extree, mat_node):
    node = extree.AddNode('CompositorNodeMixRGB')
    node.blend_type = 'MIX'
    strength = mat_node.inputs[0].default_value
    strength = 1.0 if strength > 1.0 else strength
    node.inputs[0].default_value = strength*strength
    node.inputs[1].default_value = (0.5, 0.5, 1.0, 1.0)
    comp = node_utils.CompositeNode(node)
    comp.AddInputs(node.inputs[2], mat_node.inputs[1])
    for i in range(len(node.outputs)):
        comp.AddOutputs(node.outputs[i], mat_node.outputs[i])
    return comp


def ShaderNodeNormal(extree, mat_node):
    node = extree.AddNode('CompositorNodeNormal')
    comp = node_utils.CompositeNode(node)
    for i in range(len(node.inputs)):
        comp.AddInputs(node.inputs[i], mat_node.inputs[i])
    for i in range(len(node.outputs)):
        comp.AddOutputs(node.outputs[i], mat_node.outputs[i])
    return comp


def ShaderNodeVectorCurve(extree, mat_node):
    node = extree.AddNode('CompositorNodeCurveVec')
    for i, mat_curve in enumerate(mat_node.mapping.curves):
        comp_curve = node.mapping.curves[i]
        for i, mat_point in enumerate(mat_curve.points):
            if len(comp_curve.points) == i:
                comp_curve.points.new(mat_point.location.x, mat_point.location.y)
            comp_curve.points[i].location = mat_point.location
    comp = node_utils.CompositeNode(node)
    comp.AddInputs(node.inputs[0], mat_node.inputs[1])
    for i in range(len(node.outputs)):
        comp.AddOutputs(node.outputs[i], mat_node.outputs[i])
    return comp


def ShaderNodeMapping(extree, mat_node):
    node = extree.AddNode('CompositorNodeCurveVec')
    comp = node_utils.CompositeNode(node)
    comp.AddInputs(node.inputs[0], mat_node.inputs[0])
    comp.AddOutputs(node.outputs[0], mat_node.outputs[0])
    return comp


def ShaderNodeVectorTransform(extree, mat_node):
    node = extree.AddNode('CompositorNodeCurveVec')
    comp = node_utils.CompositeNode(node)
    comp.AddInputs(node.inputs[0], mat_node.inputs[0])
    comp.AddOutputs(node.outputs[0], mat_node.outputs[0])
    return comp


def ShaderNodeVectorDisplacement(extree, mat_node):
    node = extree.AddNode('CompositorNodeMixRGB')
    node.inputs[0].default_value = 0.0
    comp = node_utils.CompositeNode(node)
    comp.AddInputs(node.inputs[1], mat_node.inputs[0])
    comp.AddOutputs(node.outputs[0], mat_node.outputs[0])
    return comp


def ShaderNodeBump(extree, mat_node):
    node = extree.AddNode('CompositorNodeCurveVec')
    comp = node_utils.CompositeNode(node)
    comp.AddInputs(node.inputs[0], mat_node.inputs[3])
    comp.AddOutputs(node.outputs[0], mat_node.outputs[0])
    return comp


def ShaderNodeDisplacement(extree, mat_node):
    node = extree.AddNode('CompositorNodeCurveVec')
    comp = node_utils.CompositeNode(node)
    comp.AddInputs(node.inputs[0], mat_node.inputs[3])
    comp.AddOutputs(node.outputs[0], mat_node.outputs[0])
    return comp


# converter

def ShaderNodeValToRGB(extree, mat_node):
    node = extree.AddNode('CompositorNodeValToRGB')
    node.color_ramp.color_mode = mat_node.color_ramp.color_mode
    node.color_ramp.interpolation = mat_node.color_ramp.interpolation
    elements = node.color_ramp.elements
    elements.remove(elements[1])
    for i, element in enumerate(mat_node.color_ramp.elements):
        if len(node.color_ramp.elements) == i:
            node.color_ramp.elements.new(1.0)
        node.color_ramp.elements[i].color = element.color
        node.color_ramp.elements[i].position = element.position
    comp = node_utils.CompositeNode(node)
    for i in range(len(node.inputs)):
        comp.AddInputs(node.inputs[i], mat_node.inputs[i])
    for i in range(len(node.outputs)):
        comp.AddOutputs(node.outputs[i], mat_node.outputs[i])
    return comp


def ShaderNodeCombineHSV(extree, mat_node):
    node = extree.AddNode('CompositorNodeCombHSVA')
    comp = node_utils.CompositeNode(node)
    for i in range(3):
        comp.AddInputs(node.inputs[i], mat_node.inputs[i])
    for i in range(len(node.outputs)):
        comp.AddOutputs(node.outputs[i], mat_node.outputs[i])
    return comp


def ShaderNodeCombineRGB(extree, mat_node):
    node = extree.AddNode('CompositorNodeCombRGBA')
    comp = node_utils.CompositeNode(node)
    for i in range(3):
        comp.AddInputs(node.inputs[i], mat_node.inputs[i])
    for i in range(len(node.outputs)):
        comp.AddOutputs(node.outputs[i], mat_node.outputs[i])
    return comp


def ShaderNodeCombineXYZ(extree, mat_node):
    node = extree.AddNode('CompositorNodeCombRGBA')
    comp = node_utils.CompositeNode(node)
    for i in range(3):
        comp.AddInputs(node.inputs[i], mat_node.inputs[i])
    for i in range(len(node.outputs)):
        comp.AddOutputs(node.outputs[i], mat_node.outputs[i])
    return comp


def ShaderNodeMath(extree, mat_node):
    node = extree.AddNode('CompositorNodeMath')
    node.operation = mat_node.operation
    node.use_clamp = mat_node.use_clamp
    comp = node_utils.CompositeNode(node)
    for i in range(len(node.inputs)):
        comp.AddInputs(node.inputs[i], mat_node.inputs[i])
    for i in range(len(node.outputs)):
        comp.AddOutputs(node.outputs[i], mat_node.outputs[i])
    return comp


def ShaderNodeRGBToBW(extree, mat_node):
    node = extree.AddNode('CompositorNodeRGBToBW')
    comp = node_utils.CompositeNode(node)
    for i in range(len(node.inputs)):
        comp.AddInputs(node.inputs[i], mat_node.inputs[i])
    for i in range(len(node.outputs)):
        comp.AddOutputs(node.outputs[i], mat_node.outputs[i])
    return comp


def ShaderNodeSeparateHSV(extree, mat_node):
    node = extree.AddNode('CompositorNodeSepHSVA')
    comp = node_utils.CompositeNode(node)
    for i in range(len(node.inputs)):
        comp.AddInputs(node.inputs[i], mat_node.inputs[i])
    for i in range(len(mat_node.outputs)):
        comp.AddOutputs(node.outputs[i], mat_node.outputs[i])
    return comp


def ShaderNodeSeparateRGB(extree, mat_node):
    node = extree.AddNode('CompositorNodeSepRGBA')
    comp = node_utils.CompositeNode(node)
    for i in range(len(node.inputs)):
        comp.AddInputs(node.inputs[i], mat_node.inputs[i])
    for i in range(3):
        comp.AddOutputs(node.outputs[i], mat_node.outputs[i])
    return comp
