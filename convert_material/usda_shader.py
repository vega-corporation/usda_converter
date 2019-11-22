

class UsdaTexture():
    def __init__(self):
        self.file = ""
        # self.st = ""
        self.wrapS = "repeat"
        self.wrapT = "repeat"
        self.fallback = [0.0, 0.0, 0.0, 1.0]
        # self.scale = [1.0, 1.0, 1.0, 1.0]
        # self.bias = [0.0, 0.0, 0.0, 0.0]



class UsdaShader():
    def __init__(self):
        self.diffuseColor = [0.18, 0.18, 0.18]
        self.emissiveColor = [0.0, 0.0, 0.0]
        # self.useSpecularWorkflow = 0
        # self.specularColor = [0.0, 0.0, 0.0]   # useSpecularWorkflow = 1
        self.metallic = [0.0]
        self.roughness = [0.5]
        self.clearcoat = [0.0]
        self.clearcoatRoughness = [0.01]
        self.opacity = [1.0]
        # self.opacityThreshold = [0.0]
        self.ior = [1.5]
        self.normal = [0.0, 0.0, 1.0]
        self.displacement = [0.0]
        # self.occlusion = [1.0]

