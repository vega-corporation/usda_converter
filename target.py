
import bpy


def SetTargets(key):
    global keywords
    global objects
    global meshes
    global armatures

    keywords = key

    objects = [obj for obj in bpy.data.objects if obj.type == 'MESH' and obj.data.polygons]
    if key['selection_only']:
        objects = [obj for obj in objects if obj.select_get()]
    objects = tuple(objects)
    
    meshes = [obj.to_mesh() for obj in objects]
    meshes = tuple(set(meshes))

    armatures = []
    for obj in objects:
        for mod in obj.modifiers:
            if mod.bl_rna.identifier == 'ArmatureModifier':
                armatures.append(mod.object)
    armatures = tuple(set(armatures))