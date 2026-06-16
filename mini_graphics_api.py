"""
mini_graphics_api.py

A small software graphics API for Python.

Pipeline:
1. Vertex Shader
2. Primitive Assembly
3. Rasterization
4. Fragment Shader
5. Framebuffer
"""

from dataclasses import dataclass
from typing import Callable, List, Tuple, Dict, Any
import math

try:
    from PIL import Image
except ImportError:
    Image = None


Vec4 = Tuple[float, float, float, float]
Color = Tuple[int, int, int, int]


def clamp(value, low, high):
    return max(low, min(high, value))


def mat4_mul_vec4(m: List[List[float]], v: Vec4) -> Vec4:
    x, y, z, w = v
    return (
        m[0][0] * x + m[0][1] * y + m[0][2] * z + m[0][3] * w,
        m[1][0] * x + m[1][1] * y + m[1][2] * z + m[1][3] * w,
        m[2][0] * x + m[2][1] * y + m[2][2] * z + m[2][3] * w,
        m[3][0] * x + m[3][1] * y + m[3][2] * z + m[3][3] * w,
    )


def identity_matrix() -> List[List[float]]:
    return [
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1],
    ]


def rotation_z(angle_radians: float) -> List[List[float]]:
    c = math.cos(angle_radians)
    s = math.sin(angle_radians)
    return [
        [c, -s, 0, 0],
        [s, c, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1],
    ]


@dataclass
class Vertex:
    position: Vec4
    color: Color


@dataclass
class VertexOut:
    clip_position: Vec4
    color: Color


@dataclass
class Fragment:
    x: int
    y: int
    depth: float
    color: Color


@dataclass
class Triangle:
    a: VertexOut
    b: VertexOut
    c: VertexOut


class Framebuffer:
    """Stores final rendered pixels and depth values."""

    def __init__(self, width: int, height: int, clear_color: Color = (10, 10, 20, 255)):
        self.width = width
        self.height = height
        self.clear_color = clear_color
        self.color_buffer: List[List[Color]] = []
        self.depth_buffer: List[List[float]] = []
        self.clear()

    def clear(self):
        self.color_buffer = [[self.clear_color for _ in range(self.width)] for _ in range(self.height)]
        self.depth_buffer = [[float("inf") for _ in range(self.width)] for _ in range(self.height)]

    def write_pixel(self, x: int, y: int, depth: float, color: Color):
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return
        if depth < self.depth_buffer[y][x]:
            self.depth_buffer[y][x] = depth
            self.color_buffer[y][x] = color

    def save_png(self, path: str):
        if Image is None:
            raise RuntimeError("Pillow is required. Install it with: pip install pillow")
        image = Image.new("RGBA", (self.width, self.height))
        for y in range(self.height):
            for x in range(self.width):
                image.putpixel((x, y), self.color_buffer[y][x])
        image.save(path)

    def to_ascii(self) -> str:
        chars = " .:-=+*#%@"
        lines = []
        for y in range(self.height):
            line = ""
            for x in range(self.width):
                r, g, b, _ = self.color_buffer[y][x]
                brightness = (r + g + b) / 3
                idx = int((brightness / 255) * (len(chars) - 1))
                line += chars[idx]
            lines.append(line)
        return "\n".join(lines)


class ShaderProgram:
    """User-definable vertex and fragment shaders."""

    def __init__(self, vertex_shader: Callable[[Vertex, Dict[str, Any]], VertexOut], fragment_shader: Callable[[Fragment, Dict[str, Any]], Color]):
        self.vertex_shader = vertex_shader
        self.fragment_shader = fragment_shader


def default_vertex_shader(vertex: Vertex, uniforms: Dict[str, Any]) -> VertexOut:
    mvp = uniforms.get("mvp", identity_matrix())
    return VertexOut(clip_position=mat4_mul_vec4(mvp, vertex.position), color=vertex.color)


def default_fragment_shader(fragment: Fragment, uniforms: Dict[str, Any]) -> Color:
    return fragment.color


