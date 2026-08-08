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
# Vaste stukjes footer die op de Engelse pagina's mee moeten vertalen.
# De footer komt uit index.html (Nederlands), dus die vertaling doen we hier.
FOOTER_EN = [
    ('Weena 250 (gebouw Weena 200)<br>', 'Weena 250 (building Weena 200)<br>'),
    ('Toren C, 12e verdieping<br>', 'Tower C, 12th floor<br>'),
]
START = '<!-- CAMPAGNE:EIGEN-INHOUD-START -->'
EINDE = '<!-- CAMPAGNE:EIGEN-INHOUD-EINDE -->'
PLACEHOLDER = 'images/placeholder.webp'
TALEN = ['nl', 'en']          # Nederlands in de hoofdmap, Engels in /en/


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


def veld(item, naam, taal, terugval=True):
    """Waarde in de gevraagde taal. Een leeg Engels veld valt terug op het
    Nederlands, zodat een half vertaalde case nooit gaten in de pagina geeft."""
    if taal != 'nl':
        vertaling = (item.get(taal) or {}).get(naam)
        if vertaling not in (None, '', []):
            return vertaling
        if not terugval:
            return ''
    return item.get(naam, '')


def een_regel(waarde):
    """Titels mogen een regelafbreking bevatten voor de hero; in het menu, de
    paginatitel en alt-teksten moet dat weer één doorlopende regel worden."""
    return re.sub(r'\s*\n\s*', ' ', str(waarde or '')).strip()


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


def bestandsnaam(item, voorvoegsel='', taal='nl'):
    """Bestandsnaam in de gevraagde taal. Nederlands: een eigen naam wint,
    anders de slug. Engels: de Engelse slug uit de vertaling; is die leeg,
    dan valt hij terug op de Nederlandse naam."""
    if taal != 'nl':
        en_slug = str((item.get(taal) or {}).get('slug') or '').strip()
        if en_slug:
            return f"{voorvoegsel}{en_slug}.html"
        return bestandsnaam(item, voorvoegsel)
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


def naar_submap(html, vertaling):
    """Engelse pagina's staan in /en/, dus alles wat relatief is moet een mapje
    omhoog: beelden, het script en links naar pagina's die alleen in het
    Nederlands bestaan. Links naar pagina's die óók een Engelse versie hebben
    worden vervangen door hun Engelse bestandsnaam; die staat in dezelfde map."""
    html = re.sub(r'(src|href)="(images/[^"]*)"', r'\1="../\2"', html)
    html = html.replace('src="cms-data.js"', 'src="../cms-data.js"')

    def link(m):
        attribuut, doel = m.group(1), m.group(2)
        bestand, _, anker = doel.partition('#')
        anker = '#' + anker if anker else ''
        if bestand in vertaling:
            return f'{attribuut}="{vertaling[bestand]}{anker}"'
        return f'{attribuut}="../{doel}"'

    return re.sub(r'(src|href)="([a-z0-9][a-z0-9-]*\.html(?:#[^"]*)?)"', link, html)


def taalknop(html, taal, nl_bestand, en_bestand):
    """De twee knoppen worden echte links naar dezelfde pagina in de andere taal."""
    if taal == 'nl':
        naar_en, naar_nl = f'en/{en_bestand}', nl_bestand
    else:
        naar_en, naar_nl = en_bestand, f'../{nl_bestand}'
    actief_en = ' class="actief"' if taal != 'nl' else ''
    actief_nl = ' class="actief"' if taal == 'nl' else ''
    knoppen = (
        f'<div class="taalswitch" data-taal="{taal}" role="group" aria-label="Taalkeuze">\n'
        f'      <a href="{naar_en}" hreflang="en"{actief_en}>EN</a>\n'
        f'      <a href="{naar_nl}" hreflang="nl"{actief_nl}>NL</a>\n'
        f'    </div>'
    )
    return re.sub(r'<div class="taalswitch".*?</div>', lambda m: knoppen, html, count=1, flags=re.S)


