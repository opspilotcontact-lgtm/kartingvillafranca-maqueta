"""Monta web/index.html: la plantilla con la vuelta del kart sobre cada render.
La línea central viene proyectada con la misma cámara del render (web/render/<nombre>.json).
Uso: python -I fuente/pista.py && python -I fuente/hornear.py ... && python -I fuente/generar.py
"""
import json, pathlib

RAIZ = pathlib.Path(__file__).resolve().parent.parent
F = RAIZ / 'fuente'


def vuelta(nombre, clase):
    d = json.load(open(RAIZ / 'web' / 'render' / f'{nombre}.json'))
    pts = d['linea']
    ruta = 'M' + ' '.join(f'{x:.0f} {y:.0f}' for x, y in pts) + 'Z'
    x0, y0 = pts[0]
    return (f'<svg class="vuelta {clase}" viewBox="0 0 {d["w"]} {d["h"]}" preserveAspectRatio="none" aria-hidden="true">'
            f'<path class="estela" d="{ruta}"/><circle class="kart" cx="{x0:.0f}" cy="{y0:.0f}" r="{11 if d["w"] > 2000 else 9}"/></svg>')


html = (F / 'plantilla.html').read_text(encoding='utf-8')
html = html.replace('{{VUELTA_H}}', vuelta('portada', 'vuelta-h')).replace('{{VUELTA_M}}', vuelta('portada-m', 'vuelta-m'))
assert '{{' not in html
(RAIZ / 'web' / 'index.html').write_text(html, encoding='utf-8')
(RAIZ / 'web' / 'robots.txt').write_text('User-agent: *\nDisallow: /\n', encoding='utf-8')
print('web/index.html', len(html.encode('utf-8')), 'bytes')
