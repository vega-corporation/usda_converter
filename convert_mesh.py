import bpy
import numpy as np
import bmesh

from . import utils
from .utils import Rename




def MeshTriangulate(me):
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()



def ConvertMeshData(usda, mesh, obj):
    # get vertex
    faceVertexCounts = [None]*len(mesh.polygons)
    mesh.polygons.foreach_get("loop_total", faceVertexCounts)
    
    faceVertexIndices = [None]*len(mesh.loops)
    mesh.polygons.foreach_get("vertices", faceVertexIndices)
    
    # points
    points = [None]*len(mesh.vertices)*3
    mesh.vertices.foreach_get("co", points)
    # round units
    points = [round(n,5) for n in points]
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
    uv = None
    uv_layer = mesh.uv_layers.active
    if uv_layer and utils.keywords["include_uvs"]:
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
    mat_ids_all = [None]*len(mesh.polygons)
    mesh.polygons.foreach_get("material_index", mat_ids_all)
    mat_ids_all = np.array(mat_ids_all)
    mat_ids = [ [] for i in range(max(mat_ids_all)+1) ]
    for i, ids in enumerate(mat_ids):
        mat_ids[i] = np.where(mat_ids_all == i)[0]

    # bounding box
    extent = np.array(points)
    extent = [tuple(np.min(extent, axis=0)), tuple(np.max(extent, axis=0))]

    usda.append(f"""
        float3[] extent = {extent}
        int[] faceVertexCounts = {faceVertexCounts}
        int[] faceVertexIndices = {faceVertexIndices}
        point3f[] points = {points}
        normal3f[] primvars:normals = {normals} (
            interpolation = "faceVarying"
        )
        int[] primvars:normals:indices = {normals_indices}"""
    )
    if uv:
        usda.append(f"""
        texCoord2f[] primvars:uv = {uv} (
            interpolation = "faceVarying"
        )
        int[] primvars:uv:indices = {uv_indices}"""
        )

    if utils.keywords["include_armatures"]:
        elementsize = 0
        for i, v in enumerate(mesh.vertices):
            if elementsize < len(v.groups):
                elementsize = len(v.groups)

        joint_indices = [0]*len(mesh.vertices)*elementsize
        joint_weights = [0]*len(mesh.vertices)*elementsize
        for i, v in enumerate(mesh.vertices):
            for j, g in enumerate(v.groups):
                joint_indices[i*elementsize+j] = g.group
                joint_weights[i*elementsize+j] = g.weight
                
        if utils.armature_obj[obj.name]:
            bones = utils.armature_obj[obj.name].data.bones
            g_names = {g.name: i for i, g in enumerate(obj.vertex_groups)}
            ids_convert = {g_names[bone.name]: i for i, bone in enumerate(bones) if bone.name in g_names}
            joint_indices = [ids_convert[j_id] if j_id in ids_convert else 0 for j_id in joint_indices]
            
            usda.append(f"""
        int[] primvars:skel:jointIndices = {joint_indices} (
            elementSize = {elementsize}
            interpolation = "vertex"
        )
        float[] primvars:skel:jointWeights = {joint_weights} (
            elementSize = {elementsize}
            interpolation = "vertex"
        )"""
            )

    # Properties that are valid for usda but not supported by usdz
    usda.append("""
        uniform bool doubleSided = 1
        uniform token subdivisionScheme = "none\""""
    )

    for i, ids in enumerate(mat_ids):
        usda.append(f"""
        def "mat_{str(i).zfill(4)}"
        {{
            uniform token elementType = "face"
            uniform token familyName = "materialBind"
            int[] indices = {list(ids)}
        }}"""
        )




def ConvertMeshes(usda):
    usda.append("""

def Scope "Meshes"
{""")
    # get depsgraph once
    if utils.keywords["apply_modifiers"]:
        scn = bpy.context.scene
        orig_frame = scn.frame_current
        scn.frame_set(scn.frame_start)
        for armature in utils.armatures:
            armature.data.pose_position = 'REST'

        depsgraph = bpy.context.evaluated_depsgraph_get()

        scn.frame_set(orig_frame)
        for armature in utils.armatures:
            armature.data.pose_position = 'POSE'

    # get meshes
    meshes = []

    for obj in utils.objects:

        # include all meshes if apply modifier
        if utils.keywords["apply_modifiers"]:
            ob_for_convert = obj.evaluated_get(depsgraph)
            name = obj.name
        else:
            if obj.data in meshes:
                continue

            ob_for_convert = obj.original
            meshes.append(obj.data)
            name = obj.data.name

        try:
            me = ob_for_convert.to_mesh()
        except RuntimeError:
            me = None

        if me is None:
            continue

        # triangulate（fixed for iOS13.）
        if utils.keywords["mesh_triangulate"]:
            MeshTriangulate(me)

        # get mesh data
        usda.append(f"""
    def "{Rename(name)}"
    {{""")

        ConvertMeshData(usda, me, obj)

        usda.append("""
    }""")
        # clear
        ob_for_convert.to_mesh_clear()
    
    usda.append("""
}""")
