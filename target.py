
import bpy


def SetTargets(key):
    global keywords
    global objects
    global meshes
    global armatures

    keywords = key

    scene = bpy.context.scene
    if key['selection_only']:
        objects = bpy.context.selected_objects
    else:
        objects = bpy.context.scene.objects[:]
    objects = tuple(objects)

    armatures = []
    for obj in objects:
        for mod in obj.modifiers:
            if mod.bl_rna.identifier == 'ArmatureModifier':
                armatures.append(mod.object)
    armatures = tuple(set(armatures))