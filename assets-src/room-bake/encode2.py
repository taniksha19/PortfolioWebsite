# Edge-aware denoise of a baked lightmap, then encode it as an sRGB JPEG storing value / K.
# The baked world-position map is the guide: texels only average with neighbours that sit at
# (almost) the same point in the room, so separate surfaces packed side by side in the atlas never bleed.
# usage: python -I encode2.py lm.npy pos.npy out.jpg K [radius] [sigma_space_px] [sigma_pos_m]
import sys, numpy as np
from PIL import Image

lmf, posf, dst, K = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
R = int(sys.argv[5]) if len(sys.argv) > 5 else 4
SS = float(sys.argv[6]) if len(sys.argv) > 6 else 2.2
SP = float(sys.argv[7]) if len(sys.argv) > 7 else 0.03

a = np.load(lmf).astype(np.float32)
p = np.load(posf).astype(np.float32)
valid = (a.sum(axis=2) > 0).astype(np.float32)
out = np.zeros_like(a); wsum = np.zeros(a.shape[:2], np.float32)
for dy in range(-R, R + 1):
    for dx in range(-R, R + 1):
        ws = np.exp(-(dx * dx + dy * dy) / (2 * SS * SS))
        a2 = np.roll(a, (dy, dx), axis=(0, 1)); p2 = np.roll(p, (dy, dx), axis=(0, 1)); v2 = np.roll(valid, (dy, dx), axis=(0, 1))
        w = ws * np.exp(-((p - p2) ** 2).sum(axis=2) / (2 * SP * SP)) * v2
        out += a2 * w[..., None]; wsum += w
res = np.where(wsum[..., None] > 1e-6, out / np.maximum(wsum, 1e-6)[..., None], a)

v = np.clip(res / K, 0, 1)
srgb = np.where(v <= 0.0031308, v * 12.92, 1.055 * np.power(v, 1 / 2.4) - 0.055)
Image.fromarray((srgb * 255 + .5).astype(np.uint8)).save(dst, quality=92, subsampling=0)
print(dst, "clipped %.3f%%" % (100 * (res / K > 1).mean()), "mean", res[valid > 0].mean(axis=0).round(3))
