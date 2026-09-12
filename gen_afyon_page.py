# -*- coding: utf-8 -*-
"""Sadece Afyon sayfasini uretir (diger sayfalara dokunmaz)."""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seo_pages as sp

BASE = os.path.dirname(os.path.abspath(__file__))
keys = list(sp.CITIES.keys())
info = sp.CITIES['afyon']
html = sp.render_city('afyon', info, keys)

for folder in ('rootsite', 'docs'):
    path = os.path.join(BASE, folder, info['slug'])
    with io.open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print('yazildi:', path)

    # sitemap'e ekle
    sm_path = os.path.join(BASE, folder, 'sitemap.xml')
    with io.open(sm_path, encoding='utf-8') as f:
        sm = f.read()
    url = 'https://exampleuser-123.github.io/' + info['slug']
    if url not in sm:
        sm = sm.replace('</urlset>',
                        '  <url><loc>{0}</loc><lastmod>2026-09-12</lastmod></url>\n</urlset>'.format(url))
        with io.open(sm_path, 'w', encoding='utf-8') as f:
            f.write(sm)
        print('sitemap guncellendi:', sm_path)
    else:
        print('sitemap zaten iceriyor:', sm_path)