def opengraph(titel, omschrijving, beeld, bestand, taal, inst):
    """De tags die bepalen hoe een gedeelde link eruitziet in WhatsApp, LinkedIn
    en Slack. Adressen moeten absoluut zijn, vandaar het site-adres uit
    instellingen.json."""
    basis = str(inst.get('site_url') or '').rstrip('/')
    map_deel = 'en/' if taal != 'nl' else ''
    adres = f'{basis}/{map_deel}{bestand}'
    bron = beeldpad(beeld, inst.get('deelbeeld') or PLACEHOLDER)
    naam = esc(inst.get('site_naam') or 'Campagne')
    taalcode = 'nl_NL' if taal == 'nl' else 'en_US'
    regels_og = [
        '<meta property="og:type" content="article">',
        f'<meta property="og:site_name" content="{naam}">',
        f'<meta property="og:locale" content="{taalcode}">',
        f'<meta property="og:title" content="{titel}">',
        f'<meta property="og:description" content="{omschrijving}">',
        f'<meta property="og:url" content="{adres}">',
        f'<meta property="og:image" content="{basis}/{bron}">',
        '<meta name="twitter:card" content="summary_large_image">',
    ]
    return '\n'.join(regels_og)


def pad_in_taal(bestand, taal):
    return bestand if taal == 'nl' else os.path.join('en', bestand)


def afwerken(html, blokken, taal, nl_bestand, en_bestand, vertaling):
    """Master-blokken erin, taal instellen, taalknop koppelen en — voor Engels —
    alle relatieve paden en links omzetten naar de Engelse variant."""
    html = sync_master(html, blokken)
    if taal != 'nl':
        html = html.replace('<html lang="nl"', '<html lang="en"', 1)
        for nl_tekst, en_tekst in FOOTER_EN:
            html = html.replace(nl_tekst, en_tekst)
        html = naar_submap(html, vertaling)
        # cms-data.js moet weten waar de JSON-bestanden staan
        html = html.replace('<html lang="en"', '<html lang="en" data-basis="../"', 1)
    # de taalknop pas hierna: die links wijzen bewust buiten de eigen map
    html = taalknop(html, taal, nl_bestand, en_bestand)
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
def bouw_case(c, blokken, sjabloon, taal, vertaling, inst):
    nl_naam = bestandsnaam(c, 'case-')
    en_naam = bestandsnaam(c, 'case-', 'en')
    naam = nl_naam if taal == 'nl' else en_naam
    klant = veld(c, 'naam', taal) or ''
    opdrachtgever = veld(c, 'klant', taal) or klant
    label = 'Klant' if taal == 'nl' else 'Client'

    if c.get('hero_video'):
        video = (
            '      <iframe src="https://player.vimeo.com/video/'
            + esc(c['hero_video'])
            + '?background=1&amp;autoplay=1&amp;muted=1&amp;loop=1&amp;autopause=0'
              '&amp;title=0&amp;byline=0&amp;portrait=0&amp;badge=0" '
              'allow="autoplay; fullscreen; picture-in-picture; encrypted-media" '
              'referrerpolicy="strict-origin-when-cross-origin" title="'
            + esc(klant) + '" loading="eager"></iframe>'
        )
    else:
        video = ''

    kenmerken = [f'      <dt>{label}</dt>\n      <dd>{regels(opdrachtgever)}</dd>']
    onderwerp = veld(c, 'onderwerp', taal)
    if onderwerp:
        kop = 'Onderwerp' if taal == 'nl' else 'Subject'
        kenmerken.append(f'\n      <dt>{kop}</dt>\n      <dd>{regels(onderwerp)}</dd>')
    if c.get('tags'):
        labels = '<br>'.join(esc(str(t).capitalize()) for t in c['tags'])
        kenmerken.append(f'\n      <dt>Tags</dt>\n      <dd class="tags">{labels}</dd>')

    disciplines = '\n'.join(
        f'        <div class="rij">\n          <h2>{esc(d.get("titel"))}</h2>\n'
        f'          <p>{esc(d.get("tekst"))}</p>\n        </div>'
        for d in veld(c, 'disciplines_detail', taal) or []
    )

    meta = veld(c, 'meta_omschrijving', taal)
    omschrijving = (esc(meta.strip()) if meta
                    else plat(veld(c, 'resultaat', taal) or veld(c, 'verhaal', taal)))
    html = vul(sjabloon, {
        'SLUG': esc(c.get('slug')),
        'KLEUR': esc(c.get('merkkleur') or '#ffff00'),
        'PAGINATITEL': esc(een_regel(klant)),
        'OMSCHRIJVING': omschrijving,
        'HERO_BEELD': esc(beeldpad(c.get('hero_beeld') or c.get('tegelbeeld'))),
        'HERO_ALT': esc(veld(c, 'hero_alt', taal) or veld(c, 'tegelbeeld_alt', taal) or f'Case {klant}'),
        'HERO_VIDEO': video,
        'KLANT': esc(een_regel(klant)),
        'HERO_TITEL': regels(veld(c, 'titel', taal)),
        'HERO_RESULTAAT': regels(veld(c, 'resultaat', taal)),
        'KENMERKEN': ''.join(kenmerken),
        'VERHAAL': esc(veld(c, 'verhaal', taal)),
        'DISCIPLINES': disciplines,
        'EIGEN_INHOUD': eigen_inhoud(pad_in_taal(naam, taal)),
        'OPENGRAPH': opengraph(esc(een_regel(klant)), omschrijving, c.get('hero_beeld') or c.get('tegelbeeld'),
                               naam, taal, inst),
    })
    return naam, afwerken(html, blokken, taal, nl_naam, en_naam, vertaling)


