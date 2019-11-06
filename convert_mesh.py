import bpy
import numpy as np
import math
import os
import shutil

from . import keywords
from . import usda_mesh


# Triangulate（Required for iOS13.）
def MeshTriangulate():
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.mesh.reveal()
    bpy.ops.mesh.select_all(action = 'SELECT')
    bpy.ops.mesh.quads_convert_to_tris()
    bpy.ops.object.mode_set(mode = 'OBJECT')




def GetMeshData(obj):
    usda = usda_mesh.UsdaMesh()

    mesh = obj.data

    # get vertex
    faceVertexCounts = [None]*len(mesh.polygons)
    mesh.polygons.foreach_get("loop_total", faceVertexCounts)
    usda.faceVertexCounts = faceVertexCounts
    faceVertexIndices = [None]*len(mesh.loops)
    mesh.polygons.foreach_get("vertices", faceVertexIndices)
    usda.faceVertexIndices = faceVertexIndices
    
    # points
    points = [None]*len(mesh.vertices)*3
    mesh.vertices.foreach_get("co", points)
    # round units
    points = [round(n*100,5) for n in points]
    # [1,2,3,4,5,6,...] -> [(1,2,3),(4,5,6),...]
    points = list(zip(*[iter(points)]*3))
    usda.points = str(points)

    # normals
    normals_all = [None]*len(mesh.loops)*3
    mesh.calc_normals_split()
    mesh.loops.foreach_get("normal", normals_all)
    normals_all = [float('{:.5f}'.format(n)) for n in normals_all]
    # [1,2,3,4,5,6,...] -> [(1,2,3),(4,5,6),...]
    normals_all = zip(*[iter(normals_all)]*3)
    normals_all = np.array(list(normals_all))
    normals, normals_indices = np.unique(normals_all, axis=0, return_inverse=True)
    normals = [tuple([float('{:.5f}'.format(nn)) for nn in n]) for n in normals]
    normals_indices = list(normals_indices)
    usda.normal = str(normals)
    usda.normal_indices = str(normals_indices)

    # uv
    uv_layer = mesh.uv_layers.active
    if uv_layer and keywords.key["use_uvs"]:
        uv_all = [None]*len(mesh.loops)*2
        uv_layer.data.foreach_get("uv", uv_all)
        uv_all = [float('{:.5f}'.format(n)) for n in uv_all]
        # [1,2,3,4,5,6,...] -> [(1,2),(3,4),(5,6),...]
        uv_all = zip(*[iter(uv_all)]*2)
        uv_all = np.array(list(uv_all))
        uv, uv_indices = np.unique(uv_all, axis=0, return_inverse=True)
        uv = [tuple([float('{:.5f}'.format(nn)) for nn in n]) for n in uv]
        uv_indices = list(uv_indices)
        usda.uv = str(uv)
        usda.uv_indices = str(uv_indices)

    # material indices
    usda.mat_indices = { ms.material.name : [] for ms in obj.material_slots }
    for i, poly in enumerate( obj.data.polygons ):
        usda.mat_indices[ obj.material_slots[ poly.material_index ].name ].append( i )

    return usda




def GetMeshDataAll(objects):
    usda_meshes = {}
    # get active
    actived = bpy.context.view_layer.objects.active
    selected = [obj for obj in bpy.data.objects if obj.select_get()]

    # get original objects mesh
    for obj in objects:
        # make sub object
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.duplicate()
        sub_obj = bpy.context.view_layer.objects.active

        # apply modifiers
        if keywords.key["use_mesh_modifiers"]:
            for modifier in sub_obj.modifiers:
                bpy.ops.object.modifier_apply(modifier=modifier.name)

        # triangulate
        MeshTriangulate()

        # get mesh data
        usda_meshes[obj.data.name] = GetMeshData(sub_obj)
        
        # remove sub object
        bpy.data.meshes.remove(sub_obj.data)
    
    # set active
    bpy.context.view_layer.objects.active = actived
    bpy.ops.object.select_all(action='DESELECT')
    for obj in selected:
        obj.select_set(True)

    return usda_meshes

