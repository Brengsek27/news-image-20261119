import math
import struct
import zlib

W = H = 1024
PAPER = (247, 242, 228)
INK = (32, 42, 42)
MUTED = (85, 91, 83)
GOLD = (179, 137, 62)
PALE = (235, 226, 205)
TEAL = (34, 105, 105)
CORAL = (188, 83, 59)
BLUE = (51, 83, 113)

pixels = [bytearray(PAPER * W) for _ in range(H)]


def blend(x, y, color, alpha=1.0):
    if x < 0 or y < 0 or x >= W or y >= H or alpha <= 0:
        return
    row = pixels[y]
    at = x * 3
    if alpha >= 1:
        row[at:at + 3] = bytes(color)
    else:
        for channel in range(3):
            row[at + channel] = round(row[at + channel] * (1 - alpha) + color[channel] * alpha)


def smoothstep(edge0, edge1, value):
    t = max(0.0, min(1.0, (value - edge0) / (edge1 - edge0)))
    return t * t * (3 - 2 * t)


def rounded_rect(x0, y0, x1, y1, radius, color):
    pad = 1
    for y in range(max(0, int(y0) - pad), min(H, int(y1) + pad + 1)):
        for x in range(max(0, int(x0) - pad), min(W, int(x1) + pad + 1)):
            qx = abs(x + 0.5 - (x0 + x1) / 2) - ((x1 - x0) / 2 - radius)
            qy = abs(y + 0.5 - (y0 + y1) / 2) - ((y1 - y0) / 2 - radius)
            outside = math.hypot(max(qx, 0), max(qy, 0))
            distance = outside + min(max(qx, qy), 0) - radius
            blend(x, y, color, 1 - smoothstep(-0.65, 0.65, distance))


def circle(cx, cy, radius, color):
    for y in range(max(0, int(cy - radius - 1)), min(H, int(cy + radius + 2))):
        for x in range(max(0, int(cx - radius - 1)), min(W, int(cx + radius + 2))):
            distance = math.hypot(x + 0.5 - cx, y + 0.5 - cy) - radius
            blend(x, y, color, 1 - smoothstep(-0.65, 0.65, distance))


def star(cx, cy, outer_radius, inner_radius, color):
    vertices = []
    for index in range(10):
        angle = -math.pi / 2 + index * math.pi / 5
        radius = outer_radius if index % 2 == 0 else inner_radius
        vertices.append((cx + math.cos(angle) * radius, cy + math.sin(angle) * radius))
    for y in range(max(0, int(cy - outer_radius - 1)), min(H, int(cy + outer_radius + 2))):
        for x in range(max(0, int(cx - outer_radius - 1)), min(W, int(cx + outer_radius + 2))):
            px, py = x + 0.5, y + 0.5
            inside = False
            edge_distance = outer_radius
            for index, (x0, y0) in enumerate(vertices):
                x1, y1 = vertices[(index + 1) % len(vertices)]
                if (y0 > py) != (y1 > py) and px < (x1 - x0) * (py - y0) / (y1 - y0) + x0:
                    inside = not inside
                dx, dy = x1 - x0, y1 - y0
                length2 = dx * dx + dy * dy or 1
                t = max(0.0, min(1.0, ((px - x0) * dx + (py - y0) * dy) / length2))
                edge_distance = min(edge_distance, math.hypot(px - (x0 + t * dx), py - (y0 + t * dy)))
            signed_distance = -edge_distance if inside else edge_distance
            blend(x, y, color, 1 - smoothstep(-0.65, 0.65, signed_distance))


def line(x0, y0, x1, y1, width, color):
    radius = width / 2
    left, right = min(x0, x1) - radius - 1, max(x0, x1) + radius + 1
    top, bottom = min(y0, y1) - radius - 1, max(y0, y1) + radius + 1
    dx, dy = x1 - x0, y1 - y0
    length2 = dx * dx + dy * dy or 1
    for y in range(max(0, int(top)), min(H, int(bottom) + 1)):
        for x in range(max(0, int(left)), min(W, int(right) + 1)):
            t = max(0.0, min(1.0, ((x + 0.5 - x0) * dx + (y + 0.5 - y0) * dy) / length2))
            distance = math.hypot(x + 0.5 - (x0 + t * dx), y + 0.5 - (y0 + t * dy)) - radius
            blend(x, y, color, 1 - smoothstep(-0.65, 0.65, distance))