# ---------------------------------------------------------------- diensten
def case_blok(c, taal):
    """Uitgelichte case onderaan een dienstpagina — zelfde opmaak als elders."""
    doel = bestandsnaam(c, 'case-')
    open_tag = (f'    <a class="case-blok" href="{esc(doel)}"'
                + (f' data-video="{esc(c["hover_video"])}"' if c.get('hover_video') else '')
                + '>') if doel else '    <article class="case-blok">'
    sluit = '    </a>' if doel else '    </article>'
    klant = veld(c, 'naam', taal) or ''
    return (
        f'{open_tag}\n'
        f'      <img loading="lazy" decoding="async" src="{esc(beeldpad(c.get("tegelbeeld")))}" alt="{esc(veld(c, "tegelbeeld_alt", taal) or f"Case {klant}")}">\n'
        f'      <div class="case-inhoud">\n'
        f'        <span class="case-eyebrow">{esc(een_regel(klant))}</span>\n'
        f'        <h3 class="case-titel">{regels(veld(c, "titel", taal))}</h3>\n'
        f'        <p class="case-resultaat">\n'
        f'          <span class="pijl-knop"><svg class="pijl-svg" aria-hidden="true"><use href="#svg-pijl"></use></svg></span>\n'
        f'          <span>{regels(veld(c, "resultaat", taal))}</span>\n'
        f'        </p>\n'
        f'      </div>\n{sluit}'
    )


