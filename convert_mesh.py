import bpy
import bmesh
import numpy as np
import math
import os
import shutil

from . import target


# Triangulate（Required for iOS13.）
def MeshTriangulate(me):
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()



def Rename(name):
    usd_name = name.replace(",", "_").replace(".", "_").replace("-", "_").replace(" ", "")
    if len(name) > 0 and name[0].isdecimal():
        usd_name = "_"+usd_name
    return usd_name



def ConvertUsdaMeshes():
    pass



def GetMeshData(obj, name):
    mesh = obj.data
    # get vertex
    faceVertexCounts = [None]*len(mesh.polygons)
    mesh.polygons.foreach_get("loop_total", faceVertexCounts)
    
    faceVertexIndices = [None]*len(mesh.loops)
    mesh.polygons.foreach_get("vertices", faceVertexIndices)
    
    # points
    points = [None]*len(mesh.vertices)*3
    mesh.vertices.foreach_get("co", points)
    # round units
    points = [round(n*100,5) for n in points]
    # [1,2,3,4,5,6,...] -> [(1,2,3),(4,5,6),...]
    points = list(zip(*[iter(points)]*3))

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

    # uv
    uv_layer = mesh.uv_layers.active
    if uv_layer and target.keywords["include_uvs"]:
        uv_all = [None]*len(mesh.loops)*2
        uv_layer.data.foreach_get("uv", uv_all)
        uv_all = [float('{:.5f}'.format(n)) for n in uv_all]
        # [1,2,3,4,5,6,...] -> [(1,2),(3,4),(5,6),...]
        uv_all = zip(*[iter(uv_all)]*2)
        uv_all = np.array(list(uv_all))
        uv, uv_indices = np.unique(uv_all, axis=0, return_inverse=True)
        uv = [tuple([float('{:.5f}'.format(nn)) for nn in n]) for n in uv]
        uv_indices = list(uv_indices)

    # material indices
    mat_ids = [ [] for i in range(len(obj.material_slots)) ]
    if obj.material_slots:
        for i, poly in enumerate( mesh.polygons ):
            mat_ids[ poly.material_index ].append( i )


    extent = [tuple(obj.bound_box[0]), tuple(obj.bound_box[6])]

    usda = """

    def """+'"'+Rename(name)+'"'+"""
    {
        float3[] extent = """+str(extent)+"""
        int[] faceVertexCounts = """+str(faceVertexCounts)+"""
        int[] faceVertexIndices = """+str(faceVertexIndices)+"""
        point3f[] points = """+str(points)+"""
        normal3f[] primvars:normals = """+str(normals)+""" (
            interpolation = "faceVarying"
        )
        int[] primvars:normals:indices = """+str(normals_indices)
        
    if uv:
        usda += """
        texCoord2f[] primvars:uv = """+str(uv)+""" (
            interpolation = "faceVarying"
        )
        int[] primvars:uv:indices = """+str(uv_indices)

    for i, mat_ids in enumerate(mat_ids):
        usda += """
        def """+'"'+"mat_"+str(i).zfill(4)+'"'+"""
        {
            uniform token elementType = "face"
            uniform token familyName = "materialBind"
            int[] indices = """+str(mat_ids)+"""
        }"""

    usda += """
    }"""

    return usda




def GetMeshDataAll():
    usda = """

def Scope "Meshes"
{"""

    # get meshes
    meshes = []
    for obj in target.objects:
        bm = bmesh.new()
        name = obj.data.name
        sub_obj = None
        
        if target.keywords["apply_modifiers"]:
            name = obj.name
            # get preview mesh
            depsgraph = bpy.context.evaluated_depsgraph_get()
            sub_obj = obj.evaluated_get(depsgraph)
            bm.from_mesh(sub_obj.data)

            # invert transform
            sub_obj.data.transform(np.linalg.inv(obj.matrix_world))
        else:
            if obj.data not in meshes:
                sub_obj = obj
                bm.from_mesh(obj.data)
                meshes.append(obj.data)

        if sub_obj:
            # triangulate（fixed for iOS13.）
            bmesh.ops.triangulate(bm, faces=bm.faces)

            # get mesh data
            bm.to_mesh(sub_obj.data)
            usda += GetMeshData(sub_obj, name)

        bm.free()
    
    usda += """
}"""

    return usda