def fill_rect(x0, y0, x1, y1, color):
    xa, xb = max(0, int(x0)), min(W, int(x1))
    ya, yb = max(0, int(y0)), min(H, int(y1))
    value = bytes(color) * max(0, xb - xa)
    for y in range(ya, yb):
        pixels[y][xa * 3:xb * 3] = value


def paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    return a if pa <= pb and pa <= pc else (b if pb <= pc else c)


def png_chunk(kind, data):
    body = kind + data
    return struct.pack('>I', len(data)) + body + struct.pack('>I', zlib.crc32(body) & 0xffffffff)

GLYPHS = {
    'A': ('01110','10001','10001','11111','10001','10001','10001'),
    'B': ('11110','10001','10001','11110','10001','10001','11110'),
    'C': ('01111','10000','10000','10000','10000','10000','01111'),
    'D': ('11110','10001','10001','10001','10001','10001','11110'),
    'E': ('11111','10000','10000','11110','10000','10000','11111'),
    'F': ('11111','10000','10000','11110','10000','10000','10000'),
    'G': ('01111','10000','10000','10111','10001','10001','01111'),
    'H': ('10001','10001','10001','11111','10001','10001','10001'),
    'I': ('11111','00100','00100','00100','00100','00100','11111'),
    'J': ('00111','00010','00010','00010','10010','10010','01100'),
    'K': ('10001','10010','10100','11000','10100','10010','10001'),
    'L': ('10000','10000','10000','10000','10000','10000','11111'),
    'M': ('10001','11011','10101','10101','10001','10001','10001'),
    'N': ('10001','11001','10101','10011','10001','10001','10001'),
    'O': ('01110','10001','10001','10001','10001','10001','01110'),
    'P': ('11110','10001','10001','11110','10000','10000','10000'),
    'Q': ('01110','10001','10001','10001','10101','10010','01101'),
    'R': ('11110','10001','10001','11110','10100','10010','10001'),
    'S': ('01111','10000','10000','01110','00001','00001','11110'),
    'T': ('11111','00100','00100','00100','00100','00100','00100'),
    'U': ('10001','10001','10001','10001','10001','10001','01110'),
    'V': ('10001','10001','10001','10001','10001','01010','00100'),
    'W': ('10001','10001','10001','10101','10101','11011','10001'),
    'X': ('10001','10001','01010','00100','01010','10001','10001'),
    'Y': ('10001','10001','01010','00100','00100','00100','00100'),
    'Z': ('11111','00001','00010','00100','01000','10000','11111'),
    'a': ('00000','01110','00001','01111','10001','10011','01101'),
    'b': ('10000','10000','10110','11001','10001','10001','11110'),
    'c': ('00000','01111','10000','10000','10000','10000','01111'),
    'd': ('00001','00001','01101','10011','10001','10001','01111'),
    'e': ('00000','01110','10001','11111','10000','10000','01111'),
    'f': ('00110','01001','01000','11100','01000','01000','01000'),
    'g': ('00000','01111','10001','10001','01111','00001','11110'),
    'h': ('10000','10000','10110','11001','10001','10001','10001'),
    'i': ('00100','00000','01100','00100','00100','00100','01110'),
    'j': ('00010','00000','00110','00010','00010','10010','01100'),
    'k': ('10000','10000','10010','10100','11000','10100','10010'),
    'l': ('01100','00100','00100','00100','00100','00100','01110'),
    'm': ('00000','11010','10101','10101','10101','10101','10101'),
    'n': ('00000','10110','11001','10001','10001','10001','10001'),
    'o': ('00000','01110','10001','10001','10001','10001','01110'),
    'p': ('00000','11110','10001','10001','11110','10000','10000'),
    'q': ('00000','01111','10001','10001','01111','00001','00001'),
    'r': ('00000','10110','11001','10000','10000','10000','10000'),
    's': ('00000','01111','10000','01110','00001','00001','11110'),
    't': ('01000','01000','11100','01000','01000','01001','00110'),
    'u': ('00000','10001','10001','10001','10001','10011','01101'),
    'v': ('00000','10001','10001','10001','10001','01010','00100'),
    'w': ('00000','10001','10001','10101','10101','10101','01010'),
    'x': ('00000','10001','01010','00100','00100','01010','10001'),
    'y': ('00000','10001','10001','10001','01111','00001','11110'),
    'z': ('00000','11111','00010','00100','01000','10000','11111'),
    '0': ('01110','10001','10011','10101','11001','10001','01110'),
    '1': ('00100','01100','00100','00100','00100','00100','01110'),
    '2': ('01110','10001','00001','00010','00100','01000','11111'),
    '3': ('11110','00001','00001','01110','00001','00001','11110'),
    '4': ('00010','00110','01010','10010','11111','00010','00010'),
    '5': ('11111','10000','10000','11110','00001','00001','11110'),
    '6': ('01110','10000','10000','11110','10001','10001','01110'),
    '7': ('11111','00001','00010','00100','01000','01000','01000'),
    '8': ('01110','10001','10001','01110','10001','10001','01110'),
    '9': ('01110','10001','10001','01111','00001','00001','01110'),
    ' ': ('00000','00000','00000','00000','00000','00000','00000'),
    '.': ('00000','00000','00000','00000','00000','00100','00100'),
    ',': ('00000','00000','00000','00000','00100','00100','01000'),
    ';': ('00000','00100','00100','00000','00100','00100','01000'),
    ':': ('00000','00100','00100','00000','00100','00100','00000'),
    "'": ('00100','00100','00010','00000','00000','00000','00000'),
    '-': ('00000','00000','00000','11111','00000','00000','00000'),
    '!': ('00100','00100','00100','00100','00100','00000','00100'),
}


