/* ==========================================================================
   Hero-video soepel laten starten
   --------------------------------------------------------------------------
   De Vimeo-player heeft een seconde of twee nodig voordat er beeld is. Tot die
   tijd stond er een zwart kader, wat bij het wisselen van pagina opvalt.
   Nu blijft het stilstaande beeld staan en schuift de video eroverheen zodra
   hij daadwerkelijk speelt. Lukt dat onverhoopt niet, dan komt de video na een
   paar seconden alsnog in beeld — je ziet dus nooit een leeg kader.
   ========================================================================== */
(function () {
  'use strict';

  var wachtenden = [];

  // Eerst luisteren, dan pas opbouwen: mocht er in de opbouw iets misgaan, dan
  // blijft het bericht van de player alsnog binnenkomen.
  window.addEventListener('message', function (bericht) {
    if (bericht.origin !== 'https://player.vimeo.com') return;
    var data = bericht.data;
    if (typeof data === 'string') {
      try { data = JSON.parse(data); } catch (fout) { return; }
    }
    if (!data || !data.event) return;

    var bron = wachtenden.filter(function (w) { return w.frame.contentWindow === bericht.source; });
    var doelen = bron.length ? bron : wachtenden;

    if (data.event === 'ready') {
      doelen.forEach(function (w) { w.abonneer(); });
    } else if (data.event === 'play' || data.event === 'playing' || data.event === 'timeupdate') {
      doelen.forEach(function (w) { w.speelt(); });
    }
  });

  var houders = Array.prototype.slice.call(document.querySelectorAll('.hero-video'));
  if (!houders.length) return;

  houders.forEach(function (houder) {
    var frame = houder.querySelector('iframe');
    var poster = houder.querySelector('img');

    // Ontbreekt het posterbeeld, verberg het dan; een kapot-beeldicoon is
    // lelijker dan het donkere kader dat eronder zit.
    if (poster) {
      poster.addEventListener('error', function () { poster.style.display = 'none'; });
    }
    if (!frame) return;

    var afgerond = false;
    function speelt() {
      if (afgerond) return;
      afgerond = true;
      houder.classList.add('video-speelt');
    }

    function abonneer() {
      ['play', 'playing', 'timeupdate'].forEach(function (gebeurtenis) {
        try {
          frame.contentWindow.postMessage(
            JSON.stringify({ method: 'addEventListener', value: gebeurtenis }),
            'https://player.vimeo.com');
        } catch (fout) { /* player nog niet bereikbaar; het vangnet vangt dit op */ }
      });
    }

    wachtenden.push({ frame: frame, speelt: speelt, abonneer: abonneer });

    // Vangnet: nooit langer dan 3 seconden op de player wachten.
    frame.addEventListener('load', function () { abonneer(); setTimeout(speelt, 3000); });
    if (frame.contentWindow) abonneer();
    setTimeout(speelt, 6000);
  });

})();

/* ==========================================================================
   Volgende pagina alvast ophalen bij hover
   --------------------------------------------------------------------------
   Zodra de muis boven een interne link hangt (of een vinger hem aanraakt),
   haalt de browser die pagina vast op. Klik je daarna, dan staat de HTML er al
   en begint de hero-video meteen te laden in plaats van na de pagina-overgang.
   ========================================================================== */
(function () {
  'use strict';

  var gehaald = {};

  function haalOp(adres) {
    if (!adres || gehaald[adres]) return;
    gehaald[adres] = true;
    var link = document.createElement('link');
    link.rel = 'prefetch';
    link.href = adres;
    document.head.appendChild(link);
  }

  function bekijk(gebeurtenis) {
    var anker = gebeurtenis.target.closest ? gebeurtenis.target.closest('a[href]') : null;
    if (!anker) return;
    var adres = anker.getAttribute('href');
    if (!adres || adres.charAt(0) === '#' ||
        adres.indexOf('mailto:') === 0 || adres.indexOf('tel:') === 0) return;
    if (anker.hostname && anker.hostname !== window.location.hostname) return;
    if (adres.indexOf('.html') === -1) return;
    haalOp(anker.href);
  }

  // Alleen op apparaten met een muis: op mobiel kost vooruit ophalen data
  // zonder dat er een hover-moment is om het te verdienen.
  if (window.matchMedia('(hover: hover)').matches) {
    document.addEventListener('mouseover', bekijk, { passive: true });
  }
})();

