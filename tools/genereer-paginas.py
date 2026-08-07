#!/usr/bin/env python3
"""
Campagne — paginagenerator
==========================
Maakt van elke case in cases.json en elk onderwerp in diensten.json een echte
HTML-pagina, op basis van de templates in /templates.

Waarom: Sveltia beheert de inhoud, maar maakt zelf geen HTML-pagina's. Dit script
vult dat gat. Het draait automatisch via GitHub Actions zodra er iets in het CMS
wordt opgeslagen, dus na het toevoegen van een case staat de detailpagina er
vanzelf — zonder dat er handmatig een bestand gekopieerd hoeft te worden.

Belangrijk:
  * Alles tussen de EIGEN-INHOUD-markers in een bestaande pagina blijft staan.
    Daar kun je vrij eigen HTML kwijt onder de vouw.
  * Menu, header, footer en het SVG-sprite worden bij elke run uit index.html
    overgenomen. index.html is en blijft dus de master.
  * Pagina's die niet meer bij een case of onderwerp horen worden opgeruimd,
    maar alleen als ze de GEGENEREERD-markering dragen. Handgemaakte pagina's
    blijven altijd met rust.

Gebruik:  python3 tools/genereer-paginas.py [--controle]
          --controle schrijft niets weg en meldt alleen wat er zou veranderen.
"""

import json
import os
import re
import sys

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARKERING = 'CAMPAGNE:GEGENEREERD'
START = '<!-- CAMPAGNE:EIGEN-INHOUD-START -->'
EINDE = '<!-- CAMPAGNE:EIGEN-INHOUD-EINDE -->'
PLACEHOLDER = 'images/placeholder.webp'


# ----------------------------------------------------------------- hulpjes
def lees(pad):
    with open(os.path.join(WORTEL, pad), encoding='utf-8') as f:
        return f.read()


def lees_json(pad):
    try:
        return json.loads(lees(pad))
    except FileNotFoundError:
        print(f"  ! {pad} niet gevonden — overgeslagen")
        return {}


def esc(waarde):
    """HTML-escape. Alle tekst uit het CMS gaat hier doorheen."""
    return (str('' if waarde is None else waarde)
            .replace('&', '&amp;').replace('<', '&lt;')
            .replace('>', '&gt;').replace('"', '&quot;'))


def regels(waarde):
    """Escape + nieuwe regels als <br>, zoals de CMS-velden bedoeld zijn."""
    return esc(waarde).replace('\n', '<br>')


def beeldpad(waarde, terugval=PLACEHOLDER):
    """De site draait in een submap, dus paden moeten relatief blijven."""
    schoon = str(waarde or '').strip().lstrip('/')
    return schoon or terugval


def plat(waarde, lengte=155):
    """Eén regel platte tekst voor de meta-omschrijving."""
    tekst = re.sub(r'\s+', ' ', str(waarde or '')).strip()
    return esc(tekst[:lengte - 1] + '…' if len(tekst) > lengte else tekst)


def vul(sjabloon, waarden):
    for sleutel, waarde in waarden.items():
        sjabloon = sjabloon.replace('{{' + sleutel + '}}', waarde)
    resterend = sorted(set(re.findall(r'\{\{([A-Z_]+)\}\}', sjabloon)))
    if resterend:
        raise SystemExit(f"FOUT: template mist waarden voor {resterend}")
    return sjabloon


def bestandsnaam(item, voorvoegsel=''):
    """Handmatige naam heeft voorrang, anders afgeleid van de slug."""
    eigen = str(item.get('detailpagina') or '').strip()
    if eigen:
        return eigen if eigen.endswith('.html') else eigen + '.html'
    slug = str(item.get('slug') or '').strip()
    return f"{voorvoegsel}{slug}.html" if slug else ''


