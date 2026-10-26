"""Gera as texturas de padronagem (decal) usadas pela cena da mesa.
Salva PNGs 256x256 em ../images. Pode ser substituido por qualquer imagem
sua com o mesmo nome."""
from __future__ import annotations

import os

import numpy as np
from PIL import Image

N = 256
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "images")

def save (name: str, rgb: np.ndarray) -> None:
  os.makedirs(OUT, exist_ok=True)
  Image.fromarray(np.clip(rgb, 0, 255).astype("uint8"), "RGB").save(os.path.join(OUT, name))

def wood () -> np.ndarray:
  y, x = np.mgrid[0:N, 0:N].astype("float32")
  rings = np.sin((x * 0.06 + 6.0 * np.sin(y * 0.02) + 2.0 * np.sin(x * 0.015)) * 2.0)
  fine = np.sin(x * 0.9 + 3.0 * np.sin(y * 0.05))
  t = 0.5 + 0.35 * rings + 0.15 * fine
  dark = np.array([110, 65, 30], dtype="float32")
  light = np.array([190, 130, 70], dtype="float32")
  return dark + (light - dark) * t[..., None]

def checker () -> np.ndarray:
  y, x = np.mgrid[0:N, 0:N]
  c = ((x // 32 + y // 32) % 2).astype("float32")
  return (60 + 170 * c)[..., None] * np.ones(3, dtype="float32")

if __name__ == "__main__":
  save("wood.png", wood())
  save("checker.png", checker())
  print("texturas geradas em", os.path.normpath(OUT))
