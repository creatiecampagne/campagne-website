# Campagne CMS-upgrade — online zetten

Dit pakket maakt `cases.json`, `logos.json` en `diensten.json` de centrale databronnen naast het bestaande `team.json`. De HTML blijft statisch hostbaar; Sveltia CMS schrijft wijzigingen als commits naar GitHub en de site leest de JSON-bestanden in de browser.

## 1. Eerst veilig in GitHub zetten

Werk bij voorkeur in een aparte branch zodat je de Deploy Preview kunt controleren voordat je `main` wijzigt.

```bash
git checkout -b cms-data-laag
```

Kopieer daarna de bestanden uit dit pakket over je bestaande project. Belangrijk:

- `admin/index.html` en `admin/config.yml` horen in de map `/admin/`.
- `cases.json`, `logos.json`, `diensten.json` en `cms-data.js` horen naast je bestaande HTML-bestanden in de site-root.
- De mappen `images/cases`, `images/logos` en `images/diensten` moeten bestaan; de meegeleverde `.gitkeep`-bestanden zorgen daarvoor.
- Bestaande beelden zijn bewust niet verplaatst. De startdata verwijst naar de huidige paden zoals `images/cases/tour.webp`.
- De losse `config.yml` in de pakket-root is alleen een handige kopie ter vergelijking. Voor Sveltia is `/admin/config.yml` de canonieke configuratie. Als jouw repository nu al `admin/config.yml` heeft, vervang die daarmee en hoef je de losse rootkopie niet te publiceren.

Commit en push vervolgens:

```bash
git add .
git commit -m "Add CMS-driven cases logos and services"
git push -u origin cms-data-laag
```

Maak op GitHub een Pull Request van `cms-data-laag` naar `main`.

## 2. Deploy Preview controleren

Als de repository al met Netlify gekoppeld is, laat de Pull Request eerst als Deploy Preview bouwen. Controleer daar minimaal:

1. Homepage: eerste 3 cases groot, volgende 6 klein.
2. Hovervideo's op desktop.
3. `/cases.html`: alle actieve cases en de filter op tags.
4. Logo-slider op homepage én about.
5. Menu: Strategie, Branding en Activatie tonen de onderwerpen uit `diensten.json`.
6. `/strategy.html`: overzicht wordt uit `diensten.json` gevuld.
7. `/merk-strategie.html`: hero, intro, beelden, quote, tekst en geselecteerde cases worden uit `diensten.json` gevuld.
8. `/case-tdff.html`: kleur, hero, klant, onderwerp, tags, verhaal en disciplines worden uit `cases.json` gevuld.
9. Mobiel: menu, filters en tegels nogmaals nalopen.

Pas na deze controle de PR samen naar `main`.

## 3. Netlify koppelen als dat nog niet gebeurd is

Maak in Netlify een nieuw project vanuit de bestaande GitHub-repository en kies `main` als production branch. Voor deze aangeleverde structuur is geen buildstap nodig zolang de HTML-bestanden in de repository-root staan. Gebruik in dat geval de repository-root als publish directory. Als je huidige Netlify-project al een andere, werkende publish directory gebruikt, laat die instelling staan.

Na het koppelen wordt een push/merge naar de productietak automatisch opnieuw gedeployed.

## 4. CMS-login activeren

Ga na deployment naar:

`https://jouwdomein.nl/admin/`

### Snelste route voor één beheerder

Sveltia CMS kan met een GitHub Personal Access Token inloggen. Dit vereist geen extra wijziging in `config.yml`. Gebruik dit vooral om de eerste test te doen.

### Nettere route voor meerdere redacteuren: GitHub OAuth via Netlify

Maak in GitHub een OAuth App aan. Gebruik als callback URL exact:

`https://api.netlify.com/auth/done`

Voeg daarna in Netlify bij de OAuth-instellingen de GitHub-provider toe met de Client ID en Client Secret van die OAuth App. Wanneer Netlify als OAuth-client wordt gebruikt, hoeft de Sveltia backend-config hiervoor niet te worden aangepast.

Iedere redacteur die via GitHub content moet kunnen opslaan heeft passende schrijftoegang tot de repository nodig.

## 5. Eerste CMS-test

Open `/admin/`. Je hoort onder **Website** vier onderdelen te zien:

- Teamleden
- Cases
- Logo-slider
- Diensten

Doe eerst een onschuldige wijziging, bijvoorbeeld één resultaatregel aanpassen, klik **Save** en controleer vervolgens:

- er verschijnt een commit in GitHub;
- Netlify start een deploy;
- de wijziging verschijnt live na de deploy.

Zet de tekst daarna eventueel weer terug via het CMS. Daarmee is de hele keten CMS → GitHub → deploy → live bewezen.

## 6. Zo beheer je cases

De volgorde in `cases.json` is de homepage-indeling:

- positie 1–3: grote homepagecases;
- positie 4–9: kleine homepagecases;
- positie 10 en verder: alleen cases-overzicht.

Alle actieve cases verschijnen op `cases.html`. Tags uit hetzelfde case-object worden als filtertags gerenderd. Cases zonder `detailpagina` krijgen geen nep-link naar `#`.

Voor een nieuwe detailcase:

1. maak de case in het CMS;
2. kopieer `case-tdff.html` naar bijvoorbeeld `case-mijn-project.html`;
3. verander op `<body>` alleen `data-case-slug="tour-de-france-femmes"` naar de nieuwe slug;
4. vul in het CMS bij **Detailpagina** exact die bestandsnaam in;
5. laat custom case-HTML onder het gemarkeerde `CUSTOM CASE CONTENT`-punt staan.

De bovenkant blijft dan CMS-gestuurd; de rest van de pagina blijft vrij maatwerk.

## 7. Zo beheer je diensten

`diensten.json` bevat zowel de drie groepen als de onderwerpen. Een onderwerp met `actief: false` verdwijnt uit de dynamisch gevulde lijsten.

Voor een nieuwe detaildienst:

1. maak/vul het onderwerp in het CMS;
2. kopieer `merk-strategie.html` naar bijvoorbeeld `marketing-strategie.html`;
3. verander op `<body>` alleen `data-dienst-slug="merk-strategie"` naar de nieuwe slug;
4. vul bij **Detailpagina** in het CMS de bestandsnaam in.

De geselecteerde cases onderaan een dienst worden in het CMS gekozen uit de cases in `cases.json`.

`branding.html` en `activatie.html` zijn al als overzichtsstubs toegevoegd. Ze gebruiken voorlopig dezelfde visuele hero-opzet als `strategy.html`; vul in het CMS eigen introcopy in en vervang later eventueel de hero-assets wanneer die beschikbaar zijn.

## 8. Media

Nieuwe uploads vanuit het CMS worden per onderdeel opgeborgen in:

- `/images/team`
- `/images/cases`
- `/images/logos`
- `/images/diensten`

Oude beelden hoeven niet direct te worden gemigreerd; de meegeleverde JSON verwijst nog naar de bestaande bestanden.

## 9. Belangrijk vóór definitief live

Controleer in een echte browser/deploy preview vooral de Vimeo-hoverstates, slider-loop, mobiele breakpoints en filterinteractie. De meegeleverde bestanden zijn statisch gecontroleerd op JSON/YAML-validiteit en JavaScript-syntax, maar een deploy preview is de laatste visuele integratietest met jouw echte hosting, assets en domein.