def bouw_dienst(d, groep, blokken, sjabloon, cases_op_slug, taal, vertaling, inst):
    nl_naam = bestandsnaam(d)
    en_naam = bestandsnaam(d, '', 'en')
    naam = nl_naam if taal == 'nl' else en_naam
    titel = veld(d, 'titel', taal) or ''
    kort = een_regel(titel)

    brede = veld(d, 'brede_foto', taal)
    if d.get('brede_foto'):
        brede = ('<!-- ============================================================ VOL BEELD -->\n'
                 f'<section class="beeld-vol" aria-label="{esc(kort)}">\n  <figure>\n'
                 f'    <img loading="lazy" decoding="async" src="{esc(beeldpad(d["brede_foto"]))}" '
                 f'alt="{esc(veld(d, "brede_foto_alt", taal) or kort)}">\n  </figure>\n</section>')
    else:
        brede = '<!-- geen brede foto ingesteld in het CMS -->'

    quote_tekst = veld(d, 'quote', taal)
    if quote_tekst:
        bronnaam = veld(d, 'quote_bron', taal)
        bron = f'\n    <cite>&ndash; {esc(bronnaam)} &ndash;</cite>' if bronnaam else ''
        tekst = esc(str(quote_tekst).strip().strip('“”"'))
        quote = ('<!-- ============================================================ QUOTE -->\n'
                 f'<section class="quote">\n  <blockquote>\n'
                 f'    <p>&ldquo;{tekst}&rdquo;</p>{bron}\n  </blockquote>\n</section>')
    else:
        quote = '<!-- geen quote ingesteld in het CMS -->'

    alineas = [a.strip() for a in re.split(r'\n\s*\n', str(veld(d, 'bloktekst', taal) or '')) if a.strip()]
    bloktekst = '\n'.join(f'      <p>{regels(a)}</p>' for a in alineas) or '      <p></p>'

    gekozen = [cases_op_slug[s] for s in (d.get('cases') or []) if s in cases_op_slug]
    cases_html = '\n'.join(case_blok(c, taal) for c in gekozen)

    groep_naam = (veld(groep, 'naam', taal) if groep else
                  ('Wat wij doen' if taal == 'nl' else 'What we do'))
    standaard_kop = (f'{kort} in actie: succesverhalen.' if taal == 'nl'
                     else f'{kort} in action: success stories.')
    standaard_cta = ('Wil je meer weten?\nNeem contact met ons op!' if taal == 'nl'
                     else 'Want to know more?\nGet in touch with us!')
    meta = veld(d, 'meta_omschrijving', taal)
    omschrijving_d = esc(meta.strip()) if meta else plat(veld(d, 'introtekst', taal))

    html = vul(sjabloon, {
        'SLUG': esc(d.get('slug')),
        'PAGINATITEL': esc(kort),
        'OMSCHRIJVING': omschrijving_d,
        'MENUTITEL': esc(kort),
        'GROEP_NAAM': esc(groep_naam),
        'WAT_WIJ_DOEN': 'Wat wij doen' if taal == 'nl' else 'What we do',
        'GROEP_URL': esc(groep.get('overzicht_url') if groep else 'index.html#diensten'),
        'HERO_BEELD': esc(beeldpad(d.get('headerbeeld'))),
        'HERO_ALT': esc(veld(d, 'headerbeeld_alt', taal) or kort),
        'HERO_TITEL': regels(titel),
        'INTROTITEL': esc(veld(d, 'introtitel', taal) or kort),
        'INTROTEKST': regels(veld(d, 'introtekst', taal)),
        'BREED_BEELD': brede,
        'QUOTE': quote,
        'BLOKTITEL': esc(veld(d, 'bloktitel', taal) or kort),
        'BLOKTEKST': bloktekst,
        'CTA_TEKST': regels(veld(d, 'cta_tekst', taal) or standaard_cta),
        'STAAND_BEELD': esc(beeldpad(d.get('staand_beeld'))),
        'STAAND_ALT': esc(veld(d, 'staand_beeld_alt', taal) or kort),
        'CASES_KOP': esc(veld(d, 'cases_kop', taal) or standaard_kop),
        'CASES': cases_html,
        'EIGEN_INHOUD': eigen_inhoud(pad_in_taal(naam, taal)),
        'OPENGRAPH': opengraph(esc(kort), omschrijving_d, d.get('headerbeeld'), naam, taal, inst),
    })
    return naam, afwerken(html, blokken, taal, nl_naam, en_naam, vertaling)


# -------------------------------------------------------------------- main
OG_START = '<!-- CAMPAGNE:DEELKAART-START -->'
OG_EINDE = '<!-- CAMPAGNE:DEELKAART-EINDE -->'


