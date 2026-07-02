from PIL import Image, ImageDraw, ImageFont
import os

BG    = (13, 13, 13)
TITLE = (167, 139, 250)
BOOK  = (107, 114, 128)

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
PAD         = 16
LINE_HT     = 16
LINE_HB     = 16

ft = ImageFont.truetype(FONT_PATH, FONT_SIZE_T)
fb = ImageFont.truetype(FONT_PATH, FONT_SIZE_B)

height = PAD + len(TITLE_LINES) * LINE_HT + 12 + len(BOOK_LINES) * LINE_HB + PAD
img = Image.new("RGB", (860, height), BG)
d   = ImageDraw.Draw(img)

y = PAD
for line in TITLE_LINES:
    d.text((PAD, y), line, font=ft, fill=TITLE)
    y += LINE_HT
y += 12
for line in BOOK_LINES:
    d.text((PAD, y), line, font=fb, fill=BOOK)
    y += LINE_HB

out = os.path.join(os.path.dirname(__file__), "..", "assets", "banner.png")
img.save(os.path.abspath(out))
print(f"saved: {os.path.abspath(out)} ({img.size[0]}x{img.size[1]})")
