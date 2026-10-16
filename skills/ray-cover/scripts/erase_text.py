"""Erase one line of text from a finished cover, keeping everything else pixel for pixel.

usage: uv run --no-project --with opencv-python-headless --with numpy python erase_text.py \
           <in.png> <out.png> <x0> <y0> <x1> <y1> [--dark] [--thresh 95]

When Ray likes a cover but wants a line removed ("小标题可以不用加"), regenerating gives a different
composition and a different face. Instead: mask the text pixels inside the box (light text by default,
--dark for dark text on a light ground), grow the mask a little, and inpaint (OpenCV Telea). Works well on
smooth or softly lit grounds (the S3 spotlight beam came out clean); on busy texture or over the face,
regenerate instead. Find the box by Read-ing the cover and keep it tight around the line. Always look at
the result next to the original before handing it over.
"""
import sys, cv2, numpy as np

argv = sys.argv[1:]
th = 95
if "--thresh" in argv:
    i = argv.index("--thresh"); th = int(argv[i + 1]); del argv[i:i + 2]
dark = "--dark" in argv
args = [a for a in argv if a != "--dark"]
src, dst, x0, y0, x1, y1 = args[0], args[1], *map(int, args[2:6])
im = cv2.imread(src)
g = cv2.cvtColor(im[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY)
m = ((g < 255 - th) if dark else (g > th)).astype(np.uint8) * 255
m = cv2.dilate(m, np.ones((7, 7), np.uint8), iterations=2)
mask = np.zeros(im.shape[:2], np.uint8); mask[y0:y1, x0:x1] = m
cv2.imwrite(dst, cv2.inpaint(im, mask, 9, cv2.INPAINT_TELEA))
print(f"{dst}: {int(m.sum() / 255)} px masked in box {x0},{y0}–{x1},{y1}")
