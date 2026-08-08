# Campagne website — uploaden en beheren

## Deel 1 — Eenmalig online zetten

### 1. Bestanden in de repo zetten

Pak de zip uit en kopieer de inhoud over je lokale kopie van `campagne-website`.
Let op deze mappen, die zijn nieuw:

- `templates/` — de twee mallen waaruit pagina's worden gemaakt
- `tools/` — het generatorscript
- `.github/workflows/` — de automatisering (verborgen map, zorg dat je die meeneemt)

Verwijder daarna het oude `team.html` als dat er nog staat; die heet nu `about.html`.

```bash
git checkout -b cms-koppeling
git add -A
git commit -m "CMS-koppeling en paginagenerator"
git push -u origin cms-koppeling
```

Maak op GitHub een pull request en merge die naar `main`. Werk je liever zonder
branch, dan kan het ook direct op `main` — de branch is alleen een vangnet.

### 2. Twee instellingen controleren op GitHub

Ga naar je repo → **Settings**:

1. **Actions → General → Workflow permissions**: zet dit op *Read and write
   permissions*. Zonder dit mag de generator geen pagina's terugzetten.
2. **Pages**: bron moet *Deploy from a branch* zijn, branch `main`, map `/ (root)`.

### 3. Eerste keer laten draaien

Ga naar het tabblad **Actions** → *Pagina's genereren* → **Run workflow**.
Na ongeveer een minuut zie je een nieuwe commit met de gegenereerde pagina's.
Controleer daarna de site: alle casetegels moeten doorklikken.

### 4. Inloggen op het CMS

Sveltia gebruikt je GitHub-account, dus je hebt geen apart wachtwoord.

1. Ga naar `https://creatiecampagne.github.io/campagne-website/admin/`
2. Klik op **Sign in with GitHub** en geef toestemming.

Werkt het inloggen niet, dan ontbreekt de authenticatiebrug. Sveltia kan die
overslaan met een persoonlijke toegangssleutel: klik op de kleine link
*Sign in with Personal Access Token* op het inlogscherm en plak een token dat je
aanmaakt via GitHub → Settings → Developer settings → Personal access tokens →
Fine-grained tokens, met leesrechten en schrijfrechten op alleen deze repo.
Dat is de snelste route voor één beheerder. Wil je later dat collega's zonder
GitHub-kennis kunnen inloggen, dan zetten we er een OAuth-koppeling voor op.

## Deel 2 — Zo controleer je of het werkt

Log in op `/admin/` en doe deze proef:

1. Open **Logoslider**, versleep een logo naar boven en klik **Save**.
2. Kijk in je repo bij *Commits* — daar staat nu een commit van jouw GitHub-account.
3. Ververs de homepage na ongeveer een minuut: de slidervolgorde is gewijzigd.

Werkt dat, dan staat de hele keten goed: CMS → commit → live.

## Deel 3 — Dagelijks gebruik

### Nieuwe case toevoegen

Open **Cases** → *Add* onderaan de lijst en vul minimaal in:

- **Slug** — kleine letters met streepjes, bijvoorbeeld `air-so-pure`. Dit wordt
  de bestandsnaam (`case-air-so-pure.html`), dus wijzig hem niet meer na livegang.
- **Naam**, **Merkkleur**, **Tegelbeeld** en **Tags**
- **Detailpagina automatisch aanmaken** staat standaard aan

Klik **Save**. Binnen een minuut staat de tegel op de site én bestaat de
detailpagina met alle ingevulde informatie. Je hoeft zelf geen bestand aan te maken.

### Homepage indelen

De volgorde in de caseslijst is de indeling: de bovenste 3 worden de grote
blokken, de 6 daaronder de kleine tegels, de rest staat alleen op de
cases-pagina. Verslepen is dus herindelen.

### Een casepagina uitbreiden met eigen HTML

Onderin elke gegenereerde pagina staat dit blok:

```html
<!-- CAMPAGNE:EIGEN-INHOUD-START -->
<!-- CAMPAGNE:EIGEN-INHOUD-EINDE -->
```

Alles wat je daartussen zet blijft van jou. De generator raakt het nooit aan,
ook niet als je later de teksten in het CMS aanpast. Verwijder de twee
markerregels niet — dan raakt je eigen werk bij de volgende bewerking wel kwijt.

### Onderwerpen onder Strategie, Branding en Activatie

Open **Wat wij doen** → *Onderwerpen*. Zet **Tonen op de site** uit en het
onderwerp verdwijnt tegelijk uit het menu, de homepage en de overzichtspagina.
Zet **Eigen detailpagina aanmaken** aan als het onderwerp een eigen pagina
verdient; dan wordt `<slug>.html` automatisch gemaakt uit de ingevulde velden.
Nu staat dat alleen aan voor Merk strategie.

### Beelden

Upload ze gewoon via het CMS; die komen automatisch in de goede map
(`images/cases`, `images/logos`, `images/diensten`, `images/team`).

Belangrijk: paden moeten **relatief** blijven (`images/...`, nooit `/images/...`),
omdat de site in een submap draait. De configuratie staat goed ingesteld, dus
zolang je via het CMS uploadt gaat dit vanzelf goed.

## Deel 4 — Wat nog openstaat

- De beelden `tour-hero.webp`, de Blinqx-beelden en de teamfoto's ontbreken nog;
  daar staat nu een placeholder. Exporteer ze uit Figma en upload ze via het CMS.
- In `images/` staan de casebeelden en logo's dubbel: los in de map en in
  `images/cases` / `images/logos`. Na een geslaagde deploy kunnen de losse
  versies weg (`amin.webp` moet blijven, die is nog in gebruik).
- De menu-items *Social content*, *Banners & media* en *Vacatures* hebben nog
  geen pagina.

## Handmatig genereren op je eigen computer

Niet nodig, maar handig om vooraf te kijken:

```bash
python3 tools/genereer-paginas.py --controle   # meldt alleen wat er zou veranderen
python3 tools/genereer-paginas.py              # schrijft de pagina's echt weg
python3 -m http.server 8080                    # bekijk daarna http://localhost:8080/
```