def text_width(text, sx, advance=None):
    if not text:
        return 0
    advance = 6 * sx if advance is None else advance
    return (len(text) - 1) * advance + 5 * sx


def wrap_text(text, max_width, sx, advance=None):
    words = text.split(' ')
    lines, line_text = [], ''
    for word in words:
        candidate = word if not line_text else line_text + ' ' + word
        if line_text and text_width(candidate, sx, advance) > max_width:
            lines.append(line_text)
            line_text = word
        else:
            line_text = candidate
        if text_width(line_text, sx, advance) > max_width:
            raise ValueError('Word exceeds available line width: ' + line_text)
    if line_text:
        lines.append(line_text)
    return lines


def draw_text(text, x, y, color, sx, sy, advance=None, serif=False):
    advance = 6 * sx if advance is None else advance
    for index, character in enumerate(text):
        if character not in GLYPHS:
            raise ValueError('Missing glyph: ' + repr(character))
        gx = x + index * advance
        for row_index, row in enumerate(GLYPHS[character]):
            for column_index, bit in enumerate(row):
                if bit == '1':
                    left = gx + column_index * sx
                    top = y + row_index * sy
                    rounded_rect(left, top, left + sx * 0.98, top + sy * 0.96, min(sx, sy) * 0.08, color)
            if serif and row_index in (0, 6) and '1' in row:
                first_bit = row.index('1')
                last_bit = row.rindex('1')
                left = gx + first_bit * sx - sx * 0.52
                right = gx + (last_bit + 1) * sx + sx * 0.52
                top = y + row_index * sy
                rounded_rect(left, top, right, top + sy * 0.5, sy * 0.18, color)


