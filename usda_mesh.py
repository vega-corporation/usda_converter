

class UsdaMesh():
    def __init__(self):
        self.faceVertexCounts = None
        self.faceVertexIndices = None
        self.points = None
        self.normal = None
        self.normal_indices = None
        self.uv = None
        self.uv_indices = None
        self.mat_indices = None


class Animation():
    def __init__(self):
        self.end = 0
        self.start = 0
        self.fps = 24