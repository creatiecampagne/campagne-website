(function () {
  'use strict';

  function laadJSON(pad) {
    return fetch(pad, { cache: 'no-store' }).then(function (r) {
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
  // Beeldpad opschonen: de site draait in een submap (…/campagne-website/), dus een
  // pad met beginslash wijst naar de domeinroot en geeft een 404. Sveltia kan zo'n
  // pad wegschrijven als public_folder ooit weer absoluut wordt gezet; dit vangt dat af.
  function beeldpad(p, terugval) {
    var s = String(p == null ? '' : p).trim().replace(/^\/+/, '');
    return s || (terugval === undefined ? 'images/placeholder.webp' : terugval);
  }
  function svgPijl() { return '<span class="pijl-knop"><svg class="pijl-svg" aria-hidden="true"><use href="#svg-pijl"></use></svg></span>'; }
  // Zelfde regel als tools/genereer-paginas.py: een eigen bestandsnaam wint,
  // anders wordt hij afgeleid van de slug. Zo linken tegels altijd naar de
  // pagina die de generator daadwerkelijk aanmaakt.
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
      '<img loading="lazy" decoding="async" src="'+esc(beeldpad(c.tegelbeeld))+'" alt="Case '+esc(c.klantnaam)+'">'+
      '<div class="case-inhoud"><span class="case-eyebrow">'+esc(c.klantnaam)+'</span>'+
      '<'+heading+' class="case-titel">'+br(c.titel)+'</'+heading+'>'+
      '<p class="case-resultaat">'+svgPijl()+br(c.resultaatregel)+'</p></div>'+close;
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
    var title=c.overzicht_titel || c.klantnaam;
    var result=c.overzicht_resultaat || c.resultaatregel;
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

  function renderHomepageCases(data) {
    var cases=actieveCases(data);
    var groot=document.querySelector('section.cases#cases');
    if (groot) groot.innerHTML=cases.slice(0,3).map(function(c){return caseGroot(c,'h2');}).join('');
    var grid=document.querySelector('section.tegels .tegel-grid');
    if (grid && !document.body.classList.contains('cases-pagina')) grid.innerHTML=cases.slice(3,9).map(function(c){return caseTegel(c,false);}).join('');
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
      var html=menuLink(g.naam+' overzicht',g.overzicht_url);
      diensten.filter(function(d){return String(d.groep).toLowerCase()===g.slug;}).forEach(function(d){
        html+=menuLink(d.titel,d.detailpagina || g.overzicht_url+'#'+d.slug);
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
      return '<div class="dienst-groep"><h2 class="dienst-kop"><a href="'+esc(g.overzicht_url)+'">'+esc(g.naam)+'<svg class="icoon" aria-hidden="true"><use href="#icoon-'+icon+'"></use></svg></a></h2>'+
        '<div class="dienst-items">'+items.map(function(d){return '<a class="dienst-item" href="'+esc(d.detailpagina || g.overzicht_url+'#'+d.slug)+'"><span class="mini-pijl"><svg class="pijl-svg" aria-hidden="true"><use href="#svg-pijl-dik"></use></svg></span>'+esc(d.titel)+'</a>';}).join('')+'</div></div>';
    }).join('');
  }

  function renderGroepOverzicht(data) {
    var slug=document.body.getAttribute('data-diensten-groep'); if(!slug) return;
    var groep=(data.groepen||[]).find(function(g){return g.slug===slug;}); if(!groep) return;
    var diensten=actieveDiensten(data).filter(function(d){return String(d.groep).toLowerCase()===slug;});
    var h1=document.querySelector('.hero-titel'); if(h1) h1.textContent=groep.naam;
    var heroImg=document.querySelector('.hero-video img'); if(heroImg && groep.headerbeeld){heroImg.src=beeldpad(groep.headerbeeld);heroImg.alt=groep.naam;}
    document.title=groep.naam+' — Campagne';
    var crumbs=document.querySelectorAll('.hero-kruimels li:last-child span'); if(crumbs.length) crumbs[0].textContent=groep.naam;
    var intro=document.querySelector('.tekstblok.duo .kolommen');
    if(intro){
      var h=intro.querySelector('h2'),p=intro.querySelector('p');
      if(h) h.textContent=groep.intro_titel || groep.naam;
      if(p){ p.textContent=groep.intro_tekst || ''; p.hidden=!groep.intro_tekst; }
    }
    var grid=document.querySelector('.strategie-tegels .strat-grid');
    if(grid){
      var cols=[[],[],[]]; diensten.forEach(function(d,i){cols[i%3].push(d);});
      grid.innerHTML=cols.map(function(col){return '<div class="strat-kolom">'+col.map(function(d){
        return '<a class="strat-tegel" id="'+esc(d.slug)+'" href="'+esc(d.detailpagina || '#')+'"><h2>'+esc(d.titel)+'</h2><p class="tegel-tekst">'+esc(d.introtekst || '')+'</p><span class="strat-knop"><span class="label">Vertel me meer</span><span class="lijn" aria-hidden="true"></span>'+svgPijl()+'</span></a>';
      }).join('')+'</div>';}).join('');
    }
  }

  function renderDienstDetail(data, casesData) {
    var slug=document.body.getAttribute('data-dienst-slug'); if(!slug) return;
    var d=actieveDiensten(data).find(function(x){return x.slug===slug;}); if(!d) return;
    var h=document.querySelector('.hero-titel'); if(h) h.innerHTML=br(d.titel);
    document.title=d.titel+' — Campagne';
    var hero=document.querySelector('.hero-video img'); if(hero && d.headerbeeld){hero.src=beeldpad(d.headerbeeld);hero.alt=d.titel;}
    var intro=document.querySelector('.tekstblok.duo .kolommen'); if(intro){
      var ih=intro.querySelector('h2'),ip=intro.querySelector('p'); if(ih) ih.textContent=d.introtitel||d.titel; if(ip) ip.textContent=d.introtekst||'';
    }
    var wide=document.querySelector('.beeld-vol img'); if(wide && d.brede_foto){wide.src=beeldpad(d.brede_foto);wide.alt=d.titel;}
    var q=document.querySelector('.quote blockquote'); if(q){var qp=q.querySelector('p'),qc=q.querySelector('cite'); if(qp) qp.textContent=d.quote||''; if(qc) qc.textContent=d.quote_bron?('– '+d.quote_bron+' –'):''; q.closest('.quote').hidden=!d.quote;}
    var text=document.querySelector('.tekst-beeld .tekst'); if(text){
      var th=text.querySelector('h2'); if(th) th.textContent=d.bloktitel||d.titel;
      text.querySelectorAll(':scope > p').forEach(function(p){p.remove();});
      var cta=text.querySelector('.blok-cta');
      (d.bloktekst||'').split(/\n\s*\n/).filter(Boolean).forEach(function(p){var el=document.createElement('p');el.textContent=p;text.insertBefore(el,cta);});
    }
    var portrait=document.querySelector('.tekst-beeld figure img'); if(portrait && d.staand_beeld){portrait.src=beeldpad(d.staand_beeld);portrait.alt=d.titel;}
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
    document.title=(c.klantnaam || c.titel)+' — Campagne';
    var section=document.querySelector('.hero-scroll'); if(section) section.setAttribute('aria-label',c.klantnaam||c.titel);
    var img=document.querySelector('.hero-video img'); if(img && c.hero_beeld){img.src=beeldpad(c.hero_beeld);img.alt='Case '+(c.klantnaam||c.titel);}
    var frame=document.querySelector('.hero-video iframe'); if(frame && c.hero_video){frame.src='https://player.vimeo.com/video/'+encodeURIComponent(c.hero_video)+'?background=1&autoplay=1&muted=1&loop=1&autopause=0&title=0&byline=0&portrait=0&badge=0';frame.title=c.klantnaam||c.titel;}
    var h=document.querySelector('.hero-titel'); if(h) h.innerHTML=br(c.hero_titel||c.titel);
    var res=document.querySelector('.hero-resultaat span:last-child'); if(res) res.innerHTML=br(c.hero_resultaat||c.resultaatregel);
    var crumb=document.querySelector('.hero-kruimels li:last-child span'); if(crumb) crumb.textContent=c.klantnaam||c.titel;
    var dl=document.querySelector('.case-kenmerken'); if(dl){
      dl.innerHTML='<dt>Klant</dt><dd>'+esc(c.klantnaam)+'</dd><dt>Onderwerp</dt><dd>'+br(c.onderwerp)+'</dd><dt>Tags</dt><dd class="tags">'+(c.tags||[]).map(esc).join('<br>')+'</dd>';
    }
    var story=document.querySelector('.case-verhaal > p'); if(story) story.textContent=c.verhaal||'';
    var disc=document.querySelector('.case-disciplines'); if(disc) disc.innerHTML=(c.disciplines_detail||[]).map(function(x){return '<div class="rij"><h2>'+esc(x.titel)+'</h2><p>'+esc(x.tekst)+'</p></div>';}).join('');
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

  window.CampagneCMSReady=Promise.all([casesP,logosP,dienstenP]).then(function(all){
    var cases=all[0],logos=all[1],diensten=all[2];
    if(logos) renderLogos(logos);
    if(cases){renderHomepageCases(cases);renderCasesOverzicht(cases);renderCaseDetail(cases);}
    if(diensten){renderMenu(diensten);renderHomepageDiensten(diensten);renderGroepOverzicht(diensten);if(cases)renderDienstDetail(diensten,cases);}
    document.querySelectorAll('img').forEach(bindAfbeelding);
    initDynamicVideoHover(document);
    document.dispatchEvent(new CustomEvent('campagne:cms-ready'));
    return {cases:cases,logos:logos,diensten:diensten};
  });
})();
