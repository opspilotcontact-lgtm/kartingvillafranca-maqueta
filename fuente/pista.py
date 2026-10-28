"""Trazado de Karting Villafranca desde OpenStreetMap (ways 1037196628 exterior + 1037196629 interior).

Genera los SVG de la firma (apaisado y vertical) y la silueta del cierre.
Todo en metros: 1 unidad = 1 m. El trazado es ilustrativo (línea central de OSM).
Uso: python -I fuente/pista.py  (desde la raíz del repo)
"""
import json, math, pathlib

RAIZ = pathlib.Path(__file__).resolve().parent.parent
osm = json.load(open(RAIZ / 'investigacion' / 'osm.json'))
ways = {e['id']: e['geometry'] for e in osm['elements'] if e.get('tags', {}).get('highway') == 'raceway'}

LAT0, K = 37.9595, 111320
KX = K * math.cos(math.radians(LAT0))
def proy(g): return [((p['lon'] + 4.562) * KX, -(p['lat'] - LAT0) * K) for p in g]

ext = proy(ways[1037196628])[:-1]          # bucle cerrado sin el punto repetido
inn = proy(ways[1037196629])
A, B = inn[0], inn[-1]

def cerca(p): return min(range(len(ext)), key=lambda i: math.dist(ext[i], p))
ia, ib = cerca(A), cerca(B)
n = len(ext)
# tramo del exterior entre los dos empalmes: se queda el LARGO y el corto se cambia por la variante
def tramo(i, j):
    out = [ext[i]]
    while i != j:
        i = (i + 1) % n; out.append(ext[i])
    return out
t1, t2 = tramo(ib, ia), tramo(ia, ib)
largo = t1 if len(t1) > len(t2) else t2
# el largo va de un empalme al otro; se cierra con la variante en el sentido que toque
if math.dist(largo[-1], inn[0]) < math.dist(largo[-1], inn[-1]):
    lazo = largo + inn
else:
    lazo = largo + inn[::-1]

# remuestreo cada 1,5 m
def remuestrea(pts, paso=1.5):
    pts = pts + [pts[0]]
    out = [pts[0]]; resto = 0.0
    for a, b in zip(pts, pts[1:]):
        d = math.dist(a, b); s = paso - resto
        while s <= d:
            t = s / d; out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)); s += paso
        resto = d - (s - paso)
    return out
P = remuestrea(lazo, 2.2)
# suavizado ligero (media móvil circular)
def suaviza(pts, k=3):
    m = len(pts)
    return [(sum(pts[(i + j) % m][0] for j in range(-k, k + 1)) / (2 * k + 1),
             sum(pts[(i + j) % m][1] for j in range(-k, k + 1)) / (2 * k + 1)) for i in range(m)]
P = suaviza(suaviza(P))
m = len(P)
largo_m = sum(math.dist(P[i], P[(i + 1) % m]) for i in range(m))

# encuadre
xs = [p[0] for p in P]; ys = [p[1] for p in P]
MARGEN = 9
X0, Y0 = min(xs) - MARGEN, min(ys) - MARGEN
W, H = max(xs) - min(xs) + 2 * MARGEN, max(ys) - min(ys) + 2 * MARGEN
P = [(x - X0, y - Y0) for x, y in P]

# rumbo y curvatura (giro en 6 m a cada lado)
def rumbo(i): a, b = P[(i - 1) % m], P[(i + 1) % m]; return math.atan2(b[1] - a[1], b[0] - a[0])
def giro(i, k=3):
    d = rumbo((i + k) % m) - rumbo((i - k) % m)
    return (d + math.pi) % (2 * math.pi) - math.pi
G = [giro(i) for i in range(m)]

# pianos: tramos con giro fuerte, en el lado EXTERIOR de la curva
ANCHO = 7.0
def normal(i):
    r = rumbo(i); return (-math.sin(r), math.cos(r))