# --------------------------------------------------- master uit index.html
def masterblokken():
    """Header, menu, footer en sprite uit index.html — de master."""
    bron = lees('index.html')

    def pak(startpatroon, eindtag):
        m = re.search(startpatroon, bron)
        if not m:
            raise SystemExit(f"FOUT: {startpatroon} niet gevonden in index.html")
        e = bron.find(eindtag, m.end())
        return bron[m.start():e + len(eindtag)]

    header = pak(r'<header class="header">', '</header>')
    menu = pak(r'<nav class="menu-overlay"', '</nav>')
    # op subpagina's wijzen logo en ankers terug naar de homepage
    header = header.replace('href="#" aria-label="Campagne — home"',
                            'href="index.html" aria-label="Campagne — home"')
    menu = menu.replace('href="#diensten"', 'href="index.html#diensten"')
    return {
        'sprite': pak(r'<svg width="0" height="0"[^>]*>', '</svg>'),
        'header': header,
        'menu': menu,
        'footer': pak(r'<footer class="footer"[^>]*>', '</footer>'),
    }


def sync_master(html, blokken):
    """Zet de masterblokken in een gegenereerde pagina."""
    vervangingen = [
        (r'<svg width="0" height="0"[^>]*>.*?</svg>', blokken['sprite']),
        (r'<header class="header">.*?</header>', blokken['header']),
        (r'<nav class="menu-overlay".*?</nav>', blokken['menu']),
        (r'<footer class="footer"[^>]*>.*?</footer>', blokken['footer']),
    ]
    for patroon, nieuw in vervangingen:
        html = re.sub(patroon, lambda m: nieuw, html, count=1, flags=re.S)
    return html


def eigen_inhoud(pad):
    """Haal het zelfgeschreven blok uit een bestaande pagina."""
    vol = os.path.join(WORTEL, pad)
    if not os.path.exists(vol):
        return ''
    with open(vol, encoding='utf-8') as f:
        bestaand = f.read()
    s, e = bestaand.find(START), bestaand.find(EINDE)
    return bestaand[s + len(START):e].strip('\n') if s != -1 and e > s else ''


# ------------------------------------------------------------------- cases
def bouw_case(c, blokken, sjabloon, alle_cases):
    naam = bestandsnaam(c, 'case-')
    klant = c.get('klantnaam') or c.get('naam') or ''
    opdrachtgever = c.get('klant') or klant

    if c.get('hero_video'):
        video = (
            '      <iframe src="https://player.vimeo.com/video/'
            + esc(c['hero_video'])
            + '?background=1&amp;autoplay=1&amp;muted=1&amp;loop=1&amp;autopause=0'
              '&amp;title=0&amp;byline=0&amp;portrait=0&amp;badge=0" '
              'allow="autoplay; fullscreen; picture-in-picture; encrypted-media" '
              'referrerpolicy="strict-origin-when-cross-origin" title="'
            + esc(klant) + '" loading="lazy"></iframe>'
        )
    else:
        video = ''

    kenmerken = [f'      <dt>Klant</dt>\n      <dd>{regels(opdrachtgever)}</dd>']
    if c.get('onderwerp'):
        kenmerken.append(f'\n      <dt>Onderwerp</dt>\n      <dd>{regels(c["onderwerp"])}</dd>')
    if c.get('tags'):
        labels = '<br>'.join(esc(str(t).capitalize()) for t in c['tags'])
        kenmerken.append(f'\n      <dt>Tags</dt>\n      <dd class="tags">{labels}</dd>')

    disciplines = '\n'.join(
        f'        <div class="rij">\n          <h2>{esc(d.get("titel"))}</h2>\n'
        f'          <p>{esc(d.get("tekst"))}</p>\n        </div>'
        for d in c.get('disciplines_detail') or []
    )

    html = vul(sjabloon, {
        'SLUG': esc(c.get('slug')),
        'KLEUR': esc(c.get('merkkleur') or '#ffff00'),
        'PAGINATITEL': esc(klant),
        'OMSCHRIJVING': (esc(c['meta_omschrijving'].strip()) if c.get('meta_omschrijving')
                         else plat(c.get('overzicht_resultaat') or c.get('resultaatregel') or c.get('verhaal'))),
        'HERO_BEELD': esc(beeldpad(c.get('hero_beeld') or c.get('tegelbeeld'))),
        'HERO_ALT': esc(c.get('hero_alt') or c.get('tegelbeeld_alt') or f'Case {klant}'),
        'HERO_VIDEO': video,
        'KLANT': esc(klant),
        'HERO_TITEL': regels(c.get('hero_titel') or c.get('titel')),
        'HERO_RESULTAAT': regels(c.get('hero_resultaat') or c.get('resultaatregel')),
        'KENMERKEN': ''.join(kenmerken),
        'VERHAAL': esc(c.get('verhaal')),
        'DISCIPLINES': disciplines,
        'EIGEN_INHOUD': eigen_inhoud(naam),
    })
    return naam, sync_master(html, blokken)


