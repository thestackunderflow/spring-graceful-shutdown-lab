"""Frame-0 cards (light terminal look) from the lab's real lines: hook-landscape.png (2560x1440) for the long video and
short-frame0.png (1080x1920) for the Short. Values copied from evidence/s1-default (client.txt, result.json, app.log)."""
from PIL import Image, ImageDraw, ImageFont
MONO = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'; BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf'
LINES = [('$ docker stop sgs-app', 0), ('  (took 10.42 s, exit code 137)', 1), ('', 0),
         ('14:13:15.435  Commencing graceful shutdown.', 0), ('  Waiting for active requests to complete', 0), ('', 0),
         ('client: curl: (52) Empty reply from server', 1)]
def card(path, W, H, size, title, note):
    im = Image.new('RGB', (W, H), '#f6f7f9'); d = ImageDraw.Draw(im)
    m = int(W * 0.05); top = int(H * 0.12) if H > W else 150
    d.rounded_rectangle((m, top, W - m, H - top), 28, fill='#ffffff', outline='#d8dde5', width=4)
    d.rectangle((m, top, W - m, top + 80), fill='#e3e7ee')
    for i, c in enumerate(('#e5534b', '#d9a400', '#2da44e')): d.ellipse((m + 40 + i * 50, top + 25, m + 70 + i * 50, top + 55), fill=c)
    d.text((m + 220, top + 22), title, font=ImageFont.truetype(BOLD, int(size * 0.85)), fill='#1a2230')
    f = ImageFont.truetype(MONO, size); y = top + 140
    for ln, hot in LINES:
        d.text((m + 60, y), ln, font=f, fill='#c62828' if hot else '#1a2230'); y += int(size * 1.6)
    d.text((m + 10, H - top + 30), note, font=ImageFont.truetype(MONO, int(size * 0.65)), fill='#5b6678')
    im.save(path)
card('/v/hook-landscape.png', 2560, 1440, 58, 'Spring Boot 4.1.1 · graceful shutdown ON', 'Real lab run s1-default (docker stop, defaults): log and curl lines as recorded; time and exit code measured')
card('/v/short-frame0.png', 1080, 1920, 30, 'graceful shutdown ON', 'Real lab run s1-default')
