from __future__ import annotations

import os
from typing import Any

import graphics_math as gm
import wgpu
from rendercanvas.glfw import RenderCanvas, loop

from camera3d import *
from spotlight import *
from clipplane import *
from shader import *
from pipeline import *
from phongmaterial import *
from texture import *
from sampler import *
from textureset import *
from transform import *
from node import *
from scene import *
from renderer import *
from cube import *
from sphere import *

HERE = os.path.dirname(os.path.abspath(__file__))
SHADER = os.path.join(HERE, "..", "shaders", "mesa", "scene.wgsl")
IMAGES = os.path.join(HERE, "..", "images")

canvas: RenderCanvas
device: wgpu.GPUDevice
context: Any
renderer: Renderer
camera: Camera3D
scene: Scene
shader: Shader
clip_plane: ClipPlane

CLEAR = (0.05, 0.06, 0.09, 1.0)   # tambem e a cor do fog

# efeitos ligados/desligados por teclado
effects = {"fog": True, "clip": False, "light2": True}

# dimensoes da mesa (o chao esta em y = 0)
LEG_H = 1.5
TOP_THICK = 0.15
TOP_W, TOP_D = 3.0, 2.0
LEG_SIZE = 0.15
TOP_Y = LEG_H + TOP_THICK

def make_trf (translate=(0,0,0), scale=(1,1,1), rotate=None) -> Transform:
  """Transform com ordem T * R * S: a escala vale no espaco local do objeto."""
  trf = Transform()
  trf.translate(*translate)
  if rotate is not None:
    trf.rotate(*rotate)
  trf.scale(*scale)
  return trf

def apply_effects () -> None:
  """Escreve nos campos "global" do shader o estado atual dos efeitos."""
  shader.set_value("fog_enabled", 1.0 if effects["fog"] else 0.0)
  if effects["clip"]:
    clip_plane.set_plane(-1.0, 0.0, 0.0, 0.6)   # mantem x <= 0.6: corta o cubo ao meio
  else:
    clip_plane.set_plane(0.0, 0.0, 0.0, 1.0)    # dot = 1 > 0: nada e cortado
  if effects["light2"]:
    shader.set_value("light2_diffuse", gm.vec3(0.40, 0.30, 0.15))
    shader.set_value("light2_specular", gm.vec3(0.30, 0.25, 0.15))
  else:
    shader.set_value("light2_diffuse", gm.vec3(0.0))
    shader.set_value("light2_specular", gm.vec3(0.0))

