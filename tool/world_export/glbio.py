"""Minimal GLB reader/writer (core glTF 2.0 only)."""
import json, struct
import numpy as np

CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}

def read_glb(path):
    b = open(path, 'rb').read()
    magic, ver, length = struct.unpack_from('<III', b, 0)
    assert magic == 0x46546C67
    off = 12; js = None; binc = None
    while off < length:
        clen, ctype = struct.unpack_from('<II', b, off); off += 8
        chunk = b[off:off + clen]; off += clen
        if ctype == 0x4E4F534A: js = json.loads(chunk)
        elif ctype == 0x004E4942: binc = chunk
    return js, binc

def accessor(js, binc, i):
    a = js['accessors'][i]; bv = js['bufferViews'][a['bufferView']]
    dt = CT[a['componentType']]; n = NC[a['type']]
    start = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    stride = bv.get('byteStride', 0)
    if stride and stride != n * np.dtype(dt).itemsize:
        raw = np.frombuffer(binc, dtype=np.uint8, count=stride * a['count'], offset=start).reshape(a['count'], stride)
        return raw[:, :n * np.dtype(dt).itemsize].copy().view(dt).reshape(a['count'], n)
    arr = np.frombuffer(binc, dtype=dt, count=a['count'] * n, offset=start)
    return arr.reshape(a['count'], n) if n > 1 else arr

class GLBWriter:
    def __init__(self):
        self.js = {'asset': {'version': '2.0', 'generator': 'yard_export (WEDG)'}, 'scene': 0, 'scenes': [{'nodes': []}],
                   'nodes': [], 'meshes': [], 'materials': [], 'accessors': [], 'bufferViews': [], 'buffers': []}
        self.bin = bytearray()

    def _view(self, data, target=None):
        while len(self.bin) % 4: self.bin.append(0)
        bv = {'buffer': 0, 'byteOffset': len(self.bin), 'byteLength': len(data)}
        if target: bv['target'] = target
        self.bin += data
        self.js['bufferViews'].append(bv)
        return len(self.js['bufferViews']) - 1

    def add_accessor(self, arr, target=None, minmax=False):
        arr = np.ascontiguousarray(arr)
        ct = {np.dtype(np.float32): 5126, np.dtype(np.uint16): 5123, np.dtype(np.uint32): 5125, np.dtype(np.uint8): 5121}[arr.dtype]
        n = 1 if arr.ndim == 1 else arr.shape[1]
        t = {1: 'SCALAR', 2: 'VEC2', 3: 'VEC3', 4: 'VEC4'}[n]
        acc = {'bufferView': self._view(arr.tobytes(), target), 'componentType': ct, 'count': int(arr.shape[0]), 'type': t}
        if minmax:
            acc['min'] = [float(v) for v in np.atleast_1d(arr.min(axis=0))]
            acc['max'] = [float(v) for v in np.atleast_1d(arr.max(axis=0))]
        self.js['accessors'].append(acc)
        return len(self.js['accessors']) - 1

    def add_image(self, data, mime):
        self.js.setdefault('images', []).append({'bufferView': self._view(data), 'mimeType': mime})
        return len(self.js['images']) - 1

    def add_texture(self, image, sampler):
        samplers = self.js.setdefault('samplers', [])
        if sampler not in samplers: samplers.append(sampler)
        self.js.setdefault('textures', []).append({'sampler': samplers.index(sampler), 'source': image})
        return len(self.js['textures']) - 1

    def add_material(self, m):
        self.js['materials'].append(m); return len(self.js['materials']) - 1

    def add_mesh(self, name, prims):
        """prims: list of dict(position, normal, uv(optional), index, material)."""
        out = []
        for p in prims:
            attrs = {'POSITION': self.add_accessor(p['position'].astype(np.float32), 34962, minmax=True),
                     'NORMAL': self.add_accessor(p['normal'].astype(np.float32), 34962)}
            if p.get('uv') is not None: attrs['TEXCOORD_0'] = self.add_accessor(p['uv'].astype(np.float32), 34962)
            idx = p['index']
            idx = idx.astype(np.uint16 if p['position'].shape[0] < 65536 else np.uint32)
            out.append({'attributes': attrs, 'indices': self.add_accessor(idx, 34963), 'material': p['material'], 'mode': 4})
        self.js['meshes'].append({'name': name, 'primitives': out})
        return len(self.js['meshes']) - 1

    def add_node(self, node, root=True):
        self.js['nodes'].append(node); i = len(self.js['nodes']) - 1
        if root: self.js['scenes'][0]['nodes'].append(i)
        return i

    def write(self, path):
        while len(self.bin) % 4: self.bin.append(0)
        self.js['buffers'] = [{'byteLength': len(self.bin)}]
        for k in [k for k, v in self.js.items() if v == []]: del self.js[k]
        j = json.dumps(self.js, separators=(',', ':')).encode()
        while len(j) % 4: j += b' '
        total = 12 + 8 + len(j) + 8 + len(self.bin)
        with open(path, 'wb') as f:
            f.write(struct.pack('<III', 0x46546C67, 2, total))
            f.write(struct.pack('<II', len(j), 0x4E4F534A)); f.write(j)
            f.write(struct.pack('<II', len(self.bin), 0x004E4942)); f.write(bytes(self.bin))
        return total