def og_handgemaakt(inst):
    """De handgemaakte pagina's (homepage, Over ons, Contact, overzichten) worden
    niet gegenereerd, maar hun deelkaart moet wel kloppen. Die zetten we hier bij
    elke run opnieuw, op basis van de titel en omschrijving die in de pagina zelf
    staan. Verandert het site-adres in het CMS, dan schuift het hier vanzelf mee."""
    bijgewerkt = []
    for bestand in sorted(os.listdir(WORTEL)):
        if not bestand.endswith('.html'):
            continue
        vol = os.path.join(WORTEL, bestand)
        with open(vol, encoding='utf-8') as f:
            html = f.read()
        if MARKERING in html[:2000]:
            continue                                  # gegenereerde pagina: doet het zelf al
        m_titel = re.search(r'<title>(.*?)</title>', html, re.S)
        m_oms = re.search(r'<meta name="description" content="([^"]*)"', html)
        if not m_titel:
            continue
        titel = m_titel.group(1).split('&mdash;')[0].strip() or 'Campagne'
        blok = OG_START + '\n' + opengraph(titel, m_oms.group(1) if m_oms else '',
                                           inst.get('deelbeeld'), bestand, 'nl', inst) + '\n' + OG_EINDE
        if OG_START in html:
            nieuw_html = re.sub(re.escape(OG_START) + r'.*?' + re.escape(OG_EINDE),
                                lambda m: blok, html, count=1, flags=re.S)
        else:
            m_icon = re.search(r'<link rel="icon"[^>]*>\n', html)
            if not m_icon:
                continue
            nieuw_html = html[:m_icon.end()] + blok + '\n' + html[m_icon.end():]
        if nieuw_html != html:
            with open(vol, 'w', encoding='utf-8') as f:
                f.write(nieuw_html)
            bijgewerkt.append(bestand)
    return bijgewerkt


# ------------------------------------------------- menu, homepage, overzichten
# Deze drie plekken staan als gewone HTML in de pagina's (nodig voor Google en
# voor bezoekers zonder JavaScript). Ze worden hier bij elke run opnieuw
# opgebouwd uit diensten.json, zodat een nieuw onderwerp in het CMS vanzelf
# overal verschijnt en er niets handmatig bijgezet hoeft te worden.

PIJL_DIK = ('<span class="mini-pijl"><svg class="pijl-svg" aria-hidden="true">'
            '<use href="#svg-pijl-dik"></use></svg></span>')
PIJL = ('<span class="pijl-knop"><svg class="pijl-svg" aria-hidden="true">'
        '<use href="#svg-pijl"></use></svg></span>')


def dienstpagina(d):
    """Bestandsnaam van een onderwerp, of leeg als het er geen eigen pagina heeft."""
    if not d.get('pagina_aanmaken'):
        return ''
    return bestandsnaam(d)


def zichtbare_onderwerpen(diensten, groep):
    return [d for d in diensten
            if str(d.get('groep', '')).lower() == groep['slug'] and d.get('actief') is not False]


def bouw_menulijsten(html, groepen, diensten):
    """De drie uitklaplijsten in het menu-overlay."""
    for groep in groepen:
        label = groep.get('menu_label') or groep.get('naam')
        m = re.search(r'aria-controls="([^"]+)">' + re.escape(label) + r'</button>', html)
        if not m:
            continue
        lijst_id = m.group(1)
        blok = re.search(r'(<div class="menu-sub-wrap" id="' + re.escape(lijst_id) +
                         r'">.*?<ul class="menu-sub-lijst">)(.*?)(</ul>)', html, re.S)
        if not blok:
            continue
        regels = ['            <li><a href="' + esc(groep.get('overzicht_url')) + '">' + PIJL_DIK
                  + esc(groep.get('naam')) + ' overzicht</a></li>']
        for d in zichtbare_onderwerpen(diensten, groep):
            doel = dienstpagina(d) or (groep.get('overzicht_url', '') + '#' + str(d.get('slug')))
            regels.append('            <li><a href="' + esc(doel) + '">' + PIJL_DIK
                          + esc(een_regel(d.get('titel'))) + '</a></li>')
        html = html[:blok.start(2)] + '\n' + '\n'.join(regels) + '\n            ' + html[blok.end(2):]
    return html


def bouw_homepage_diensten(html, groepen, diensten):
    """Het dienstenblok op de homepage: per groep de lijst met onderwerpen."""
    for groep in groepen:
        naam = re.escape(esc(groep.get('naam')))
        blok = re.search(r'(<h2 class="dienst-kop">(?:<a[^>]*>)?' + naam +
                         r' <svg.*?<div class="dienst-items">)(.*?)(</div>)', html, re.S)
        if not blok:
            continue
        regels = []
        for d in zichtbare_onderwerpen(diensten, groep):
            doel = dienstpagina(d) or (groep.get('overzicht_url', '') + '#' + str(d.get('slug')))
            regels.append('      <a class="dienst-item" href="' + esc(doel) + '">' + PIJL_DIK
                          + ' ' + esc(een_regel(d.get('titel'))) + '</a>')
        html = html[:blok.start(2)] + '\n' + '\n'.join(regels) + '\n    ' + html[blok.end(2):]
    return html