(function () {
  'use strict';

  // Engelse pagina's staan in /en/, dus de JSON-bestanden liggen een map hoger.
  // De generator zet daarvoor data-basis="../" op het <html>-element.
  var BASIS = document.documentElement.getAttribute('data-basis') || '';
  var TAAL = (document.documentElement.lang || 'nl').toLowerCase().slice(0, 2);

  // Op pagina's zonder Engelse versie is de taalknop een button (geen link).
  // De keuze rendert dan wél alle CMS-teksten om (cases, tegels, menu) en
  // wordt onthouden voor de rest van het bezoek — zo 'springen' de cases om,
  // ook al is de pagina zelf (nog) niet vertaald.
  var TAALKNOPPEN = !!document.querySelector('.taalswitch button');
  try {
    var bewaardeTaal = sessionStorage.getItem('cmsTaal');
    if (TAALKNOPPEN && (bewaardeTaal === 'en' || bewaardeTaal === 'nl')) TAAL = bewaardeTaal;
  } catch (fout) { /* geen storage — geen probleem */ }

  // Waarde in de taal van deze pagina; een lege vertaling valt terug op het Nederlands.
  function v(item, naam) {
    if (!item) return '';
    if (TAAL !== 'nl') {
      var vert = item[TAAL] && item[TAAL][naam];
      if (vert !== undefined && vert !== null && vert !== '' &&
          !(Array.isArray(vert) && !vert.length)) return vert;
    }
    var waarde = item[naam];
    return waarde === undefined || waarde === null ? '' : waarde;
  }

  function laadJSON(pad) {
    return fetch(BASIS + pad, { cache: 'no-store' }).then(function (r) {
      if (!r.ok) throw new Error(pad + ' kon niet worden geladen (' + r.status + ')');
      return r.json();
    });
  }
  function esc(v) {
    return String(v == null ? '' : v).replace(/[&<>"']/g, function (c) {
      return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c];
    });
  }
  function br(v) { return esc(v).replace(/\n/g, '<br>'); }
  // Titels mogen een regelafbreking bevatten voor de hero; in het menu, de
  // paginatitel en alt-teksten wordt dat weer één doorlopende regel.
  function eenRegel(v) { return String(v == null ? '' : v).replace(/\s*\n\s*/g, ' ').trim(); }
  // Beeldpad opschonen: de site draait in een submap (…/campagne-website/), dus een
  // pad met beginslash wijst naar de domeinroot en geeft een 404. Sveltia kan zo'n
  // pad wegschrijven als public_folder ooit weer absoluut wordt gezet; dit vangt dat af.
  function beeldpad(p, terugval) {
    var s = String(p == null ? '' : p).trim().replace(/^\/+/, '');
    return BASIS + (s || (terugval === undefined ? 'images/placeholder.webp' : terugval));
  }
  function svgPijl() { return '<span class="pijl-knop"><svg class="pijl-svg" aria-hidden="true"><use href="#svg-pijl"></use></svg></span>'; }
  // Zelfde regel als tools/genereer-paginas.py: een eigen bestandsnaam wint,
  // anders wordt hij afgeleid van de slug. Zo linken tegels altijd naar de
  // pagina die de generator daadwerkelijk aanmaakt.
  // Link naar een onderwerp: eigen bestandsnaam, anders afgeleid van de slug —
  // exact zoals tools/genereer-paginas.py het doet. Zonder eigen pagina wijzen
  // we naar het anker op de overzichtspagina van de groep.
  function dienstLink(d, g) {
    var eigen = String((d && d.detailpagina) || '').trim();
    if (eigen) return eigen.slice(-5) === '.html' ? eigen : eigen + '.html';
    if (d && d.pagina_aanmaken && d.slug) return d.slug + '.html';
    return (g && g.overzicht_url ? g.overzicht_url : '') + '#' + (d && d.slug ? d.slug : '');
  }

  function geldigLink(c) {
    if (!c || c.pagina_aanmaken === false) return '';
    var eigen = String(c.detailpagina || '').trim();
    if (eigen) return eigen.slice(-5) === '.html' ? eigen : eigen + '.html';
    var slug = String(c.slug || '').trim();
    return slug ? 'case-' + slug + '.html' : '';
  }
  function actieveCases(data) { return (data.cases || []).filter(function (c) { return c.actief !== false; }); }
  function actieveDiensten(data) { return (data.diensten || []).filter(function (d) { return d.actief !== false; }); }

  function bindAfbeelding(img) {
    if (!img) return;
    img.addEventListener('error', function () {
      var ouder = img.closest('.case-blok, .tegel, .hero-video, figure');
      if (ouder) ouder.classList.add('beeld-mist');
    });
  }

  function renderLogos(data) {
    document.querySelectorAll('#logo-strip').forEach(function (strip) {
      var items=(data.logos || []).map(function (l) {
        var h=l.hoogte ? ' style="height:'+Number(l.hoogte)+'px"' : '';
        return '<img loading="lazy" decoding="async" src="'+esc(beeldpad(l.beeld))+'"'+h+' alt="Logo '+esc(l.naam)+'">';
      }).join('');
      // Tweemaal renderen: de bestaande slider verwacht twee identieke helften.
      strip.innerHTML=items+items;
      strip.querySelectorAll('img').forEach(bindAfbeelding);
    });
    window.dispatchEvent(new Event('resize'));
  }

  function caseGroot(c, heading) {
    var link=geldigLink(c);
    var video=c.hover_video ? ' data-video="'+esc(c.hover_video)+'"' : '';
    var open=link ? '<a class="case-blok" href="'+esc(link)+'"'+video+'>' : '<article class="case-blok"'+video+'>';
    var close=link ? '</a>' : '</article>';
    return open+
      '<img loading="lazy" decoding="async" src="'+esc(beeldpad(c.tegelbeeld))+'" alt="'+esc(v(c,'tegelbeeld_alt')||('Case '+eenRegel(v(c,'naam'))))+'">'+
      '<div class="case-inhoud"><span class="case-eyebrow">'+esc(eenRegel(v(c,'naam')))+'</span>'+
      '<'+heading+' class="case-titel">'+br(v(c,'titel'))+'</'+heading+'>'+
      '<p class="case-resultaat">'+svgPijl()+br(v(c,'resultaat'))+'</p></div>'+close;
  }

  function tagsHtml(c, knoppen) {
    return (c.tags || []).map(function (tag) {
      var val=String(tag).toLowerCase();
      return knoppen ? '<button class="tag" type="button" data-tag="'+esc(val)+'">'+esc(tag)+'</button>' : '<span>'+esc(tag)+'</span>';
    }).join('');
  }

  function caseTegel(c, overzicht) {
    var link=geldigLink(c);
    var video=c.hover_video ? ' data-video="'+esc(c.hover_video)+'"' : '';
    var disc=(c.disciplines || []).join(' ');
    var title=eenRegel(v(c,'naam'));
    var result=v(c,'resultaat');
    var attrs=' class="tegel" style="--hover-kleur:'+esc(c.merkkleur || '#d72655')+'"'+video;
    if (overzicht) attrs+=' data-disciplines="'+esc(disc)+'"';
    if (!overzicht) attrs=' class="tegel"'+(link ? ' href="'+esc(link)+'"' : '')+' style="--hover-kleur:'+esc(c.merkkleur || '#d72655')+'"'+video;
    var tagWrap=overzicht ? tagsHtml(c,true) : tagsHtml(c,false);
    var inner='<img loading="lazy" decoding="async" src="'+esc(beeldpad(c.tegelbeeld))+'" alt="Case '+esc(title)+'">'+
      '<div class="tegel-inhoud"><p class="tegel-titel">'+esc(title)+'</p><div class="tegel-onder">'+
      '<p class="tegel-labels">'+tagWrap+'</p><p class="tegel-sub"><span class="onderschrift">'+esc(result)+'</span>'+svgPijl()+'</p></div></div>';
    if (overzicht) {
      inner += link ? '<a class="tegel-link" href="'+esc(link)+'" aria-label="Bekijk case '+esc(title)+'"></a>' : '';
      return '<article'+attrs+'>'+inner+'</article>';
    }
    return link ? '<a'+attrs+'>'+inner+'</a>' : '<article'+attrs+'>'+inner+'</article>';
  }

  // Welke case op welke homepage-plek staat: de plekken uit homepage.json
  // (menu 'Homepage-indeling' in Sveltia). Lege of ongeldige plekken worden
  // aangevuld in de volgorde van de caseslijst, zodat er nooit gaten vallen.
  // Zelfde logica als homepage_selectie in tools/genereer-paginas.py.
  function homepageSelectie(data, hp) {
    var alle=actieveCases(data);
    var perSlug={}; alle.forEach(function(c){ if(c.slug) perSlug[c.slug]=c; });
    var gekozen=[];
    function kies(plek){
      var slug=hp ? String(hp[plek]||'').trim() : '';
      var c=perSlug[slug];
      if (c && gekozen.indexOf(slug)===-1) { gekozen.push(slug); return c; }
      return null;
    }
    var groot=['groot_1','groot_2','groot_3'].map(kies);
    var klein=['klein_1','klein_2','klein_3','klein_4','klein_5','klein_6'].map(kies);
    var rest=alle.filter(function(c){ return gekozen.indexOf(c.slug)===-1; });
    function vulAan(c){ return c || rest.shift() || null; }
    return { groot: groot.map(vulAan).filter(Boolean), klein: klein.map(vulAan).filter(Boolean) };
  }

  function renderHomepageCases(data, hp) {
    var keuze=homepageSelectie(data, hp);
    var groot=document.querySelector('section.cases#cases');
    if (groot) groot.innerHTML=keuze.groot.map(function(c){return caseGroot(c,'h2');}).join('');
    var grid=document.querySelector('section.tegels .tegel-grid');
    if (grid && !document.body.classList.contains('cases-pagina')) grid.innerHTML=keuze.klein.map(function(c){return caseTegel(c,false);}).join('');
  }

  function renderCasesOverzicht(data) {
    var grid=document.querySelector('.cases-overzicht .tegel-grid');
    if (!grid) return;
    var cta=grid.querySelector('.tegel-cta');
    var ctaHtml=cta ? cta.outerHTML : '';
    grid.innerHTML=actieveCases(data).map(function(c){return caseTegel(c,true);}).join('') + ctaHtml;
  }

  function menuLink(label, url) {
    return '<li><a href="'+esc(url || '#')+'"><span class="mini-pijl"><svg class="pijl-svg" aria-hidden="true"><use href="#svg-pijl-dik"></use></svg></span>'+esc(label)+'</a></li>';
  }
  function renderMenu(data) {
    var diensten=actieveDiensten(data);
    var groups=data.groepen || [];
    var mapping={strategie:'menu-sub-strategy',branding:'menu-sub-branding',activatie:'menu-sub-activation'};
    groups.filter(function(g){return g.actief!==false;}).forEach(function(g){
      var wrap=document.getElementById(mapping[g.slug]); if(!wrap) return;
      var ul=wrap.querySelector('.menu-sub-lijst'); if(!ul) return;
      var html=menuLink(eenRegel(v(g,'naam'))+(TAAL==='nl'?' overzicht':' overview'),g.overzicht_url);
      diensten.filter(function(d){return String(d.groep).toLowerCase()===g.slug;}).forEach(function(d){
        html+=menuLink(eenRegel(v(d,'titel')),dienstLink(d,g));
      });
      ul.innerHTML=html;
    });
  }

  function renderHomepageDiensten(data) {
    var root=document.querySelector('section.diensten#diensten'); if(!root) return;
    var diensten=actieveDiensten(data), groups=(data.groepen||[]).filter(function(g){return g.actief!==false;});
    root.innerHTML=groups.map(function(g){
      var items=diensten.filter(function(d){return String(d.groep).toLowerCase()===g.slug;});
      var icon=g.slug==='strategie'?'strategie':(g.slug==='branding'?'branding':'activatie');
      // Elk icoon heeft zijn eigen maatklasse; zonder die klasse valt de SVG
      // terug op het standaardformaat en staat hij veel te groot in de kop.
      var maat=g.slug==='strategie'?'icoon-s':(g.slug==='branding'?'icoon-b':'icoon-a');
      return '<div class="dienst-groep"><h2 class="dienst-kop"><a href="'+esc(g.overzicht_url)+'">'+esc(eenRegel(v(g,'naam')))+' <svg class="icoon '+maat+'" aria-hidden="true"><use href="#icoon-'+icon+'"></use></svg></a></h2>'+
        '<div class="dienst-items">'+items.map(function(d){return '<a class="dienst-item" href="'+esc(dienstLink(d,g))+'"><span class="mini-pijl"><svg class="pijl-svg" aria-hidden="true"><use href="#svg-pijl-dik"></use></svg></span>'+esc(eenRegel(v(d,'titel')))+'</a>';}).join('')+'</div></div>';
    }).join('');
  }

  function renderGroepOverzicht(data) {
    var slug=document.body.getAttribute('data-diensten-groep'); if(!slug) return;
    var groep=(data.groepen||[]).find(function(g){return g.slug===slug;}); if(!groep) return;
    var diensten=actieveDiensten(data).filter(function(d){return String(d.groep).toLowerCase()===slug;});
    var h1=document.querySelector('.hero-titel'); if(h1) h1.textContent=eenRegel(v(groep,'naam'));
    var heroImg=document.querySelector('.hero-video img'); if(heroImg && groep.headerbeeld){heroImg.src=beeldpad(groep.headerbeeld);heroImg.alt=v(groep,'headerbeeld_alt')||eenRegel(v(groep,'naam'));}
    document.title=eenRegel(v(groep,'naam'))+' — Campagne';
    var crumbs=document.querySelectorAll('.hero-kruimels li:last-child span'); if(crumbs.length) crumbs[0].textContent=eenRegel(v(groep,'naam'));
    var intro=document.querySelector('.tekstblok.duo .kolommen');
    if(intro){
      var h=intro.querySelector('h2'),p=intro.querySelector('p');
      if(h) h.textContent=v(groep,'intro_titel')||eenRegel(v(groep,'naam'));
      if(p){ var it=v(groep,'intro_tekst'); p.textContent=it; p.hidden=!it; }
    }
    var grid=document.querySelector('.strategie-tegels .strat-grid');
    if(grid){
      var cols=[[],[],[]]; diensten.forEach(function(d,i){cols[i%3].push(d);});
      grid.innerHTML=cols.map(function(col){return '<div class="strat-kolom">'+col.map(function(d){
        return '<a class="strat-tegel" id="'+esc(d.slug)+'" href="'+esc(dienstLink(d,groep))+'"><h2>'+esc(eenRegel(v(d,'titel')))+'</h2><p class="tegel-tekst">'+esc(v(d,'introtekst'))+'</p><span class="strat-knop"><span class="label">'+(TAAL==='nl'?'Vertel me meer':'Tell me more')+'</span><span class="lijn" aria-hidden="true"></span>'+svgPijl()+'</span></a>';
      }).join('')+'</div>';}).join('');
    }
  }

  function renderDienstDetail(data, casesData) {
    var slug=document.body.getAttribute('data-dienst-slug'); if(!slug) return;
    var d=actieveDiensten(data).find(function(x){return x.slug===slug;}); if(!d) return;
    var h=document.querySelector('.hero-titel'); if(h) h.innerHTML=br(v(d,'titel'));
    document.title=eenRegel(v(d,'titel'))+' — Campagne';
    var hero=document.querySelector('.hero-video img'); if(hero && d.headerbeeld){hero.src=beeldpad(d.headerbeeld);hero.alt=v(d,'headerbeeld_alt')||eenRegel(v(d,'titel'));}
    var intro=document.querySelector('.tekstblok.duo .kolommen'); if(intro){
      var ih=intro.querySelector('h2'),ip=intro.querySelector('p'); if(ih) ih.textContent=v(d,'introtitel')||eenRegel(v(d,'titel')); if(ip) ip.textContent=v(d,'introtekst');
    }
    var wide=document.querySelector('.beeld-vol img'); if(wide && d.brede_foto){wide.src=beeldpad(d.brede_foto);wide.alt=v(d,'brede_foto_alt')||eenRegel(v(d,'titel'));}
    var q=document.querySelector('.quote blockquote'); if(q){var qp=q.querySelector('p'),qc=q.querySelector('cite'); var qt=v(d,'quote'), qb=v(d,'quote_bron'); if(qp) qp.textContent=qt; if(qc) qc.textContent=qb?('– '+qb+' –'):''; q.closest('.quote').hidden=!qt;}
    var text=document.querySelector('.tekst-beeld .tekst'); if(text){
      var th=text.querySelector('h2'); if(th) th.textContent=v(d,'bloktitel')||eenRegel(v(d,'titel'));
      text.querySelectorAll(':scope > p').forEach(function(p){p.remove();});
      var cta=text.querySelector('.blok-cta');
      String(v(d,'bloktekst')).split(/\n\s*\n/).filter(Boolean).forEach(function(p){var el=document.createElement('p');el.textContent=p;text.insertBefore(el,cta);});
    }
    var portrait=document.querySelector('.tekst-beeld figure img'); if(portrait && d.staand_beeld){portrait.src=beeldpad(d.staand_beeld);portrait.alt=v(d,'staand_beeld_alt')||eenRegel(v(d,'titel'));}
    var grid=document.querySelector('.uitgelichte-cases .case-grid');
    if(grid && casesData){
      var bySlug={}; actieveCases(casesData).forEach(function(c){bySlug[c.slug]=c;});
      grid.innerHTML=(d.cases||[]).map(function(sl){return bySlug[sl];}).filter(Boolean).map(function(c){return caseGroot(c,'h3');}).join('');
    }
  }

  function renderCaseDetail(data) {
    var slug=document.body.getAttribute('data-case-slug'); if(!slug) return;
    var c=actieveCases(data).find(function(x){return x.slug===slug;}); if(!c) return;
    document.documentElement.style.setProperty('--case-kleur', c.merkkleur || '#ffff00');
    document.body.style.backgroundColor=c.merkkleur || '#ffff00';
    document.title=eenRegel(v(c,'naam')||v(c,'titel'))+' — Campagne';
    var section=document.querySelector('.hero-scroll'); if(section) section.setAttribute('aria-label',eenRegel(v(c,'naam')||v(c,'titel')));
    var img=document.querySelector('.hero-video img'); if(img && c.hero_beeld){img.src=beeldpad(c.hero_beeld);img.alt=v(c,'hero_alt')||v(c,'tegelbeeld_alt')||('Case '+eenRegel(v(c,'naam')));}
    var frame=document.querySelector('.hero-video iframe'); if(frame && c.hero_video){frame.src='https://player.vimeo.com/video/'+encodeURIComponent(c.hero_video)+'?background=1&autoplay=1&muted=1&loop=1&autopause=0&title=0&byline=0&portrait=0&badge=0';frame.title=eenRegel(v(c,'naam')||v(c,'titel'));}
    var h=document.querySelector('.hero-titel'); if(h) h.innerHTML=br(v(c,'titel'));
    var res=document.querySelector('.hero-resultaat span:last-child'); if(res) res.innerHTML=br(v(c,'resultaat'));
    var crumb=document.querySelector('.hero-kruimels li:last-child span'); if(crumb) crumb.textContent=eenRegel(v(c,'naam')||v(c,'titel'));
    var dl=document.querySelector('.case-kenmerken'); if(dl){
      dl.innerHTML='<dt>'+(TAAL==='nl'?'Klant':'Client')+'</dt><dd>'+esc(v(c,'klant')||v(c,'naam'))+'</dd>'+
        '<dt>'+(TAAL==='nl'?'Onderwerp':'Subject')+'</dt><dd>'+br(v(c,'onderwerp'))+'</dd>'+
        '<dt>Tags</dt><dd class="tags">'+(c.tags||[]).map(esc).join('<br>')+'</dd>';
    }
    var story=document.querySelector('.case-verhaal > p'); if(story) story.textContent=v(c,'verhaal');
    var disc=document.querySelector('.case-disciplines'); if(disc) disc.innerHTML=(v(c,'disciplines_detail')||[]).map(function(x){return '<div class="rij"><h2>'+esc(x.titel)+'</h2><p>'+esc(x.tekst)+'</p></div>';}).join('');
  }

  function initDynamicVideoHover(scope) {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches || !window.matchMedia('(hover: hover)').matches) return;
    (scope||document).querySelectorAll('[data-video]').forEach(function(blok){
      if(blok.dataset.cmsVideoReady==='1') return; blok.dataset.cmsVideoReady='1';
      var id=blok.getAttribute('data-video'); if(!id) return;
      var layer,frame,timer;
      function ensure(){ if(layer) return; layer=document.createElement('div'); layer.className='blok-video'; frame=document.createElement('iframe'); frame.src='https://player.vimeo.com/video/'+encodeURIComponent(id)+'?background=1&autoplay=1&muted=1&loop=1&autopause=0&title=0&byline=0&portrait=0&badge=0'; frame.setAttribute('allow','autoplay; fullscreen; picture-in-picture; encrypted-media'); frame.setAttribute('referrerpolicy','strict-origin-when-cross-origin'); frame.setAttribute('aria-hidden','true'); frame.tabIndex=-1; layer.appendChild(frame); blok.appendChild(layer); }
      function command(m){ if(!frame) return; try{frame.contentWindow.postMessage(JSON.stringify({method:m}),'https://player.vimeo.com');}catch(e){} }
      function play(){clearTimeout(timer);ensure();requestAnimationFrame(function(){layer.classList.add('zichtbaar');command('play');});}
      function stop(){if(!layer)return;layer.classList.remove('zichtbaar');timer=setTimeout(function(){command('pause');},550);}
      var triggers=blok.classList.contains('tegel')?[blok]:Array.prototype.slice.call(blok.querySelectorAll('.case-titel,.case-resultaat'));
      if(!triggers.length) triggers=[blok]; triggers.forEach(function(t){t.addEventListener('mouseenter',play);}); blok.addEventListener('mouseleave',stop);
      var delay=900 + Array.prototype.indexOf.call((scope||document).querySelectorAll('[data-video]'), blok) * 250;
      if(document.readyState==='complete') setTimeout(ensure,delay);
      else window.addEventListener('load',function(){setTimeout(ensure,delay);},{once:true});
    });
  }

  var casesP=laadJSON('cases.json').catch(function(e){console.warn(e);return null;});
  var logosP=laadJSON('logos.json').catch(function(e){console.warn(e);return null;});
  var dienstenP=laadJSON('diensten.json').catch(function(e){console.warn(e);return null;});
  var homepageP=laadJSON('homepage.json').catch(function(e){console.warn(e);return null;});

  // Taalknop-UI gelijkzetten met de (eventueel onthouden) taal
  function syncTaalknop() {
    document.querySelectorAll('.taalswitch').forEach(function(ts){
      ts.setAttribute('data-taal', TAAL);
      ts.querySelectorAll('button').forEach(function(b){ b.classList.toggle('actief', b.dataset.kies===TAAL); });
    });
  }

  window.CampagneCMSReady=Promise.all([casesP,logosP,dienstenP,homepageP]).then(function(all){
    var cases=all[0],logos=all[1],diensten=all[2],homepage=all[3];

    function renderAlles(){
      if(cases){renderHomepageCases(cases,homepage);renderCasesOverzicht(cases);renderCaseDetail(cases);}
      if(diensten){renderMenu(diensten);renderHomepageDiensten(diensten);renderGroepOverzicht(diensten);if(cases)renderDienstDetail(diensten,cases);}
      document.querySelectorAll('img').forEach(bindAfbeelding);
      initDynamicVideoHover(document);
    }

    if(logos) renderLogos(logos);
    renderAlles();
    if (TAALKNOPPEN) {
      syncTaalknop();
      // Klik op EN/NL: alle CMS-teksten in die taal opnieuw renderen
      document.querySelectorAll('.taalswitch button').forEach(function(b){
        b.addEventListener('click', function(){
          if (b.dataset.kies===TAAL) return;
          TAAL=b.dataset.kies;
          try { sessionStorage.setItem('cmsTaal', TAAL); } catch (fout) { /* geen storage */ }
          renderAlles();
        });
      });
    }
    document.dispatchEvent(new CustomEvent('campagne:cms-ready'));
    return {cases:cases,logos:logos,diensten:diensten,homepage:homepage};
  });
})();
