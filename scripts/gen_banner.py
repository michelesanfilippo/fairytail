from PIL import Image, ImageDraw, ImageFont

BG    = (28, 28, 32)       # grigio scuro caldo
TITLE = (255, 185, 30)     # giallo canarino tendente arancione
BOOK  = (140, 130, 100)    # grigio caldo per il libro

TITLE_LINES = [
    "███████╗ █████╗ ██╗██████╗ ██╗   ██╗    ████████╗ █████╗ ██╗██╗",
    "██╔════╝██╔══██╗██║██╔══██╗╚██╗ ██╔╝    ╚══██╔══╝██╔══██╗██║██║",
    "█████╗  ███████║██║██████╔╝ ╚████╔╝        ██║   ███████║██║██║",
    "██╔══╝  ██╔══██║██║██╔══██╗  ╚██╔╝         ██║   ██╔══██║██║██║",
    "██║     ██║  ██║██║██║  ██║   ██║          ██║   ██║  ██║██║███████╗",
    "╚═╝     ╚═╝  ╚═╝╚═╝╚═╝  ╚═╝   ╚═╝          ╚═╝   ╚═╝  ╚═╝╚═╝╚══════╝",
]

BOOK_LINES = [
    "     .:+x;:;;++:.....:+:..     ..:x:.....:+x+;:;x+::",
    "     ::.  .......:..::. :.;. .::.  ...:....     .;:",
    "    .;;.   ..    ..   : x       ......         .;;",
    "    .::                : x                       ;:.",
    "    :.:  ......::.. ..: : x  .:..   ..::......  .:.",
    "    ;.;      .:+++:.. .: x    .:+++:...         ::;",
    "   .::;  .....       .. : x  :..         ...... :::",
    "   .:;.  ...:;+;.. ..:..: x   ..;.  ...;+;:.... .;:.",
    "    ;::.       ....   :.; x .:   . ...          ::;",
    "   ;:..;+:..:;x+:.. .:+.  x   .+:.. ..:+x;:...:++..:;",
    "   ::::::::::::::::::::::;...:::::::::::::::::::::::;;",
]

FONT_PATH   = "C:/Windows/Fonts/consola.ttf"
FONT_SIZE_T = 13
FONT_SIZE_B = 13
PAD_V       = 20   # vertical padding top/bottom
PAD_H       = 20   # horizontal padding (unused for centering, kept for reference)
LINE_HT     = 16
LINE_HB     = 16
IMG_W       = 820

ft = ImageFont.truetype(FONT_PATH, FONT_SIZE_T)
fb = ImageFont.truetype(FONT_PATH, FONT_SIZE_B)

height = PAD_V + len(TITLE_LINES) * LINE_HT + 14 + len(BOOK_LINES) * LINE_HB + PAD_V
img = Image.new("RGB", (IMG_W, height), BG)
d   = ImageDraw.Draw(img)

def text_width(text, font):
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0]

# Draw title as a block: find widest line, center that, use same x for all
max_title_w = max(text_width(l, ft) for l in TITLE_LINES)
x_title = (IMG_W - max_title_w) // 2
y = PAD_V
for line in TITLE_LINES:
    d.text((x_title, y), line, font=ft, fill=TITLE)
    y += LINE_HT

y += 14

# Draw book lines centered as a block (center the widest line, align others to same x)
max_w = max(text_width(l, fb) for l in BOOK_LINES)
x_block = (IMG_W - max_w) // 2
for line in BOOK_LINES:
    d.text((x_block, y), line, font=fb, fill=BOOK)
    y += LINE_HB

import os
out = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "banner.png"))
img.save(out)
print(f"saved: {out} ({img.size[0]}x{img.size[1]})")