def initialize (device: wgpu.GPUDevice, target_format: str) -> None:
  global camera, scene, shader, clip_plane

  # ---- camera com arcball (o centro deve ser definido antes do arcball) ----
  camera = Camera3D(5.0, 4.5, 6.5)
  camera.set_center(0.0, 1.2, 0.0)
  arcball = camera.create_arcball()
  arcball.attach(canvas)

  # ---- luz 1: spot acima da mesa ----
  light = SpotLight(2.0, 5.0, 2.0,
                    -2.0, -(5.0 - TOP_Y), -2.0,
                    inner_deg=22.0, outer_deg=32.0, space="world")
  light.set_ambient(0.25, 0.25, 0.28)

  # ---- shader/pipeline ----
  shader = Shader(device, SHADER, light=light, space="world")
  shader.set_vertex_buffers([
    {"array_stride": 3 * 4, "step_mode": "vertex",
     "attributes": [{"format": "float32x3", "offset": 0, "var_name": "coord"}]},
    {"array_stride": 3 * 4, "step_mode": "vertex",
     "attributes": [{"format": "float32x3", "offset": 0, "var_name": "normal"}]},
    {"array_stride": 3 * 4, "step_mode": "vertex",
     "attributes": [{"format": "float32x3", "offset": 0, "var_name": "tangent"}]},
    {"array_stride": 2 * 4, "step_mode": "vertex",
     "attributes": [{"format": "float32x2", "offset": 0, "var_name": "texcoord"}]},
  ])
  # cull "none": as faces de tras precisam ser desenhadas para formar a tampa do corte
  pipeline = Pipeline(shader, target_format, primitive={"cull_mode": "none"})

  # ---- valores globais fixos ----
  light2 = gm.vec4(-2.5, 3.0, -1.5, 1.0)
  shader.set_value("light2_position", light2)
  shader.set_value("fog_color", gm.vec3(CLEAR[0], CLEAR[1], CLEAR[2]))
  shader.set_value("fog_near", 6.0)
  shader.set_value("fog_far", 22.0)
  clip_plane = ClipPlane(shader, 0.0, 0.0, 0.0, 1.0)
  clip_plane.set_color(0.9, 0.8, 0.2)
  apply_effects()

  # ---- texturas: decal so no chao e na mesa; esfera e cubo usam texel branco 1x1 ----
  sampler = Sampler(device, "decal_sampler")
  white = Texture(device, "decal_texture", None, texel=gm.vec3(1.0, 1.0, 1.0))

  def texset (decal_tex: Texture) -> TextureSet:
    return TextureSet([decal_tex, sampler])

  floor_tex = texset(Texture(device, "decal_texture", os.path.join(IMAGES, "checker.png")))
  wood_tex = texset(Texture(device, "decal_texture", os.path.join(IMAGES, "wood.png")))
  plain_tex = texset(white)
  sphere_tex = plain_tex
  cube_tex = plain_tex

  floor_mat = PhongMaterial(0.9, 0.9, 0.9)
  floor_mat.set_specular(0.2, 0.2, 0.2)
  wood_mat = PhongMaterial(1.0, 1.0, 1.0)
  wood_mat.set_specular(0.3, 0.3, 0.3)
  sphere_mat = PhongMaterial(0.85, 0.15, 0.15)
  sphere_mat.set_shininess(64.0)
  cube_mat = PhongMaterial(0.2, 0.4, 0.9)
  cube_mat.set_specular(0.4, 0.4, 0.4)
  for mat in (floor_mat, wood_mat, sphere_mat, cube_mat):
    shader.add_material(mat)
  for ts in (floor_tex, wood_tex, plain_tex):
    shader.add_texture_set(ts)

  # ---- geometrias ----
  cube = Cube(device)
  sphere = Sphere(device)

  # ---- grafo de cena ----
  floor = Node(None, make_trf((0,-0.1,0), (10,0.1,10)), [floor_mat, floor_tex], [cube])

  table_top = Node(None, make_trf((0,LEG_H,0), (TOP_W,TOP_THICK,TOP_D)), shps=[cube])
  legs = []
  for sx in (-1, 1):
    for sz in (-1, 1):
      x = sx * (TOP_W/2 - LEG_SIZE)
      z = sz * (TOP_D/2 - LEG_SIZE)
      legs.append(Node(None, make_trf((x,0,z), (LEG_SIZE,LEG_H,LEG_SIZE)), shps=[cube]))
  table = Node(None, None, [wood_mat, wood_tex], nodes=[table_top] + legs)

  r = 0.35
  ball = Node(None, make_trf((-0.7, TOP_Y + r, 0.0), (r,r,r)), [sphere_mat, sphere_tex], [sphere])
  box = Node(None, make_trf((0.7, TOP_Y, 0.1), (0.6,0.6,0.6), rotate=(25.0, 0.0, 1.0, 0.0)),
             [cube_mat, cube_tex], [cube])

  root = Node(pipeline, nodes=[floor, table, ball, box])
  scene = Scene(root)

def draw () -> None:
  target_texture = context.get_current_texture()
  renderer.render(target_texture, scene, camera)

KEYS = {"f": "fog", "c": "clip", "l": "light2"}

def on_key (event: Any) -> None:
  key = str(event["key"]).lower()
  if key == "q":
    canvas.close()
  elif key in KEYS:
    name = KEYS[key]
    effects[name] = not effects[name]
    apply_effects()
    print(f"{name}: {'ligado' if effects[name] else 'desligado'}")

def main () -> None:
  global canvas, device, context, renderer

  canvas = RenderCanvas(size=(800, 600), title="Projeto 2 - mesa e objetos", update_mode="continuous", max_fps=60)
  adapter = wgpu.gpu.request_adapter_sync()
  device = adapter.request_device_sync()
  context = canvas.get_context("wgpu")
  target_format = context.get_preferred_format(device.adapter)
  context.configure(device=device, format=target_format)

  renderer = Renderer(device, depth_test=True, clear_value=CLEAR)

  initialize(device, target_format)

  canvas.add_event_handler(on_key, "key_down")
  print("Teclas: f=fog  c=plano de corte  l=segunda luz  q=sair")
  canvas.request_draw(draw)
  loop.run()

if __name__ == "__main__":
  main()
