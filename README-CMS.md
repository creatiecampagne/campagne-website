# Campagne CMS-upgrade

Deze map is opgebouwd uit de aangeleverde HTML-bestanden en voegt een centrale JSON-laag toe.

## Nieuwe bestanden
- `cases.json` — bron voor homepage-cases, cases-overzicht, filter en case-detail boven de vouw.
- `logos.json` — bron voor beide logo-sliders.
- `diensten.json` — bron voor menu-sublijsten, homepage-diensten, groepsoverzichten en dienst-detail.
- `cms-data.js` — gedeelde renderer.
- `admin/index.html` + `admin/config.yml` — Sveltia CMS.
- `branding.html` en `activatie.html` — groepsoverzichten op basis van de strategy-master.

## Volgorde cases
De arrayvolgorde in `cases.json` is de homepage-indeling:
1. items 1–3 = grote homepage-cases;
2. items 4–9 = kleine homepage-tegels;
3. item 10+ = alleen op het cases-overzicht.

In Sveltia CMS kun je de lijst verslepen.

## Detailpagina cases
Een case linkt alleen door als `detailpagina` gevuld is. `case-tdff.html` gebruikt `data-case-slug="tour-de-france-femmes"` en vult hero + case-info uit `cases.json`. Alles onder het case-info blok kan custom HTML blijven.

Voor een nieuwe case-detailpagina:
1. kopieer `case-tdff.html`;
2. geef het bestand een nieuwe naam;
3. wijzig alleen `data-case-slug` op `<body>`;
4. vul hetzelfde bestandsnaam in bij `detailpagina` in het CMS.

## Detailpagina diensten
`merk-strategie.html` gebruikt `data-dienst-slug="merk-strategie"`. Nieuwe detailpagina: kopieer dit bestand en wijzig alleen die slug + vul het nieuwe bestandsnaam in bij `detailpagina`.

## Test lokaal
Omdat `fetch()` bij `file://` meestal wordt geblokkeerd, test via een lokale webserver vanuit de repo-root, bijvoorbeeld:

```bash
python3 -m http.server 8080
```

Open daarna `http://localhost:8080/`.
## Ontbrekende beelden later invullen

Optionele beelden die nog niet in deze ZIP zaten zijn bewust leeg gelaten in de JSON-data. De HTML gebruikt tijdelijk `images/placeholder.webp`, zodat er geen 404 ontstaat. Upload/vervang ze via Sveltia CMS:

- Cases → `images/cases/`
- Logo-slider → `images/logos/`
- Diensten/overzichtsheaders → `images/diensten/`
- Teamleden → `images/team/`

Na opslaan schrijft Sveltia het gekozen bestandspad in het juiste JSON-bestand en verdwijnt de placeholder automatisch op de live site.

