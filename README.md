# CyGlobsGL

CyGlobsGL is a small pure-Python software graphics API that demonstrates the classic rendering pipeline from vertex data to a final framebuffer image.

The project is designed as a readable foundation for learning how a graphics pipeline works before moving into GPU APIs such as OpenGL, Vulkan, DirectX, WebGPU, or Metal.

## Render Pipeline

CyGlobsGL follows five main steps:

```text
Vertex Data
   ↓
Vertex Shader
   ↓
Clip-Space Coordinates
   ↓
Primitive Assembly
   ↓
Triangles
   ↓
Rasterization
   ↓
Fragments
   ↓
Fragment Shader
   ↓
Framebuffer
   ↓
PNG Output
```

## Features

- Pure Python software renderer
- Programmable vertex shader hook
- Programmable fragment shader hook
- Clip-space to screen-space conversion
- Triangle primitive assembly
- Barycentric triangle rasterization
- Interpolated vertex colors
- Depth buffer testing
- RGBA framebuffer
- PNG image export through Pillow
- Example glowing triangle render

## Files

```text
mini_graphics_api.py   Core graphics API and demo renderer
README.md              Project documentation
```

## Requirements

Python 3.9 or newer is recommended.

Install Pillow for PNG output:

```bash
pip install pillow
```

## Run the Demo

Clone the repo:

```bash
git clone https://github.com/somsung46810-collab/CyGlobsGL.git
cd CyGlobsGL
```

Run the renderer:

```bash
python mini_graphics_api.py
```

The demo writes:

```text
render_output.png
```

## API Overview

### Vertex Shader

Transforms each vertex into clip-space coordinates.

```python
def default_vertex_shader(vertex, uniforms):
    mvp = uniforms.get("mvp", identity_matrix())
    return VertexOut(
        clip_position=mat4_mul_vec4(mvp, vertex.position),
        color=vertex.color,
    )
```

### Primitive Assembly

Connects vertices by index into triangle primitives.

```python
indices = [0, 1, 2]
```

### Rasterization

Converts triangles into fragments using barycentric coordinates.

### Fragment Shader

Calculates the final color of each fragment.

```python
def glow_fragment_shader(fragment, uniforms):
    r, g, b, a = fragment.color
    glow = uniforms.get("glow", 1.25)
    return (
        int(clamp(r * glow, 0, 255)),
        int(clamp(g * glow, 0, 255)),
        int(clamp(b * glow, 0, 255)),
        a,
    )
```

### Framebuffer

Stores the final rendered image and writes it to a PNG file.

```python
framebuffer.save_png("render_output.png")
```

## Example Usage

```python
from mini_graphics_api import (
    Framebuffer,
    GraphicsAPI,
    ShaderProgram,
    Vertex,
    default_vertex_shader,
    glow_fragment_shader,
    rotation_z,
)

import math

framebuffer = Framebuffer(256, 256)
api = GraphicsAPI(framebuffer)

api.use_shader(ShaderProgram(default_vertex_shader, glow_fragment_shader))
api.set_uniform("mvp", rotation_z(math.radians(15)))
api.set_uniform("glow", 1.35)

vertices = [
    Vertex(position=(-0.7, -0.6, 0.3, 1.0), color=(255, 60, 60, 255)),
    Vertex(position=(0.7, -0.6, 0.3, 1.0), color=(60, 255, 90, 255)),
    Vertex(position=(0.0, 0.7, 0.3, 1.0), color=(60, 150, 255, 255)),
]

api.draw_indexed(vertices, [0, 1, 2])
framebuffer.save_png("render_output.png")
```

## Next Improvements

Possible next steps:

- Perspective projection matrix
- Camera/view matrix
- Texture sampling
- Wireframe mode
- Backface culling
- OBJ mesh loading
- Multiple draw calls
- Scene graph
- Animation loop
- GIF or MP4 export

## License

No license has been added yet. Add a license file before distributing or reusing this project publicly.