# ---------------------------------------------------------------- diensten
def case_blok(c):
    """Uitgelichte case onderaan een dienstpagina — zelfde opmaak als elders."""
    doel = bestandsnaam(c, 'case-')
    open_tag = (f'    <a class="case-blok" href="{esc(doel)}"'
                + (f' data-video="{esc(c["hover_video"])}"' if c.get('hover_video') else '')
                + '>') if doel else '    <article class="case-blok">'
    sluit = '    </a>' if doel else '    </article>'
    klant = c.get('klantnaam') or ''
    return (
        f'{open_tag}\n'
        f'      <img loading="lazy" decoding="async" src="{esc(beeldpad(c.get("tegelbeeld")))}" alt="{esc(c.get("tegelbeeld_alt") or f"Case {klant}")}">\n'
        f'      <div class="case-inhoud">\n'
        f'        <span class="case-eyebrow">{esc(klant)}</span>\n'
        f'        <h3 class="case-titel">{regels(c.get("titel"))}</h3>\n'
        f'        <p class="case-resultaat">\n'
        f'          <span class="pijl-knop"><svg class="pijl-svg" aria-hidden="true"><use href="#svg-pijl"></use></svg></span>\n'
        f'          <span>{regels(c.get("resultaatregel"))}</span>\n'
        f'        </p>\n'
        f'      </div>\n{sluit}'
    )


def bouw_dienst(d, groep, blokken, sjabloon, cases_op_slug):
    naam = bestandsnaam(d)
    titel = d.get('titel') or ''

    if d.get('brede_foto'):
        breed = ('<!-- ============================================================ VOL BEELD -->\n'
                 f'<section class="beeld-vol" aria-label="{esc(titel)}">\n  <figure>\n'
                 f'    <img loading="lazy" decoding="async" src="{esc(beeldpad(d["brede_foto"]))}" '
                 f'alt="{esc(d.get("brede_foto_alt") or titel)}">\n  </figure>\n</section>')
    else:
        breed = '<!-- geen brede foto ingesteld in het CMS -->'

    if d.get('quote'):
        bron = f'\n    <cite>&ndash; {esc(d["quote_bron"])} &ndash;</cite>' if d.get('quote_bron') else ''
        tekst = esc(str(d['quote']).strip().strip('“”"'))
        quote = ('<!-- ============================================================ QUOTE -->\n'
                 f'<section class="quote">\n  <blockquote>\n'
                 f'    <p>&ldquo;{tekst}&rdquo;</p>{bron}\n  </blockquote>\n</section>')
    else:
        quote = '<!-- geen quote ingesteld in het CMS -->'

    alineas = [a.strip() for a in re.split(r'\n\s*\n', str(d.get('bloktekst') or '')) if a.strip()]
    bloktekst = '\n'.join(f'      <p>{regels(a)}</p>' for a in alineas) or '      <p></p>'

    gekozen = [cases_op_slug[s] for s in (d.get('cases') or []) if s in cases_op_slug]
    cases_html = '\n'.join(case_blok(c) for c in gekozen)

    html = vul(sjabloon, {
        'SLUG': esc(d.get('slug')),
        'PAGINATITEL': esc(titel),
        'OMSCHRIJVING': (esc(d['meta_omschrijving'].strip()) if d.get('meta_omschrijving')
                         else plat(d.get('introtekst'))),
        'MENUTITEL': esc(titel),
        'GROEP_NAAM': esc(groep.get('naam') if groep else 'Wat wij doen'),
        'GROEP_URL': esc(groep.get('overzicht_url') if groep else 'index.html#diensten'),
        'HERO_BEELD': esc(beeldpad(d.get('headerbeeld'))),
        'HERO_ALT': esc(d.get('headerbeeld_alt') or titel),
        'HERO_TITEL': regels(d.get('hero_titel') or titel),
        'INTROTITEL': esc(d.get('introtitel') or titel),
        'INTROTEKST': regels(d.get('introtekst')),
        'BREED_BEELD': breed,
        'QUOTE': quote,
        'BLOKTITEL': esc(d.get('bloktitel') or titel),
        'BLOKTEKST': bloktekst,
        'CTA_TEKST': regels(d.get('cta_tekst') or 'Wil je meer weten?<br>Neem contact met ons op!'),
        'STAAND_BEELD': esc(beeldpad(d.get('staand_beeld'))),
        'STAAND_ALT': esc(d.get('staand_beeld_alt') or titel),
        'CASES_KOP': esc(d.get('cases_kop') or f'{titel} in actie: succesverhalen.'),
        'CASES': cases_html,
        'EIGEN_INHOUD': eigen_inhoud(naam),
    })
    return naam, sync_master(html, blokken)