def draw_city_controller(x, y):
    rounded_rect(x, y, x + 356, y + 164, 14, BLUE)
    circle(x + 286, y + 45, 39, (224, 173, 106))
    for bx, bw, bh, color in [(0, 52, 62, (50, 84, 98)), (48, 47, 96, (48, 99, 106)),
                              (94, 66, 76, (67, 119, 119)), (158, 45, 112, (40, 72, 92)),
                              (202, 63, 88, (59, 105, 111)), (263, 45, 124, (42, 76, 95)),
                              (306, 50, 70, (57, 106, 107))]:
        fill_rect(x + bx, y + 164 - bh, x + bx + bw, y + 164, color)
        for wx in range(x + bx + 9, x + bx + bw - 5, 17):
            for wy in range(y + 164 - bh + 11, y + 154, 21):
                fill_rect(wx, wy, wx + 5, wy + 8, (226, 192, 126))
    rounded_rect(x + 93, y + 103, x + 276, y + 151, 19, INK)
    rounded_rect(x + 97, y + 99, x + 272, y + 145, 18, PAPER)
    rounded_rect(x + 119, y + 111, x + 157, y + 119, 3, INK)
    rounded_rect(x + 134, y + 96, x + 142, y + 134, 3, INK)
    circle(x + 232, y + 112, 6, CORAL)
    circle(x + 249, y + 128, 6, TEAL)
    circle(x + 250, y + 98, 5, GOLD)
    circle(x + 266, y + 114, 5, BLUE)
    circle(x + 184, y + 121, 7, PALE)
    circle(x + 204, y + 121, 7, PALE)


def draw_scales(cx, cy, scale=1.0):
    stroke = 7 * scale
    line(cx, cy - 43 * scale, cx, cy + 41 * scale, stroke, INK)
    line(cx - 47 * scale, cy - 23 * scale, cx + 47 * scale, cy - 23 * scale, stroke, GOLD)
    line(cx, cy - 41 * scale, cx, cy - 58 * scale, stroke, GOLD)
    circle(cx, cy - 58 * scale, 5 * scale, GOLD)
    line(cx - 34 * scale, cy - 21 * scale, cx - 48 * scale, cy + 11 * scale, 3 * scale, GOLD)
    line(cx - 34 * scale, cy - 21 * scale, cx - 20 * scale, cy + 11 * scale, 3 * scale, GOLD)
    line(cx + 34 * scale, cy - 21 * scale, cx + 20 * scale, cy + 11 * scale, 3 * scale, GOLD)
    line(cx + 34 * scale, cy - 21 * scale, cx + 48 * scale, cy + 11 * scale, 3 * scale, GOLD)
    line(cx - 52 * scale, cy + 12 * scale, cx - 16 * scale, cy + 12 * scale, 5 * scale, TEAL)
    line(cx + 16 * scale, cy + 12 * scale, cx + 52 * scale, cy + 12 * scale, 5 * scale, CORAL)
    line(cx - 30 * scale, cy + 45 * scale, cx + 30 * scale, cy + 45 * scale, 7 * scale, INK)
    line(cx - 20 * scale, cy + 34 * scale, cx + 20 * scale, cy + 34 * scale, 5 * scale, INK)


def draw_capitol(cx, cy):
    fill_rect(cx - 27, cy + 10, cx + 27, cy + 15, INK)
    fill_rect(cx - 23, cy + 16, cx + 23, cy + 20, GOLD)
    for dx in (-18, -6, 6, 18):
        rounded_rect(cx + dx - 2, cy - 2, cx + dx + 2, cy + 10, 1, INK)
    circle(cx, cy - 7, 12, GOLD)
    fill_rect(cx - 10, cy - 7, cx + 10, cy + 1, PAPER)
    line(cx - 10, cy + 1, cx + 10, cy + 1, 4, INK)
    line(cx - 30, cy + 24, cx + 30, cy + 24, 4, INK)
    line(cx - 24, cy + 29, cx + 24, cy + 29, 4, GOLD)


def draw_summit_flags(cx, cy):
    for dx, color, height in [(-26, CORAL, 28), (0, TEAL, 35), (26, BLUE, 30)]:
        line(cx + dx, cy - height, cx + dx, cy + 18, 2.5, INK)
        rounded_rect(cx + dx + 2, cy - height + 2, cx + dx + 16, cy - height + 13, 2, color)
        circle(cx + dx + 9, cy - height + 7, 1.8, PAPER)
    rounded_rect(cx - 38, cy + 16, cx + 38, cy + 22, 3, GOLD)


