# Renderiza el circuito con Edge sin ventana y guarda la imagen y la línea proyectada.
# Uso: python -I fuente/hornear.py <nombre> <w> <h> <cam x,y,z> <mira x,y,z> <fov>
#   -> web/img/<nombre>.webp (+ <nombre>-jpg de control en investigacion/) y web/render/<nombre>.json
import base64, html, io, json, pathlib, re, subprocess, sys
from PIL import Image

RAIZ = pathlib.Path(__file__).resolve().parent.parent
nombre, w, h, cam, mira, fov = sys.argv[1:7]
EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
url = f'http://127.0.0.1:4417/render/circuito.html?w={w}&h={h}&cam={cam}&mira={mira}&fov={fov}'
dom = subprocess.run([EDGE, '--headless=new', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--disable-gpu-sandbox',
                      '--virtual-time-budget=120000', '--dump-dom', url], capture_output=True, timeout=600).stdout.decode('utf-8', 'ignore')
m = re.search(r'<textarea id="salida">(.*?)</textarea>', dom, re.S)
if not m or not m.group(1).strip():
    sys.exit('sin salida: ' + dom[:400])
d = json.loads(html.unescape(m.group(1)))
im = Image.open(io.BytesIO(base64.b64decode(d['img'].split(',', 1)[1]))).convert('RGB')
im.save(RAIZ / 'web' / 'img' / f'{nombre}.webp', quality=80, method=6)
im.save(RAIZ / 'investigacion' / f'{nombre}.jpg', quality=85)
json.dump({'w': d['w'], 'h': d['h'], 'linea': d['linea']}, open(RAIZ / 'web' / 'render' / f'{nombre}.json', 'w'), separators=(',', ':'))
print(nombre, im.size, (RAIZ / 'web' / 'img' / f'{nombre}.webp').stat().st_size // 1024, 'KB')