pianos = []; i = 0
while i < m:
    if abs(G[i]) > 0.30:
        j = i
        while j < m and abs(G[j]) > 0.30 and (G[j] > 0) == (G[i] > 0): j += 1
        if j - i >= 3:
            lado = -1 if G[i] > 0 else 1          # exterior
            seg = []
            for k in range(i - 1, j + 1):
                nx, ny = normal(k % m); q = P[k % m]
                seg.append((q[0] + nx * lado * (ANCHO / 2 + .9), q[1] + ny * lado * (ANCHO / 2 + .9)))
            pianos.append(seg)
        i = j
    else:
        i += 1

# recta de meta: la tirada más larga casi sin giro
mejor = (0, 0); i = 0
while i < m:
    j = i
    while j < m and abs(G[j]) < 0.05: j += 1
    if j - i > mejor[1] - mejor[0]: mejor = (i, j)
    i = j + 1
r0, r1 = mejor
recta_m = (r1 - r0) * 2.2
# la vuelta empieza en la línea de meta (70 % de la recta) para que el kart salga de la parrilla
meta = r0 + int((r1 - r0) * .72)
P = P[meta:] + P[:meta]; G = G[meta:] + G[:meta]
pianos_idx = None
r0, r1 = (r0 - meta) % m, (r1 - meta) % m

def d(pts, cerrar=False):
    s = 'M' + ' '.join(f'{x:.1f} {y:.1f}'.replace('.0 ', ' ') for x, y in pts)
    return s + ('Z' if cerrar else '')

linea = d(P, True)
def rumbo2(i): a, b = P[(i - 1) % m], P[(i + 1) % m]; return math.atan2(b[1] - a[1], b[0] - a[0])
def normal2(i): r = rumbo2(i); return (-math.sin(r), math.cos(r))
hx, hy = normal2(0); rx, ry = math.cos(rumbo2(0)), math.sin(rumbo2(0))
q = P[0]
# línea de meta a cuadros: dos filas de cuadros a lo ancho de la pista
cuadros = []
c = ANCHO / 7
for fila in range(2):
    for k in range(7):
        if (k + fila) % 2: continue
        ox = (k - 3.5) * c; oy = fila * c - c
        x = q[0] + hx * ox + rx * oy; y = q[1] + hy * ox + ry * oy
        cuadros.append((x, y))
ang = math.degrees(rumbo2(0))
meta_svg = ''.join(f'<rect x="{x:.2f}" y="{y:.2f}" width="{c:.2f}" height="{c:.2f}" transform="rotate({ang:.1f} {x:.2f} {y:.2f})"/>' for x, y in cuadros)

# parrilla: cajones escalonados detrás de la meta (marcas en L como en su recta)
caj = ''
for k in range(6):
    i = (-(3 + k * 3)) % m
    p = P[i]; nx, ny = normal2(i); tx, ty = math.cos(rumbo2(i)), math.sin(rumbo2(i))
    lado = 1 if k % 2 else -1
    cx, cy = p[0] + nx * lado * 1.6, p[1] + ny * lado * 1.6
    a = (cx - nx * 1.3, cy - ny * 1.3); b = (cx + nx * 1.3, cy + ny * 1.3)
    caj += f'<path d="M{a[0]:.1f} {a[1]:.1f}L{b[0]:.1f} {b[1]:.1f}"/>'

# pórtico: centro y ángulo para colocar el logo sobre la recta (unos 30 m detrás de la meta)
ip = (-int(34 / 2.2)) % m
portico = P[ip]; ang_portico = math.degrees(rumbo2(ip))

# barreras rojo-blanco junto a la recta (lado exterior)
barr = []
for k in range(2, (r1 - r0) % m - 2):
    i = (r0 + k) % m; nx, ny = normal2(i); p = P[i]
    barr.append((p[0] - nx * (ANCHO / 2 + 2.2), p[1] - ny * (ANCHO / 2 + 2.2)))

pianos_svg = ''.join(f'<path d="{d(s)}"/>' for s in pianos)

