# CyGlobsGL

CyGlobsGL is an open, pure-Python graphics library inspired by the programmable structure of OpenGL. It exposes a readable software-rendering pipeline for vertices, indexed primitives, shaders, rasterization, depth testing, wireframes, and framebuffer output.

The project treats graphics commands as compact, inspectable data. Directives can be encoded with bit-field packing, viewed or modified as hexadecimal bytes, decoded into transforms, and executed through a Model–View–Projection pipeline.

## Directive Contract

```c
#ifndef CYGLOBSGL_SORT_IO
#define CYGLOBSGL_SORT_IO

Sort(io)      -> Jecht;
Translate(io) -> Daq;
Rotate(io)    -> MVP;
Scale(io)     -> Cap;

#endif
```

The names are domain labels with precise runtime meanings:

| Directive | Domain | Runtime meaning |
|---|---|---|
| `Sort` | `Jecht` | Deterministically order vertices, indices, commands, or contingencies. |
| `Translate` | `Daq` | Apply positional displacement to model data. |
| `Rotate` | `MVP` | Apply rotation inside the Model–View–Projection transform chain. |
| `Scale` | `Cap` | Apply bounded scale, including the default radius constraint. |

## Domain Rule

> Draw in a vector to Directives, or at a radius of `0.62`, into the clip space of a Model–View–Projection matrix, injecting inanimate objects as contingencies to wireframes.

In concrete API terms:

1. An inanimate object is represented by vertices and indices.
2. A `Contingency` supplies a fallback wireframe representation.
3. A `DirectivePacket` packs operation, flags, and parameters into bytes.
4. The packet is inspectable as hexadecimal and decoded without `eval` or executable payloads.
5. Model, view, and projection matrices transform vertices into clip space.
6. Clipping, perspective division, viewport conversion, and rasterization produce framebuffer pixels.

## Pipeline

```text
Object / Contingency
        |
        v
Directive packets: Sort -> Translate -> Rotate -> Scale
        |
        v
Vertex processing -> Model -> View -> Projection
        |
        v
Clip space -> clipping -> NDC -> viewport
        |
        v
Primitive assembly -> wireframe or triangles
        |
        v
Rasterization -> fragment shader -> depth test -> framebuffer
```

## Bit-Field Packet

CyGlobsGL uses an eight-byte directive packet:

```text
byte 0: [ opcode:4 | flags:4 ]
byte 1: object identifier
byte 2-3: signed X parameter, Q8.8 fixed point
byte 4-5: signed Y parameter, Q8.8 fixed point
byte 6-7: signed Z parameter, Q8.8 fixed point
```

Opcodes:

```text
0x1 Sort      / Jecht
0x2 Translate / Daq
0x3 Rotate    / MVP
0x4 Scale     / Cap
```

Example:

```python
from cyglobsgl.directives import Directive, DirectivePacket, Opcode

packet = DirectivePacket(
    directive=Directive(Opcode.SCALE, object_id=7, x=0.62, y=0.62, z=0.62)
)

raw = packet.pack()
print(raw.hex())
restored = DirectivePacket.unpack(raw)
```

## Quick Start

```bash
git clone https://github.com/somsung46810-collab/CyGlobsGL.git
cd CyGlobsGL
python -m pip install -e .
python mini_graphics_api.py
```

The demo writes `render_output.png`.

## Existing Renderer

`mini_graphics_api.py` remains the reference software rasterizer and includes:

- programmable vertex and fragment shader hooks
- indexed triangle assembly
- clip-space to screen-space conversion
- barycentric rasterization
- interpolated RGBA colors
- depth buffering
- PNG export through Pillow

## Project Layout

```text
cyglobsgl/
  __init__.py       Public package exports
  directives.py     Directive domains and packed hexadecimal command format
mini_graphics_api.py
pyproject.toml
LICENSE
README.md
```

## Design Boundaries

CyGlobsGL is an educational software renderer, not a drop-in implementation of the OpenGL specification. It does not claim OpenGL conformance, GPU acceleration, driver compatibility, or binary compatibility. Its API is intentionally open and extensible so additional backends can be implemented later for Vulkan, WebGPU, Metal, Direct3D, or native OpenGL.

Hex editing is limited to validated data packets. Packet decoding checks length, opcode, numeric representation, and finite values before a directive reaches the rendering pipeline.

## License

CyGlobsGL is released under the GNU General Public License version 3 only (`GPL-3.0-only`). See `LICENSE`.