def draw_cyclone(cx, cy):
    for radius, start, end, width, color in [(23, 20, 305, 3.5, TEAL), (15, 160, 505, 3, BLUE), (7, 205, 540, 3, CORAL)]:
        points = []
        for step in range(81):
            angle = math.radians(start + (end - start) * step / 80)
            r = radius * (1 - 0.78 * step / 80)
            points.append((cx + math.cos(angle) * r, cy + math.sin(angle) * r))
        for first, second in zip(points, points[1:]):
            line(first[0], first[1], second[0], second[1], width, color)
    line(cx - 23, cy + 19, cx - 31, cy + 23, 3, GOLD)
    line(cx - 23, cy + 19, cx - 22, cy + 28, 3, GOLD)


def draw_voyager(cx, cy):
    for sx, sy in [(-27, -20), (26, -25), (-30, 21), (30, 22), (7, -30)]:
        circle(cx + sx, cy + sy, 2.5, GOLD)
    line(cx - 30, cy, cx + 29, cy, 3.5, INK)
    line(cx, cy - 28, cx, cy + 28, 3.5, GOLD)
    circle(cx, cy, 12, GOLD)
    circle(cx, cy, 7, PAPER)
    rounded_rect(cx - 28, cy - 8, cx - 10, cy + 8, 2, BLUE)
    rounded_rect(cx + 10, cy - 8, cx + 28, cy + 8, 2, BLUE)
    line(cx - 27, cy - 3, cx - 11, cy - 3, 2, PAPER)
    line(cx + 11, cy + 3, cx + 27, cy + 3, 2, PAPER)
    line(cx, cy - 11, cx + 13, cy - 24, 3, INK)


def draw_eu_stars(cx, cy):
    circle(cx, cy, 27, PALE)
    circle(cx, cy, 21, PAPER)
    for index in range(12):
        angle = -math.pi / 2 + index * math.tau / 12
        star(cx + math.cos(angle) * 23, cy + math.sin(angle) * 23, 3.4, 1.5, GOLD)


def draw_badge(cx, cy, icon):
    circle(cx, cy, 28, PALE)
    circle(cx, cy, 24, (251, 248, 239))
    icon(cx, cy)


def draw_wrapped_text(text, x, y, max_width, color, sx, sy, advance, line_step, max_lines=2):
    lines = wrap_text(text, max_width, sx, advance)
    if len(lines) > max_lines:
        raise ValueError(f'Text requires more than {max_lines} lines: {text}')
    for index, line_text in enumerate(lines):
        measured_width = text_width(line_text, sx, advance)
        if measured_width > max_width:
            raise ValueError(f'Text line does not fit: {line_text} ({measured_width}px)')
        draw_text(line_text, x, y + index * line_step, color, sx, sy, advance)
    return lines


def draw_row(y, headline, deck, icon):
    rounded_rect(44, y, 980, y + 80, 10, GOLD)
    rounded_rect(46, y + 2, 978, y + 78, 9, (251, 248, 239))
    draw_badge(94, y + 39, icon)
    headline_width = text_width(headline, 4.3)
    if headline_width + 4 > 810:
        raise ValueError(f'Headline does not fit: {headline} ({headline_width}px)')
    draw_text(headline, 148, y + 1, INK, 4.3, 4.3, serif=True)
    draw_wrapped_text(deck, 148, y + 35, 805, MUTED, 2.1, 2.9, 11.3, 21.5, 2)