def inkorten(tekst, lengte=150):
    t = re.sub(r'\s+', ' ', str(tekst or '')).strip()
    return t if len(t) <= lengte else t[:lengte].rsplit(' ', 1)[0] + '...'


def bouw_overzichtstegels(html, groep, diensten):
    """De tegels op de overzichtspagina van een groep (Strategie/Branding/Activatie)."""
    blok = re.search(r'(  <div class="strat-grid">).*?(\n  </div>)', html, re.S)
    if not blok:
        return html

    def tegel(titel, tekst, href, extra=''):
        return ('      <a class="strat-tegel' + extra + '" href="' + esc(href) + '">\n'
                '        <h2>' + esc(titel) + '</h2>\n'
                '        <p class="tegel-tekst">' + esc(inkorten(tekst)) + '</p>\n'
                '        <span class="strat-knop">\n'
                '          <span class="label">Vertel me meer</span>\n'
                '          <span class="lijn" aria-hidden="true"></span>\n'
                '          ' + PIJL + '\n'
                '        </span>\n'
                '      </a>')

    onderwerpen = zichtbare_onderwerpen(diensten, groep)
    kolommen = [[], [], []]
    for i, d in enumerate(onderwerpen):
        kolommen[0 if i < 2 else (1 if i == 2 else 2)].append(d)

    stukken = []
    for nr, kolom in enumerate(kolommen, start=1):
        tegels = [tegel(een_regel(d.get('titel')), d.get('introtekst'),
                        dienstpagina(d) or (groep.get('overzicht_url', '') + '#' + str(d.get('slug'))))
                  for d in kolom]
        if nr == 3:
            tegels.append(tegel('Benieuwd wat ' + str(groep.get('naam', '')).lower()
                                + ' voor jouw merk doet?', groep.get('intro_tekst'),
                                'contact.html', ' uitgelicht'))
        stukken.append('    <!-- Kolom ' + str(nr) + ' -->\n    <div class="strat-kolom">\n'
                       + '\n'.join(tegels) + '\n    </div>')

    nieuw = '  <div class="strat-grid">\n\n' + '\n\n'.join(stukken) + '\n\n  </div>'
    return html[:blok.start()] + nieuw + html[blok.end():]


def sync_handgemaakt(blokken):
    """Header, menu, footer en sprite van de handgemaakte pagina's gelijktrekken
    met index.html. Gegenereerde pagina's doen dat al bij het aanmaken."""
    bijgewerkt = []
    for bestand in sorted(os.listdir(WORTEL)):
        if not bestand.endswith('.html') or bestand == 'index.html':
            continue
        vol = os.path.join(WORTEL, bestand)
        with open(vol, encoding='utf-8') as f:
            html = f.read()
        if MARKERING in html[:2000]:
            continue
        nieuw = sync_master(html, blokken)
        if nieuw != html:
            with open(vol, 'w', encoding='utf-8') as f:
                f.write(nieuw)
            bijgewerkt.append(bestand)
    return bijgewerkt


