#!/usr/bin/env python3
"""
Campagne — site bouwen voor Cloudflare Pages
============================================
Cloudflare draait dit script bij elke publicatie: productie (main) én elke
preview (branches, pull requests en CMS-concepten).

1. Draait de paginagenerator, zodat elke preview complete pagina's toont —
   ook van een CMS-concept dat nog niet op main staat.
2. Kopieert alleen de website zelf naar de map _site. Broncode, workflows,
   sjablonen en de git-geschiedenis worden dus níet gepubliceerd.

Faalt de generator, dan stopt dit script met een foutcode. Cloudflare breekt
de publicatie dan af en de vorige versie blijft gewoon online.

Cloudflare-instellingen:  Build command  python3 tools/bouw-site.py
                          Build output   _site
Lokaal testen kan ook:    python3 tools/bouw-site.py   (_site staat in .gitignore)
"""

import os
import shutil
import subprocess
import sys

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOEL = os.path.join(WORTEL, '_site')

# Niet publiceren: alles wat alleen nodig is om de site te bouwen of te beheren.
# (functions/ hoeft er niet in: Cloudflare pakt die map zelf op uit de repo.)
UITSLUITEN = {
    '.git', '.github', '.gitignore', '.DS_Store',
    '_site', 'tools', 'templates', 'functions', 'node_modules', '__pycache__',
    'config.yml',          # oude kopie in de hoofdmap; Sveltia gebruikt admin/config.yml
}
UITSLUITEN_EXTENSIES = ('.py', '.md', '.pyc')


def negeren(map_pad, namen):
    weg = set()
    for naam in namen:
        if naam.startswith('._') or naam.endswith(UITSLUITEN_EXTENSIES):
            weg.add(naam)
        elif naam in UITSLUITEN and (naam != 'config.yml' or map_pad == WORTEL):
            weg.add(naam)
    return weg


def main():
    print('1/2  Paginagenerator draaien', flush=True)
    subprocess.run([sys.executable, os.path.join(WORTEL, 'tools', 'genereer-paginas.py')],
                   check=True, cwd=WORTEL)

    print('2/2  Website kopiëren naar _site')
    if os.path.exists(DOEL):
        shutil.rmtree(DOEL)
    shutil.copytree(WORTEL, DOEL, ignore=negeren)

    # Vangnet: zonder deze bestanden is er iets grondig mis — dan liever niet publiceren.
    for verplicht in ('index.html', '404.html', 'admin/index.html', 'admin/config.yml', '_headers'):
        if not os.path.exists(os.path.join(DOEL, verplicht)):
            raise SystemExit(f'FOUT: {verplicht} ontbreekt in _site — publicatie afgebroken.')

    aantal = sum(len([f for f in bestanden if f.endswith('.html')])
                 for _, _, bestanden in os.walk(DOEL))
    print(f'Klaar: {aantal} HTML-pagina\'s klaargezet in _site')


if __name__ == '__main__':
    main()