def draw_page():
    fill_rect(0, 0, W, H, PAPER)
    masthead = 'THE WORLD IN ONE PAGE'
    date = 'THURSDAY 19 NOVEMBER 2026'
    for text, max_width, sx in [(masthead, 920, 5), (date, 920, 4), ('GTA VI LAUNCHES', 493, 4), ('WORLD COURT RULES TODAY', 790, 3.1)]:
        measured_width = text_width(text, sx)
        if measured_width > max_width:
            raise ValueError(f'Headline does not fit: {text} ({measured_width}px)')
    draw_text(masthead, 55, 26, INK, 5, 6, serif=True)
    draw_text(date, 56, 83, TEAL, 4, 5, serif=True)
    line(48, 137, 976, 137, 3, GOLD)
    line(48, 146, 976, 146, 1, GOLD)

    rounded_rect(43, 157, 981, 349, 16, GOLD)
    rounded_rect(46, 160, 978, 346, 14, (251, 248, 239))
    draw_city_controller(90, 163)
    draw_text('GTA VI LAUNCHES', 485, 181, INK, 4, 4.8, serif=True)
    gta_deck = 'After a 13-year wait, Grand Theft Auto VI begins its global rollout; players return to Vice City.'
    draw_wrapped_text(gta_deck, 485, 260, 467, MUTED, 1.8, 2.9, 10.2, 22, 3)

    rounded_rect(43, 362, 981, 534, 15, GOLD)
    rounded_rect(46, 365, 978, 531, 13, (251, 248, 239))
    draw_text('WORLD COURT RULES TODAY', 70, 379, INK, 3.1, 4.6, serif=True)
    draw_scales(920, 445, 0.9)
    court_deck = 'The world court delivers its judgment today on whether Myanmar committed genocide against the Rohingya.'
    draw_wrapped_text(court_deck, 69, 433, 790, MUTED, 2.1, 2.9, 11.3, 22, 2)

    rows = [
        (546, 'JEFFRIES FOR SPEAKER', 'Democrats nominate Hakeem Jeffries for Speaker of the House; he would be the first African-American Speaker.', draw_capitol),
        (629, 'TRUMP, XI AND PUTIN MEET', 'Trump, Xi and Putin meet in Shenzhen on the sidelines of the APEC summit; nuclear cuts and the US war with Iran on the agenda.', draw_summit_flags),
        (712, 'CYCLONE AKVAN', "Cyclone Akvan bears down on India's east coast, expected to cross between Machilipatnam and Puri.", draw_cyclone),
        (795, 'VOYAGER 1', 'Voyager 1 reaches one light-day from Earth, nearly 50 years after launch; NASA confirms the milestone today.', draw_voyager),
        (878, 'EU UKRAINE LOAN', 'The EU proposes a 45 billion euro loan for Ukraine, to be repaid after Russia pays reparations.', draw_eu_stars),
    ]
    for row in rows:
        draw_row(*row)

    footer = 'Seven stories that defined Thursday 19 November 2026, as reported that day.'
    footer_width = text_width(footer, 1.7, 9.2)
    if footer_width > 920:
        raise ValueError(f'Footer does not fit ({footer_width}px)')
    draw_text(footer, 53, 977, INK, 1.7, 3, 9.2)
    line(48, 1008, 976, 1008, 2, GOLD)


def save_png(path='entry.png'):
    raw_rows = [bytes(row) for row in pixels]
    filtered_rows = bytearray()
    for row_index, raw in enumerate(raw_rows):
        prior = raw_rows[row_index - 1] if row_index else bytes(len(raw))
        candidates = []
        for filter_type in range(5):
            filtered = bytearray(len(raw))
            for index, value in enumerate(raw):
                left = raw[index - 3] if index >= 3 else 0
                up = prior[index]
                upper_left = prior[index - 3] if index >= 3 else 0
                if filter_type == 0:
                    predictor = 0
                elif filter_type == 1:
                    predictor = left
                elif filter_type == 2:
                    predictor = up
                elif filter_type == 3:
                    predictor = (left + up) // 2
                else:
                    predictor = paeth(left, up, upper_left)
                filtered[index] = (value - predictor) & 255
            score = sum(abs(value if value < 128 else value - 256) for value in filtered)
            candidates.append((score, filter_type, filtered))
        _, chosen_filter, chosen = min(candidates, key=lambda candidate: candidate[0])
        filtered_rows.append(chosen_filter)
        filtered_rows.extend(chosen)
    image_data = zlib.compress(bytes(filtered_rows), 9)
    data = (b'\x89PNG\r\n\x1a\n'
            + png_chunk(b'IHDR', struct.pack('>IIBBBBB', W, H, 8, 2, 0, 0, 0))
            + png_chunk(b'IDAT', image_data)
            + png_chunk(b'IEND', b''))
    if len(data) > 1048576:
        raise ValueError(f'PNG exceeds size limit: {len(data)} bytes')
    with open(path, 'wb') as image_file:
        image_file.write(data)
    return len(data)


if __name__ == '__main__':
    draw_page()
    print(f'Wrote entry.png: {save_png()} bytes')