def main():
    controle = '--controle' in sys.argv
    cases = (lees_json('cases.json') or {}).get('cases', [])
    diensten_data = lees_json('diensten.json') or {}
    diensten = diensten_data.get('diensten', [])
    groepen = {g['slug']: g for g in diensten_data.get('groepen', [])}
    cases_op_slug = {c['slug']: c for c in cases if c.get('slug')}
    inst = lees_json('instellingen.json') or {}
    groepen_lijst = diensten_data.get('groepen', [])

    # Menu en homepage-dienstenblok in index.html (de master) opnieuw opbouwen
    # uit diensten.json, vóórdat de masterblokken worden overgenomen.
    index_html = lees('index.html')
    index_nieuw = bouw_menulijsten(index_html, groepen_lijst, diensten)
    index_nieuw = bouw_homepage_diensten(index_nieuw, groepen_lijst, diensten)
    if index_nieuw != index_html and not controle:
        with open(os.path.join(WORTEL, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(index_nieuw)

    blokken = masterblokken()

    def vertaaltabel():
        """Nederlandse bestandsnaam -> Engelse bestandsnaam, voor elke pagina die
        in beide talen bestaat. Links binnen /en/ worden hiermee omgezet."""
        tabel = {}
        for c in cases:
            if c.get('actief') is not False and c.get('pagina_aanmaken') is not False and c.get('slug'):
                nl, en = bestandsnaam(c, 'case-'), bestandsnaam(c, 'case-', 'en')
                if nl:
                    tabel[nl] = en
        for d in diensten:
            if d.get('actief') is not False and d.get('pagina_aanmaken') and d.get('slug'):
                nl, en = bestandsnaam(d), bestandsnaam(d, '', 'en')
                if nl:
                    tabel[nl] = en
        return tabel

    vertaling = vertaaltabel()
    gewenst, geschreven, ongewijzigd = {}, [], []

    sjabloon_case = lees('templates/case.html')
    sjabloon_dienst = lees('templates/dienst.html')

    for taal in TALEN:
        for c in cases:
            if c.get('actief') is False or c.get('pagina_aanmaken') is False or not c.get('slug'):
                continue
            naam, html = bouw_case(c, blokken, sjabloon_case, taal, vertaling, inst)
            if naam:
                gewenst[pad_in_taal(naam, taal)] = html
        for d in diensten:
            if d.get('actief') is False or not d.get('pagina_aanmaken') or not d.get('slug'):
                continue
            groep = groepen.get(str(d.get('groep', '')).lower())
            naam, html = bouw_dienst(d, groep, blokken, sjabloon_dienst,
                                     cases_op_slug, taal, vertaling, inst)
            if naam:
                gewenst[pad_in_taal(naam, taal)] = html

    os.makedirs(os.path.join(WORTEL, 'en'), exist_ok=True)
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
    for map_naam in ['', 'en']:
        map_pad = os.path.join(WORTEL, map_naam) if map_naam else WORTEL
        if not os.path.isdir(map_pad):
            continue
        for bestand in sorted(os.listdir(map_pad)):
            if not bestand.endswith('.html'):
                continue
            relatief = os.path.join(map_naam, bestand) if map_naam else bestand
            if relatief in gewenst:
                continue
            vol = os.path.join(map_pad, bestand)
            with open(vol, encoding='utf-8') as f:
                if MARKERING in f.read(2000):
                    if not controle:
                        os.remove(vol)
                    verwijderd.append(relatief)

    if not controle:
        # overzichtstegels per groep
        for groep in groepen_lijst:
            pagina = groep.get('overzicht_url')
            vol = os.path.join(WORTEL, str(pagina))
            if not pagina or not os.path.exists(vol):
                continue
            with open(vol, encoding='utf-8') as f:
                html = f.read()
            nieuw_html = bouw_overzichtstegels(html, groep, diensten)
            if nieuw_html != html:
                with open(vol, 'w', encoding='utf-8') as f:
                    f.write(nieuw_html)
        gelijkgetrokken = sync_handgemaakt(blokken)
    else:
        gelijkgetrokken = []

    deelkaarten = [] if controle else og_handgemaakt(inst)

    print(f"Gegenereerd : {len(geschreven)}  {geschreven if geschreven else ''}")
    if gelijkgetrokken:
        print(f"Gelijkgetrokken: {len(gelijkgetrokken)} handgemaakte pagina's (menu, header, footer)")
    if deelkaarten:
        print(f"Deelkaarten : {len(deelkaarten)} handgemaakte pagina's bijgewerkt")
    print(f"Ongewijzigd : {len(ongewijzigd)}")
    print(f"Verwijderd  : {len(verwijderd)}  {verwijderd if verwijderd else ''}")
    if controle and (geschreven or verwijderd):
        print("\n(controlestand: er is niets weggeschreven)")


if __name__ == '__main__':
    main()