def bloque(rot):
    """SVG de la firma. rot=True -> apaisado (girado -90°)."""
    sufijo = 'h' if rot else 'v'
    if rot:
        vb = f'0 0 {H:.1f} {W:.1f}'; g = f'transform="translate(0 {W:.1f}) rotate(-90)"'
    else:
        vb = f'0 0 {W:.1f} {H:.1f}'; g = ''
    # el logo del pórtico va siempre derecho: se coloca fuera del grupo girado
    px, py = portico
    if rot: px, py = py, W - px
    LW = 40; LH = LW * 582 / 1573
    lx = min(max(px - LW / 2, 2), (H if rot else W) - LW - 2)
    ly = py - LH / 2
    k0 = P[0]
    return f'''<svg class="pista pista-{sufijo}" viewBox="{vb}" role="img" aria-label="Trazado del circuito de Karting Villafranca: la recta de meta con su parrilla, los pianos azules de las curvas y el pórtico con el logo">
<defs><path id="l{sufijo}" d="{linea}"/></defs>
<g {g}>
<use href="#l{sufijo}" class="borde"/>
<use href="#l{sufijo}" class="asfalto"/>
<g class="pianos"><g class="pb">{pianos_svg}</g><g class="pa">{pianos_svg}</g></g>
<path class="barrera" d="{d(barr)}"/>
<g class="parrilla">{caj}</g>
<g class="meta">{meta_svg}</g>
<g class="kart" transform="translate({k0[0]:.1f} {k0[1]:.1f})"><circle class="aura" r="5"/><circle r="2.4"/></g>
</g>
<g class="portico"><rect x="{lx - 1:.1f}" y="{ly - 1:.1f}" width="{LW + 2}" height="{LH + 2:.1f}" rx="2"/><image href="img/logo-villafranca-s.webp" x="{lx:.1f}" y="{ly:.1f}" width="{LW}" height="{LH:.1f}"/></g>
</svg>'''

# silueta para el cierre (solo la línea, en un color)
silueta = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {H:.1f} {W:.1f}"><g transform="translate(0 {W:.1f}) rotate(-90)"><path d="{linea}" fill="none" stroke="#fff" stroke-width="{ANCHO}" stroke-linejoin="round"/></g></svg>'

(RAIZ / 'fuente' / 'pista-h.svg.frag').write_text(bloque(True), encoding='utf-8')
(RAIZ / 'fuente' / 'pista-v.svg.frag').write_text(bloque(False), encoding='utf-8')
(RAIZ / 'web' / 'img' / 'trazado.svg').write_text(silueta, encoding='utf-8')
json.dump({'W': W, 'H': H, 'largo_osm_m': round(largo_m), 'recta_m': recta_m, 'pianos': len(pianos),
           'portico': {'x': portico[0], 'y': portico[1], 'ang': ang_portico}},
          open(RAIZ / 'fuente' / 'pista.json', 'w'), indent=1)
print(f'largo OSM {largo_m:.0f} m · recta {recta_m:.0f} m · {len(pianos)} pianos · caja {W:.0f}×{H:.0f} m · pórtico {portico} {ang_portico:.0f}°')

# geometría en metros para la escena 3D (render/circuito.html): x a la derecha, y hacia abajo (como el SVG vertical)
grid = []
for k in range(6):
    i = (-(3 + k * 3)) % m
    p = P[i]; nx, ny = normal2(i); lado = 1 if k % 2 else -1
    grid.append({'x': p[0] + nx * lado * 1.6, 'y': p[1] + ny * lado * 1.6, 'ang': rumbo2(i)})
json.dump({
    'W': W, 'H': H, 'ancho': ANCHO,
    'linea': [[round(x, 2), round(y, 2)] for x, y in P],
    'pianos': [[[round(x, 2), round(y, 2)] for x, y in s] for s in pianos],
    'barrera': [[round(x, 2), round(y, 2)] for x, y in barr],
    'parrilla': grid,
    'portico': {'x': portico[0], 'y': portico[1], 'ang': rumbo2(ip)},
    'meta': {'x': P[0][0], 'y': P[0][1], 'ang': rumbo2(0)},
}, open(RAIZ / 'web' / 'render' / 'pista-geo.json', 'w'), separators=(',', ':'))