class GraphicsAPI:
    """Software graphics API with a programmable rendering pipeline."""

    def __init__(self, framebuffer: Framebuffer):
        self.framebuffer = framebuffer
        self.shader_program = ShaderProgram(default_vertex_shader, default_fragment_shader)
        self.uniforms: Dict[str, Any] = {}

    def use_shader(self, shader_program: ShaderProgram):
        self.shader_program = shader_program

    def set_uniform(self, name: str, value: Any):
        self.uniforms[name] = value

    def run_vertex_shader(self, vertices: List[Vertex]) -> List[VertexOut]:
        return [self.shader_program.vertex_shader(vertex, self.uniforms) for vertex in vertices]

    def assemble_triangles(self, vertices: List[VertexOut], indices: List[int]) -> List[Triangle]:
        triangles = []
        for i in range(0, len(indices), 3):
            if i + 2 >= len(indices):
                break
            triangles.append(Triangle(vertices[indices[i]], vertices[indices[i + 1]], vertices[indices[i + 2]]))
        return triangles

    def clip_to_screen(self, clip_position: Vec4):
        x, y, z, w = clip_position
        if w == 0:
            w = 0.00001
        ndc_x = x / w
        ndc_y = y / w
        ndc_z = z / w
        screen_x = int((ndc_x * 0.5 + 0.5) * (self.framebuffer.width - 1))
        screen_y = int((1.0 - (ndc_y * 0.5 + 0.5)) * (self.framebuffer.height - 1))
        return screen_x, screen_y, ndc_z

    def rasterize_triangle(self, triangle: Triangle) -> List[Fragment]:
        x0, y0, z0 = self.clip_to_screen(triangle.a.clip_position)
        x1, y1, z1 = self.clip_to_screen(triangle.b.clip_position)
        x2, y2, z2 = self.clip_to_screen(triangle.c.clip_position)

        min_x = int(clamp(min(x0, x1, x2), 0, self.framebuffer.width - 1))
        max_x = int(clamp(max(x0, x1, x2), 0, self.framebuffer.width - 1))
        min_y = int(clamp(min(y0, y1, y2), 0, self.framebuffer.height - 1))
        max_y = int(clamp(max(y0, y1, y2), 0, self.framebuffer.height - 1))

        fragments = []
        area = edge_function(x0, y0, x1, y1, x2, y2)
        if area == 0:
            return fragments

        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                w0 = edge_function(x1, y1, x2, y2, x, y)
                w1 = edge_function(x2, y2, x0, y0, x, y)
                w2 = edge_function(x0, y0, x1, y1, x, y)

                if (w0 >= 0 and w1 >= 0 and w2 >= 0) or (w0 <= 0 and w1 <= 0 and w2 <= 0):
                    alpha = w0 / area
                    beta = w1 / area
                    gamma = w2 / area
                    depth = alpha * z0 + beta * z1 + gamma * z2
                    color = interpolate_color(triangle.a.color, triangle.b.color, triangle.c.color, alpha, beta, gamma)
                    fragments.append(Fragment(x, y, depth, color))
        return fragments

    def shade_fragment(self, fragment: Fragment) -> Color:
        return self.shader_program.fragment_shader(fragment, self.uniforms)

    def draw_indexed(self, vertices: List[Vertex], indices: List[int]):
        transformed_vertices = self.run_vertex_shader(vertices)
        triangles = self.assemble_triangles(transformed_vertices, indices)
        for triangle in triangles:
            for fragment in self.rasterize_triangle(triangle):
                shaded_color = self.shade_fragment(fragment)
                self.framebuffer.write_pixel(fragment.x, fragment.y, fragment.depth, shaded_color)


def edge_function(ax, ay, bx, by, cx, cy):
    return (cx - ax) * (by - ay) - (cy - ay) * (bx - ax)


def interpolate_channel(a, b, c, wa, wb, wc):
    return int(clamp(a * wa + b * wb + c * wc, 0, 255))


def interpolate_color(c0: Color, c1: Color, c2: Color, wa, wb, wc) -> Color:
    return (
        interpolate_channel(c0[0], c1[0], c2[0], wa, wb, wc),
        interpolate_channel(c0[1], c1[1], c2[1], wa, wb, wc),
        interpolate_channel(c0[2], c1[2], c2[2], wa, wb, wc),
        interpolate_channel(c0[3], c1[3], c2[3], wa, wb, wc),
    )


def glow_fragment_shader(fragment: Fragment, uniforms: Dict[str, Any]) -> Color:
    r, g, b, a = fragment.color
    glow = uniforms.get("glow", 1.25)
    return (int(clamp(r * glow, 0, 255)), int(clamp(g * glow, 0, 255)), int(clamp(b * glow, 0, 255)), a)


def main():
    framebuffer = Framebuffer(256, 256, clear_color=(5, 8, 18, 255))
    api = GraphicsAPI(framebuffer)
    api.use_shader(ShaderProgram(default_vertex_shader, glow_fragment_shader))
    api.set_uniform("mvp", rotation_z(math.radians(15)))
    api.set_uniform("glow", 1.35)

    vertices = [
        Vertex(position=(-0.7, -0.6, 0.3, 1.0), color=(255, 60, 60, 255)),
        Vertex(position=(0.7, -0.6, 0.3, 1.0), color=(60, 255, 90, 255)),
        Vertex(position=(0.0, 0.7, 0.3, 1.0), color=(60, 150, 255, 255)),
    ]
    indices = [0, 1, 2]
    api.draw_indexed(vertices, indices)
    framebuffer.save_png("render_output.png")
    print("Saved render_output.png")


if __name__ == "__main__":
    main()