# -------------------------------------------------------------------- main
def main():
    controle = '--controle' in sys.argv
    blokken = masterblokken()
    cases = (lees_json('cases.json') or {}).get('cases', [])
    diensten_data = lees_json('diensten.json') or {}
    diensten = diensten_data.get('diensten', [])
    groepen = {g['slug']: g for g in diensten_data.get('groepen', [])}
    cases_op_slug = {c['slug']: c for c in cases if c.get('slug')}

    gewenst, geschreven, ongewijzigd = {}, [], []

    sjabloon_case = lees('templates/case.html')
    for c in cases:
        if c.get('actief') is False or c.get('pagina_aanmaken') is False or not c.get('slug'):
            continue
        naam, html = bouw_case(c, blokken, sjabloon_case, cases)
        if naam:
            gewenst[naam] = html

    sjabloon_dienst = lees('templates/dienst.html')
    for d in diensten:
        if d.get('actief') is False or not d.get('pagina_aanmaken') or not d.get('slug'):
            continue
        groep = groepen.get(str(d.get('groep', '')).lower())
        naam, html = bouw_dienst(d, groep, blokken, sjabloon_dienst, cases_op_slug)
        if naam:
            gewenst[naam] = html

    for naam, html in sorted(gewenst.items()):
        vol = os.path.join(WORTEL, naam)
        bestaand = open(vol, encoding='utf-8').read() if os.path.exists(vol) else None
        if bestaand == html:
            ongewijzigd.append(naam)
            continue
        if not controle:
            with open(vol, 'w', encoding='utf-8') as f:
                f.write(html)
        geschreven.append(naam)

    # opruimen: alleen pagina's die dit script zelf heeft gemaakt
    verwijderd = []
    for naam in sorted(os.listdir(WORTEL)):
        if not naam.endswith('.html') or naam in gewenst:
            continue
        vol = os.path.join(WORTEL, naam)
        with open(vol, encoding='utf-8') as f:
            if MARKERING in f.read(2000):
                if not controle:
                    os.remove(vol)
                verwijderd.append(naam)

    print(f"Gegenereerd : {len(geschreven)}  {geschreven if geschreven else ''}")
    print(f"Ongewijzigd : {len(ongewijzigd)}")
    print(f"Verwijderd  : {len(verwijderd)}  {verwijderd if verwijderd else ''}")
    if controle and (geschreven or verwijderd):
        print("\n(controlestand: er is niets weggeschreven)")


if __name__ == '__main__':
    main()
