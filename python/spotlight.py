from __future__ import annotations

import math
from typing import Any

import graphics_math as gm

from light import Light


class SpotLight(Light):
    """Spot light: position + direction + cone. The cone is given in
    degrees (inner = full intensity, outer = zero intensity, smooth
    falloff between them) but stored as cosines, which is what the
    fragment shader compares against. Position is mapped like a point
    (w=1), direction like a vector (w=0, normalized), so the light works
    in world, camera or local space."""

    def __init__ (self, x: float, y: float, z: float,
                  dx: float, dy: float, dz: float,
                  inner_deg: float = 20.0, outer_deg: float = 30.0,
                  space: str = "world", **values: Any) -> None:
      Light.__init__(self, space, **values)
      self.set_position(x, y, z)
      self.set_direction(dx, dy, dz)
      self.set_cone(inner_deg, outer_deg)

    def set_position (self, x: float, y: float, z: float) -> None:
      self.set("light_position", gm.vec4(x,y,z,1.0))

    def set_direction (self, dx: float, dy: float, dz: float) -> None:
      self.set("light_direction", gm.normalize(gm.vec3(dx,dy,dz)))

    def set_cone (self, inner_deg: float, outer_deg: float) -> None:
      """Inner/outer half-angles, in degrees; inner must be < outer."""
      if not 0.0 < inner_deg < outer_deg < 90.0:
        raise ValueError(f"need 0 < inner < outer < 90, got inner={inner_deg}, outer={outer_deg}")
      self.set("light_cos_inner", math.cos(math.radians(inner_deg)))
      self.set("light_cos_outer", math.cos(math.radians(outer_deg)))

    def map (self, matrix: gm.Mat4) -> dict[str, Any]:
      position = matrix @ self.get("light_position")
      d = self.get("light_direction")
      direction = (matrix @ gm.vec4(d[0], d[1], d[2], 0.0))[:3]
      return {"light_position": position, "light_direction": gm.normalize(direction)}
