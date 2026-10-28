/* Miraj Events — site behaviour. No dependencies. */
(function(){
  'use strict';
  var reduce=window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  function $(s,c){ return (c||document).querySelector(s); }
  function $$(s,c){ return Array.prototype.slice.call((c||document).querySelectorAll(s)); }
  /* first visible, real form field in a scope (never the honeypot) */
  function firstField(scope){ return scope?($$('input:not([type=hidden]):not([name=bot-field]),select,textarea',scope).filter(function(x){ return !x.closest('[hidden]')&&!x.closest('.hp'); })[0]||null):null; }
  function gt(){ if(typeof window.gtag==='function'){ window.gtag.apply(null,arguments); } }
  var store={
    get:function(k,ss){ try{ return JSON.parse((ss?sessionStorage:localStorage).getItem(k)||'null'); }catch(e){ return null; } },
    set:function(k,v,ss){ try{ (ss?sessionStorage:localStorage).setItem(k,JSON.stringify(v)); }catch(e){} }
  };

  /* ---------- attribution: first touch (90 days) + latest ad click ---------- */
  var AI=/(chatgpt\.com|chat\.openai\.com|openai\.com|perplexity\.ai|gemini\.google\.com|bard\.google\.com|copilot\.microsoft\.com|bing\.com\/chat|claude\.ai|you\.com|phind\.com|poe\.com|meta\.ai|deepseek\.com|grok\.com)/i;
  (function(){
    var q=new URLSearchParams(location.search), now=Date.now();
    var keys=['gclid','gbraid','wbraid','oppref','utm_source','utm_medium','utm_campaign','utm_term','utm_content'];
    var hit={}; keys.forEach(function(k){ var v=q.get(k); if(v){ hit[k]=v.slice(0,200); } });
    var ref=document.referrer||''; var external=ref && ref.indexOf(location.hostname)<0;
    var us=(q.get('utm_source')||'').toLowerCase(); var aiUtm=/chatgpt|openai|perplexity|gemini|copilot|claude|anthropic/.test(us)?us:(q.get('oppref')?'chatgpt-ads':'');
    var first=store.get('miraj_ft');
    if(!first || now-first.t>90*864e5){
      first={t:now,landing_page:location.pathname+location.search,first_referrer:external?ref.slice(0,300):'',ai_referrer:(external&&AI.test(ref))?ref.split('/')[2]:aiUtm};
      store.set('miraj_ft',first);
    }
    if(Object.keys(hit).length){ hit.t=now; hit.lp=location.pathname; store.set('miraj_click',hit); }
    if(aiUtm && !(external && AI.test(ref))){ var b=store.get('miraj_ft')||{}; if(!b.ai_referrer){ b.ai_referrer=aiUtm; store.set('miraj_ft',b); } gt('event','ai_referral',{ai_source:aiUtm}); }
    if(external && AI.test(ref)){ var a=store.get('miraj_ft')||{}; if(!a.ai_referrer){ a.ai_referrer=ref.split('/')[2]; store.set('miraj_ft',a); } gt('event','ai_referral',{ai_source:ref.split('/')[2]}); }
  })();
  /* What each inquiry email shows (Tariq, Oct 28): one readable "Source" line instead of 13 tracking lines,
     the exact click id kept for a future offline-conversion upload, the landing page and the page the form was on.
     Built from the same stored first touch (miraj_ft) + latest ad/UTM click (miraj_click), 90-day window as before. */
  var AIRX=/chatgpt|openai|perplexity|gemini|bard|copilot|claude|anthropic/i;
  function aiName(s){ s=String(s||'').toLowerCase(); if(/chatgpt|openai/.test(s)){ return 'ChatGPT'; } if(/perplexity/.test(s)){ return 'Perplexity'; } if(/gemini|bard/.test(s)){ return 'Gemini'; } if(/copilot|bing/.test(s)){ return 'Copilot'; } if(/claude|anthropic/.test(s)){ return 'Claude'; } return s.replace(/^www\./,''); }
  function refName(r){
    r=String(r||''); if(!r){ return ''; }
    if(r.indexOf('android-app://com.google.android.googlequicksearchbox')===0){ return 'Google app (organic)'; }
    if(r.indexOf('android-app://com.google.android.gm')===0){ return 'Gmail app'; }
    var h=r.split('/')[2]||r; h=h.toLowerCase().replace(/^www\./,'');
    if(/(^|\.)google\.[a-z.]+$/.test(h)){ return 'Google search (organic)'; }
    if(/(^|\.)bing\.com$/.test(h)){ return 'Bing search (organic)'; }
    if(/(^|\.)duckduckgo\.com$/.test(h)){ return 'DuckDuckGo search (organic)'; }
    if(/(^|\.)yahoo\.com$/.test(h)){ return 'Yahoo search (organic)'; }
    if(/(^|\.)instagram\.com$/.test(h)){ return 'Instagram'; }
    if(/(^|\.)facebook\.com$/.test(h)||h==='fb.me'){ return 'Facebook'; }
    return h;
  }
  var TRACK=/^(gclid|gbraid|wbraid|oppref|utm_[a-z]+|fbclid|msclkid|ttclid|igshid|_gl)$/i;
  function cleanPath(p){ p=String(p||''); var i=p.indexOf('?'); if(i<0){ return p.slice(0,300); } var q=new URLSearchParams(p.slice(i+1)), drop=[];
    q.forEach(function(v,n){ if(TRACK.test(n)){ drop.push(n); } }); drop.forEach(function(n){ q.delete(n); }); var s=q.toString(); return (p.slice(0,i)+(s?'?'+s:'')).slice(0,300); }
  function attribution(){
    var ft=store.get('miraj_ft')||{}, ck=store.get('miraj_click')||{};
    if(ck.t && Date.now()-ck.t>90*864e5){ ck={}; }
    var ids=[]; ['gclid','gbraid','wbraid','oppref'].forEach(function(k){ if(ck[k]){ ids.push(k+':'+ck[k]); } });
    var tag=ck.utm_content||ck.utm_campaign||'', us=ck.utm_source||'', um=ck.utm_medium||'', src;
    if(ck.gclid||ck.gbraid||ck.wbraid){ src='Google Ads'+(tag?' · '+tag:''); }
    else if(ck.oppref){ src='ChatGPT ad'+(tag?' · '+tag:''); }
    else if(us){
      if(AIRX.test(us)){ src=aiName(us); }
      else if(/^google$/i.test(us)&&/^(cpc|ppc|paid)/i.test(um)){ src='Google Ads (no click id)'+(tag?' · '+tag:''); }
      else if(/^google$/i.test(us)&&/organic/i.test(um)&&/gbp/i.test(ck.utm_campaign||'')){ src='Google Business Profile'; }
      else { src=us+(um?' / '+um:'')+(ck.utm_campaign?' ('+ck.utm_campaign+')':''); }
    }
    else if(ft.ai_referrer){ src=aiName(ft.ai_referrer); }
    else { src=refName(ft.first_referrer)||'Direct'; }
    return {source:src.slice(0,150),click_id:ids.join(' ').slice(0,400),landing_page:cleanPath(ck.lp||ft.landing_page||''),form_page:location.pathname};
  }

  /* ---------- header: mobile menu + active link ---------- */
  var menuBtn=$('#menuBtn'), mobnav=$('#mobnav');
  if(menuBtn&&mobnav){
    var setMenu=function(open){ mobnav.hidden=!open; menuBtn.setAttribute('aria-expanded',String(open)); document.documentElement.classList.toggle('menu-open',open); };
    menuBtn.addEventListener('click',function(){ setMenu(mobnav.hidden); });
    document.addEventListener('keydown',function(e){ if(e.key==='Escape'&&!mobnav.hidden){ setMenu(false); menuBtn.focus(); } });
    $$('a',mobnav).forEach(function(a){ a.addEventListener('click',function(){ setMenu(false); }); });
  }
  var view=document.body.getAttribute('data-view');
  $$('[data-nav]').forEach(function(a){ var on=a.getAttribute('data-nav')===view; a.classList.toggle('active',on); if(on){ a.setAttribute('aria-current','page'); } });

  /* ---------- sticky CTA: step aside while a form or the footer is on screen ---------- */
  var cta=$('.sticky-cta');
  if(cta&&'IntersectionObserver' in window){
    var seen=[];
    var io=new IntersectionObserver(function(es){ es.forEach(function(e){ var i=seen.indexOf(e.target); if(e.isIntersecting&&i<0){ seen.push(e.target); } else if(!e.isIntersecting&&i>-1){ seen.splice(i,1); } }); document.documentElement.classList.toggle('cta-off',seen.length>0); },{threshold:0});
    $$('#inquire,#contact-form,footer').forEach(function(el){ io.observe(el); });
  }

  /* ---------- click tracking: phone / WhatsApp / email ---------- */
  document.addEventListener('click',function(e){
    var a=e.target.closest && e.target.closest('a[href]'); if(!a){ return; }
    var h=a.getAttribute('href');
    if(h.indexOf('tel:')===0){ gt('event','phone_click',{link_url:h,page_path:location.pathname}); }
    else if(h.indexOf('wa.me')>-1){ gt('event','whatsapp_click',{link_url:h,page_path:location.pathname}); }
    else if(h.indexOf('mailto:')===0){ gt('event','email_click',{link_url:h,page_path:location.pathname}); }
    else if(h.indexOf('sms:')===0){ gt('event','text_click',{link_url:h,page_path:location.pathname}); }
  });

  /* ---------- "No date yet": fills the date field so the inquiry still records it ---------- */
  $$('[data-nodate]').forEach(function(cb){
    var f=cb.closest('.field'), inp=f&&$('input[name="event_date"]',f); if(!inp){ return; }
    cb.addEventListener('change',function(){
      if(cb.checked){ inp.setAttribute('data-prev',inp.value==='No date yet'?'':inp.value); inp.value='No date yet'; inp.readOnly=true; }
      else { inp.value=inp.getAttribute('data-prev')||''; inp.readOnly=false; inp.focus(); }
    });
  });

  /* ---------- reveal on scroll + count-up ---------- */
  function countUp(el){
    if(el.dataset.done||reduce){ return; } el.dataset.done='1';
    var end=parseInt(el.dataset.count,10), suf=el.dataset.suffix||'', t0=null;
    function step(ts){ if(!t0){t0=ts;} var p=Math.min(1,(ts-t0)/1200), e=1-Math.pow(1-p,3); el.textContent=Math.round(end*e)+suf; if(p<1){ requestAnimationFrame(step);} }
    requestAnimationFrame(step);
  }
  if('IntersectionObserver' in window && !reduce){
    var io=new IntersectionObserver(function(entries){
      entries.forEach(function(en){ if(en.isIntersecting){ en.target.classList.remove('pre'); var n=en.target.querySelector('[data-count]'); if(n){ countUp(n); } io.unobserve(en.target); } });
    },{rootMargin:'0px 0px -8% 0px',threshold:0.1});
    var vh=window.innerHeight||800;
    $$('.reveal').forEach(function(el){ if(el.getBoundingClientRect().top>vh){ el.classList.add('pre'); } io.observe(el); });
  }

  /* ---------- weekend chips (home) ---------- */
  (function(){
    var wrap=$('.weekend'); if(!wrap){ return; }
    var box=$('.chips',wrap), chips=$$('.chip',wrap), lists=$$('.wk',wrap), i=0;
    function show(w){ chips.forEach(function(x){ x.setAttribute('aria-pressed',String(x.getAttribute('data-w')===w)); }); lists.forEach(function(l){ l.hidden=(l.getAttribute('data-w')!==w); }); }
    chips.forEach(function(c,idx){ c.addEventListener('click',function(){ box.classList.remove('auto'); i=idx; show(c.getAttribute('data-w')); }); });
    box.addEventListener('animationend',function(e){ if(e.animationName!=='chipfill'||!box.classList.contains('auto')){ return; } i=(i+1)%chips.length; show(chips[i].getAttribute('data-w')); });
    wrap.addEventListener('mouseenter',function(){ box.classList.add('paused'); });
    wrap.addEventListener('mouseleave',function(){ box.classList.remove('paused'); });
    wrap.addEventListener('focusin',function(){ box.classList.add('paused'); });
    wrap.addEventListener('focusout',function(){ box.classList.remove('paused'); });
    /* Accessibility (Oct 25): no auto-advance (WCAG 2.2.2); traditions change only when a chip is pressed */
  })();

  /* ---------- Google reviews carousel ---------- */
  $$('.rv').forEach(function(rv){
    var slides=$$('.rv-slide',rv), dots=$$('.rv-dot',rv), cur=0, timer=null, paused=false, n=slides.length;
    slides.forEach(function(s){
      var t=$('.rv-text',s), b=$('.rv-more',s);
      function check(){ if(!s.classList.contains('open')){ b.hidden=t.scrollHeight<=t.clientHeight+2; } }
      b.addEventListener('click',function(){ var open=!s.classList.contains('open'); s.classList.toggle('open',open); b.textContent=open?'Show less':'Read more'; b.setAttribute('aria-expanded',String(open)); paused=open; if(open){ stop(); } else { start(); } });
      s._check=check;
    });
    function go(i){
      cur=(i+n)%n;
      slides.forEach(function(s,k){ var on=k===cur; s.classList.toggle('is-active',on); s.setAttribute('aria-hidden',String(!on)); if(!on&&s.classList.contains('open')){ s.classList.remove('open'); var b=$('.rv-more',s); b.textContent='Read more'; b.setAttribute('aria-expanded','false'); } });
      dots.forEach(function(d,k){ if(k===cur){ d.setAttribute('aria-current','true'); } else { d.removeAttribute('aria-current'); } });
      slides[cur]._check();
    }
    function stop(){ if(timer){ clearInterval(timer); timer=null; } }
    function start(){ stop(); /* Accessibility (Oct 25): no auto-advance (WCAG 2.2.2); reviews move only on arrows, dots or swipe */ }
    var status=$('.rv-status',rv);
    function announce(){ if(status){ var w=$('.rv-id strong',slides[cur]); status.textContent='Review '+(cur+1)+' of '+n+(w?', '+w.textContent:''); } }
    $('.rv-prev',rv).addEventListener('click',function(){ go(cur-1); announce(); start(); });
    $('.rv-next',rv).addEventListener('click',function(){ go(cur+1); announce(); start(); });
    dots.forEach(function(d,k){ d.addEventListener('click',function(){ go(k); announce(); start(); }); });
    rv.addEventListener('mouseenter',function(){ stop(); });
    rv.addEventListener('mouseleave',function(){ if(!paused){ start(); } });
    rv.addEventListener('focusin',function(){ stop(); });
    rv.addEventListener('focusout',function(e){ if(!rv.contains(e.relatedTarget)&&!paused){ start(); } });
    var x0=null;
    rv.addEventListener('touchstart',function(e){ x0=e.touches[0].clientX; },{passive:true});
    rv.addEventListener('touchend',function(e){ if(x0===null){ return; } var dx=e.changedTouches[0].clientX-x0; if(Math.abs(dx)>40){ go(cur+(dx<0?1:-1)); announce(); start(); } x0=null; },{passive:true});
    window.addEventListener('resize',function(){ slides[cur]._check(); });
    go(0);
    if('IntersectionObserver' in window){ var o=new IntersectionObserver(function(en){ en.forEach(function(e){ if(e.isIntersecting){ start(); } else { stop(); } }); }); o.observe(rv); } else { start(); }
  });

  /* ---------- package modal (contact) ---------- */
  (function(){
    var modal=$('#pk-modal'); if(!modal){ return; }
    var tiers=$$('.tiers .tier[data-pk]'), details=$$('.pkd',modal), current=null, lastTier=null;
    var names={'day-of':'Day-of Coordination','design':'Design + Coordination','planning':'Planning + Design','full':'Full Planning'};
    function close(){ modal.hidden=true; document.body.style.overflow=''; current=null; if(lastTier){ lastTier.focus({preventScroll:true}); } }
    modal.removeAttribute('aria-labelledby');
    modal.addEventListener('keydown',function(e){ if(e.key!=='Tab'){ return; } var f=$$('a[href],button:not([disabled]),input:not([type=hidden]),select,textarea,[tabindex]:not([tabindex="-1"])',modal).filter(function(x){ return x.offsetParent!==null; }); if(!f.length){ return; } var a=f[0], z=f[f.length-1]; if(e.shiftKey&&document.activeElement===a){ e.preventDefault(); z.focus(); } else if(!e.shiftKey&&document.activeElement===z){ e.preventDefault(); a.focus(); } });
    function open(pk,btn){ current=pk; lastTier=btn||null; modal.setAttribute('aria-label',names[pk]+' package details'); modal.hidden=false; document.body.style.overflow='hidden'; details.forEach(function(d){ d.hidden=(d.getAttribute('data-pk')!==pk); }); var x=$('.modal-x',modal); if(x){ x.focus({preventScroll:true}); } gt('event','view_package',{package:names[pk]}); }
    tiers.forEach(function(t){ t.addEventListener('click',function(){ open(t.getAttribute('data-pk'),t); }); });
    $$('[data-close]',modal).forEach(function(b){ b.addEventListener('click',close); });
    modal.addEventListener('click',function(e){ if(e.target===modal){ close(); } });
    document.addEventListener('keydown',function(e){ if(e.key==='Escape'&&!modal.hidden){ close(); } });
    $('[data-choose]',modal).addEventListener('click',function(){
      var sel=$('#c-pkg'); if(sel&&current){ sel.value=names[current]; }
      close(); var form=$('#contactForm');
      if(form){ form.scrollIntoView({behavior:reduce?'auto':'smooth',block:'start'}); var f=firstField($$('.fstep',form).filter(function(s){ return !s.hidden; })[0]||form); if(f){ setTimeout(function(){ f.focus({preventScroll:true}); },450); } }
    });
  })();

  /* ---------- wedding events fieldset only for weddings ---------- */
  (function(){ var ct=$('#c-type'), wf=$('#wedding-events'); if(!ct||!wf){ return; } function t(){ wf.hidden=!/wedding/i.test(ct.value); } ct.addEventListener('change',t); t(); })();

  /* ---------- forms → Netlify Forms ---------- */
  var VALUES={'Day-of Coordination':1975,'Design + Coordination':4750,'Planning + Design':6500,'Full Planning':9500,'Add-ons only (photobooth, candy pop-up, rentals)':500};
  function leadValue(fd){
    var p=fd.get('package')||''; if(VALUES[p]){ return VALUES[p]; }
    var b=fd.get('budget')||''; if(/10,000\+/.test(b)){ return 9500; } if(/5,000/.test(b)&&/10,000/.test(b)){ return 6500; } if(/2,500–\$5,000/.test(b)){ return 4750; }
    return 1975;
  }
  function fill(form){ var a=attribution(); Object.keys(a).forEach(function(k){ var el=form.querySelector('input[type=hidden][name="'+k+'"]'); if(el){ el.value=a[k]; } }); }
  function encode(fd){ var p=[]; fd.forEach(function(v,k){ p.push(encodeURIComponent(k)+'='+encodeURIComponent(v)); }); return p.join('&'); }
  function post(fd){ return fetch('/',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:encode(fd)}); }
  /* fire-and-forget POST that survives the page closing (used for the step-1 "Unfinished" save) */
  function beacon(fd){
    var body=encode(fd);
    try{ if(navigator.sendBeacon&&navigator.sendBeacon('/',new Blob([body],{type:'application/x-www-form-urlencoded'}))){ return; } }catch(e){}
    try{ fetch('/',{method:'POST',keepalive:true,headers:{'Content-Type':'application/x-www-form-urlencoded'},body:body}).catch(function(){}); }catch(e){}
  }
  /* subject line of the Netlify notification email, so the inbox shows who, what and when at a glance */
  function subj(label,parts){ return (label+': '+parts.map(function(x){ return String(x||'').trim(); }).filter(Boolean).join(' · ')).slice(0,150); }
  function normPhone(p){ var d=(p||'').replace(/\D/g,''); if(d.length===10){ return '+1'+d; } if(d.length===11&&d[0]==='1'){ return '+'+d; } return d?('+'+d):''; }
  var MSG={name:'Please enter your name.',email:'Please enter your email address.',phone:'Please enter your phone number.',event_date:'Please enter a date or season, or tick \u201cNo date yet\u201d.'};
  function errMsg(el){ var v=el.validity; if(v.valueMissing&&MSG[el.name]){ return MSG[el.name]; } if(v.valueMissing){ return el.tagName==='SELECT'?'Please choose an option.':(el.type==='checkbox'?'Please check this box.':(el.type==='email'?'Please enter your email address.':(el.type==='tel'?'Please enter your phone number.':'Please fill in this field.'))); } if(el.type==='email'&&v.typeMismatch){ return 'Please enter a valid email address, like name@example.com.'; } return el.validationMessage||'Please check this field.'; }
  function setErr(el,msg){ var id=(el.id||el.name)+'-err', e=document.getElementById(id), d=(el.getAttribute('aria-describedby')||'').split(' ').filter(function(x){ return x&&x!==id; });
    if(msg){ if(!e){ e=document.createElement('span'); e.id=id; e.className='field-err'; (el.closest('.field')||el.parentNode).appendChild(e); } e.textContent=msg; el.setAttribute('aria-invalid','true'); d.push(id); el.setAttribute('aria-describedby',d.join(' ')); }
    else { if(e){ e.parentNode.removeChild(e); } el.removeAttribute('aria-invalid'); if(d.length){ el.setAttribute('aria-describedby',d.join(' ')); } else { el.removeAttribute('aria-describedby'); } } }
  function clearErr(e){ var el=e.target; if(el&&el.getAttribute&&el.getAttribute('aria-invalid')==='true'&&el.checkValidity()){ setErr(el,''); } }
  function validate(scope){ var first=null; $$('input,select,textarea',scope).forEach(function(el){ if(el.type==='hidden'||el.name==='bot-field'||el.closest('[hidden]')){ return; } if(!el.checkValidity()){ setErr(el,errMsg(el)); if(!first){ first=el; } } else if(el.getAttribute('aria-invalid')==='true'){ setErr(el,''); } }); if(first){ first.focus(); } return !first; }
  function busy(form,on){ form.dataset.busy=on?'1':''; $$('button[type=submit]',form).forEach(function(b){ b.setAttribute('aria-disabled',String(on)); if(on){ b.dataset.label=b.textContent; b.textContent='Sending…'; } else if(b.dataset.label){ b.textContent=b.dataset.label; } }); }
  function fail(form){ busy(form,false); var m=$('.form-error',form); if(!m){ m=document.createElement('p'); m.className='form-error small'; m.setAttribute('role','alert'); form.appendChild(m); } m.innerHTML='Something went wrong sending your inquiry. Please call or text <a href="tel:+15865040207">(586) 504-0207</a> or email <a href="mailto:admin@mirajevent.com">admin@mirajevent.com</a>.'; }

  $$('form.js-inquiry').forEach(function(form){
    var steps=$$('.fstep',form), meta=$('[data-stepmeta]',form)||$('.form-meta span',form);
    if(form.dataset.package){ var sel=$('select[name=package]',form); if(sel){ sel.value=form.dataset.package; } }
    form.setAttribute('data-step','1');
    form.addEventListener('input',clearErr); form.addEventListener('change',clearErr);
    function showStep(n){ form.setAttribute('data-step',String(n)); steps.forEach(function(s){ s.hidden=(s.getAttribute('data-fstep')!==String(n)); }); var m=$('[data-fstep="'+n+'"] .form-meta span',form); if(meta&&!m){ meta.textContent='Step '+n+' of 2'; } }
    /* Step-1 save ("Unfinished inquiry"), Tariq Oct 28: sent only if the visitor does NOT finish — when the tab is
       hidden or closed, or 15 minutes after Continue — and at most once, built from step 1 as it is at that moment.
       A finished inquiry therefore sends one email. (Rare: someone who switches apps mid-form and then finishes
       sends both.) Never sent while the final submit is in flight or after it succeeded. */
    var started=false, sentPartial=false, finishing=false, finished=false, partialTimer=null;
    function sendPartial(){
      if(!started||sentPartial||finishing||finished||!form.dataset.start){ return; }
      sentPartial=true; if(partialTimer){ clearTimeout(partialTimer); partialTimer=null; }
      var s1=steps[0], fd=new FormData(); fd.append('form-name',form.dataset.start);
      ['name','email','phone','celebration','event_date'].forEach(function(k){ var el=$('[name="'+k+'"]',s1); if(el&&String(el.value||'').trim()){ fd.append(k,el.value); } });
      var a=attribution(); Object.keys(a).forEach(function(k){ if(a[k]){ fd.append(k,a[k]); } });
      var hp=$('[name="bot-field"]',form); if(hp&&hp.value){ fd.append('bot-field',hp.value); } /* lets Netlify's honeypot flag bot partials too */
      fd.append('subject',subj('Unfinished inquiry – please follow up',[fd.get('name')||fd.get('phone')||fd.get('email'),fd.get('celebration'),fd.get('event_date')]));
      beacon(fd);
    }
    if(form.dataset.start){
      document.addEventListener('visibilitychange',function(){ if(document.visibilityState==='hidden'){ sendPartial(); } });
      window.addEventListener('pagehide',sendPartial);
    }
    var next=$('[data-next]',form);
    if(next){
      next.addEventListener('click',function(){
        var s1=steps[0]; if(!validate(s1)){ return; }
        if(!started){ started=true;
          if(form.dataset.start){ partialTimer=setTimeout(sendPartial,15*60*1000); }
          /* not "form_start": GA4 enhanced measurement already sends that name on first touch (the Squarespace baseline) */
          gt('event','inquiry_step1',{form_name:'inquiry',page_path:location.pathname}); }
        showStep(2);
        form.scrollIntoView({behavior:reduce?'auto':'smooth',block:'start'});
        var first=firstField($('[data-fstep="2"]',form)); if(first){ setTimeout(function(){ first.focus({preventScroll:true}); },350); }
      });
    }
    var back=$('[data-back]',form); if(back){ back.addEventListener('click',function(e){ e.preventDefault(); showStep(1); form.scrollIntoView({behavior:reduce?'auto':'smooth',block:'start'}); var f=firstField($('[data-fstep="1"]',form)); if(f){ setTimeout(function(){ f.focus({preventScroll:true}); },300); } }); }
    form.addEventListener('submit',function(e){
      e.preventDefault(); if(form.dataset.busy==='1'){ return; }
      if(steps.length && steps[steps.length-1].hidden){ if(next){ next.click(); } return; }
      if(!validate(form)){ return; }
      fill(form);
      var fd=new FormData(form);
      var ev=fd.getAll('events[]'); fd.delete('events[]'); if(ev.length){ fd.append('events_list',ev.join(', ')); }
      var val=leadValue(fd); /* value goes to the thank-you conversion only, not into the email */
      fd.set('subject',fd.get('form-name')==='quick-inquiry'?subj('Quick inquiry',[fd.get('name'),fd.get('phone'),fd.get('event_date')])
        :subj('New inquiry',[fd.get('name'),fd.get('celebration'),fd.get('event_date'),fd.get('package')]));
      Array.from(fd.keys()).forEach(function(k){ if(k!=='form-name' && !String(fd.get(k)||'').trim()){ fd.delete(k); } });
      busy(form,true); finishing=true;
      var id='L'+Date.now().toString(36)+Math.random().toString(36).slice(2,6);
      var lead={id:id,value:val,pkg:fd.get('package')||'',form:fd.get('form-name'),email:(fd.get('email')||'').trim().toLowerCase(),phone:normPhone(fd.get('phone'))};
      /* the thank-you page counts a conversion only for a lead Netlify accepted: save it after a 2xx, never before */
      post(fd).then(function(r){ if(!r.ok){ throw new Error(r.status); } finished=true; if(partialTimer){ clearTimeout(partialTimer); partialTimer=null; }
        store.set('miraj_lead',lead,true); location.href='/thank-you'; }).catch(function(){ finishing=false; fail(form); });
    });
  });

  /* services-guide request: inline confirmation, not a lead conversion */
  $$('form.js-guide').forEach(function(form){
    form.addEventListener('input',clearErr);
    form.addEventListener('submit',function(e){
      e.preventDefault(); if(form.dataset.busy==='1'||!validate(form)){ return; } fill(form);
      var fd=new FormData(form); fd.set('subject',subj('Services guide request',[fd.get('email')])); busy(form,true);
      /* the guide is sent by a person replying to the notification email (Netlify has no auto-reply), so no timing promise (Tariq, Oct 26) */
      post(fd).then(function(r){ if(!r.ok){ throw 0; } form.innerHTML='<p class="small gf-done" role="status" tabindex="-1">Thank you. We’ll email you the services guide.</p>'; var dn=$('.gf-done',form); if(dn){ dn.focus(); } gt('event','guide_request',{page_path:location.pathname}); }).catch(function(){ fail(form); });
    });
  });
})();
