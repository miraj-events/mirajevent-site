#!/usr/bin/env python3
"""Build the static mirajevent.com site into ../site from the approved design (preview v47).

Run:  python3 tools/build.py
Output is committed (Netlify publishes /site as-is; no build step on Netlify).
"""
import html, json, os, re, shutil, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'tools', 'source', 'preview-v47.html')
OUT = os.path.join(ROOT, 'site')
DATA = os.path.join(ROOT, 'tools', 'data')
ASSETS_SRC = os.path.join(ROOT, 'tools', 'assets')

SITE = 'https://www.mirajevent.com'
GA4 = 'G-PVV95TW26B'
ADS = 'AW-16694224609'
ADS_FORM_LABEL = 'AW-16694224609/zLObCLKztNAZEOHNtpg-'
OAI_PIXEL = 'DQ1HpbhhjYa76ncDFrtMaF'
PHONE = '(586) 504-0207'
TEL = '+15865040207'
EMAIL = 'admin@mirajevent.com'
IG = 'https://www.instagram.com/miraj.events/'
FB = 'https://www.facebook.com/p/Miraj-Events-61559780220825/'
import hashlib
# cache-buster = hash of everything that ends up in site.css / site.js / sprite (assets are cached for a year)
_h = hashlib.sha1()
for _f in ['tools/source/preview-v47.html', 'tools/assets/site-extra.css', 'tools/assets/site.js']:
    _h.update(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), _f), 'rb').read())
VERSION = _h.hexdigest()[:10]

src = open(SRC, encoding='utf-8').read()
reviews = json.load(open(os.path.join(DATA, 'reviews.json'), encoding='utf-8'))


# ---------------------------------------------------------------- extraction
def between(s, start, end):
    i = s.index(start) + len(start)
    j = s.index(end, i)
    return s[i:j]

css = between(src, '<style>', '</style>')
sprite_symbol = re.search(r'<symbol id="me-mark".*?</symbol>', src, re.S).group(0)
grad = re.search(r'<linearGradient id="meg".*?</linearGradient>', src, re.S).group(0)

def view(name):
    m = re.search(r'<section class="view" id="view-%s"[^>]*>(.*?)</section>\s*(?=<!--|</main>)' % name, src, re.S)
    return m.group(1)

body = {v: view(v) for v in ['home', 'services', 'about', 'contact', 'thanks']}

# ---------------------------------------------------------------- CSS clean-up
css = re.sub(r'/\* preview controls.*?(?=/\* reveal on scroll)', '', css, flags=re.S)
css = css.replace('/* Layout: one file, five views (home, services, about, contact, thanks) switched by hash;', '/* Miraj Events site styles. Layout:')
css += open(os.path.join(ASSETS_SRC, 'site-extra.css'), encoding='utf-8').read()


# ---------------------------------------------------------------- transforms
LINKS = {
    '#home': '/', '#services': '/services', '#about': '/about', '#contact': '/contact',
    '#thanks': '/thank-you', '#privacy': '/privacy',
}

def relink(h, page):
    for k, v in LINKS.items():
        h = h.replace('href="%s"' % k, 'href="%s"' % v)
    # in-page anchors that live on other pages
    if page != 'home':
        h = h.replace('href="#inquire"', 'href="/contact#contact-form"')
    if page != 'contact':
        h = h.replace('href="#contact-form"', 'href="/contact#contact-form"')
    return h

def strip_variants(h):
    h = re.sub(r'\s*<h1 data-head="team" hidden>.*?</h1>', '', h, flags=re.S)
    h = h.replace('<h1 data-head="weekend">', '<h1>')
    h = re.sub(r'\s*<p class="lead" data-copy-v="full">.*?</p>', '', h, flags=re.S)
    h = h.replace(' data-copy-v="min" hidden', '')
    return h

def logo_use(h):
    return h.replace('<use href="#me-mark"', '<use href="/assets/sprite.svg?v=%s#me-mark"' % VERSION)


# ---------------------------------------------------------------- reviews carousel
def esc(t):
    return html.escape(t, quote=True)

def reviews_block(variant=''):
    r = reviews
    slides = []
    n = len(r['reviews'])
    for i, rv in enumerate(r['reviews']):
        paras = ''.join('<p>%s</p>' % esc(p.strip()) for p in rv['text'].split('\n\n') if p.strip())
        slides.append(
            '<article class="rv-slide%s" role="group" aria-roledescription="slide" aria-label="%d of %d"%s>'
            '<div class="rv-who"><span class="rv-av" aria-hidden="true">%s</span>'
            '<div class="rv-id"><strong>%s</strong><span>%s</span></div>'
            '<span class="rv-src">Google</span></div>'
            '<div class="rv-st" aria-label="%d out of 5 stars">★★★★★</div>'
            '<div class="rv-text" id="rvt-%s-%d">%s</div>'
            '<button type="button" class="rv-more" aria-expanded="false" aria-controls="rvt-%s-%d">Read more</button>'
            '</article>' % (
                ' is-active' if i == 0 else '', i + 1, n, '' if i == 0 else ' aria-hidden="true"',
                esc(rv['name'][0]), esc(rv['name']), esc(rv['role']), rv['rating'],
                variant or 'x', i, paras, variant or 'x', i))
    dots = ''.join('<button type="button" class="rv-dot" aria-label="Show review %d"%s></button>' % (
        i + 1, ' aria-current="true"' if i == 0 else '') for i in range(n))
    return (
        '<section class="rv %s" aria-roledescription="carousel" aria-label="Google reviews">'
        '<a class="rv-head" href="%s" target="_blank" rel="noopener">'
        '<span class="rv-score">%.1f</span><span class="rv-meta"><span class="rv-stars" aria-hidden="true">★★★★★</span>'
        '<span class="rv-g">Google reviews</span></span></a>'
        '<div class="rv-track" aria-live="polite">%s</div>'
        '<div class="rv-nav"><button type="button" class="rv-arrow rv-prev" aria-label="Previous review">‹</button>'
        '<div class="rv-dots">%s</div>'
        '<button type="button" class="rv-arrow rv-next" aria-label="Next review">›</button></div>'
        '<a class="textlink" href="%s" target="_blank" rel="noopener">Read our reviews on Google →</a>'
        '</section>' % (variant, esc(r['reviews_url']), r['rating'], ''.join(slides), dots,
                        esc(r['reviews_url'])))


# ---------------------------------------------------------------- forms
HIDDEN_ATTR = ['gclid', 'gbraid', 'wbraid', 'oppref', 'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
               'landing_page', 'first_referrer', 'ai_referrer', 'page']

def hidden_fields(form_name):
    h = '<input type="hidden" name="form-name" value="%s">' % form_name
    h += '<p class="hp" aria-hidden="true"><label>Leave blank <input name="bot-field" tabindex="-1" autocomplete="off"></label></p>'
    h += ''.join('<input type="hidden" name="%s">' % f for f in HIDDEN_ATTR)
    return h

def name_fields(h, mapping):
    for _id, nm in mapping.items():
        h = re.sub(r'(<(?:input|select|textarea)[^>]*\bid="%s")' % re.escape(_id), r'\1 name="%s"' % nm, h)
    return h

def wire_forms(h, page):
    # Home two-step form -> one <form> with two steps
    if page == 'home':
        m = re.search(r'<form id="homeStep1".*?</form>\s*<form id="homeStep2".*?</form>', h, re.S)
        block = m.group(0)
        s1 = between(block, 'data-next="homeStep2">', '</form>')
        s2 = between(block, '<form id="homeStep2" class="form" hidden>', '</form>')
        s1 = s1.replace('<button class="btn btn-block" type="submit">Continue →</button>',
                        '<button class="btn btn-block" type="button" data-next>Continue →</button>')
        new = ('<form id="homeForm" class="form js-inquiry" method="POST" action="/thank-you" data-form="inquiry" data-start="inquiry-start" novalidate>'
               + hidden_fields('inquiry')
               + '<div class="fstep" data-fstep="1">' + s1 + '</div>'
               + '<div class="fstep" data-fstep="2" hidden>' + s2 + '</div></form>')
        h = h.replace(block, new)
        h = name_fields(h, {'h-type': 'celebration', 'h-date': 'event_date', 'h-phone': 'phone', 'h-name': 'name',
                            'h-email': 'email', 'h-guests': 'guests', 'h-venue': 'venue'})
        h = h.replace('<label for="h-phone">Phone / WhatsApp</label>', '<label for="h-phone">Phone / WhatsApp *</label>')
        h = h.replace('<label for="h-name">Your name</label><input id="h-name" name="name" type="text" autocomplete="name">',
                      '<label for="h-name">Your name *</label><input id="h-name" name="name" type="text" autocomplete="name" required>')
        h = h.replace('<label for="h-email">Email</label><input id="h-email" name="email" type="email" autocomplete="email">',
                      '<label for="h-email">Email *</label><input id="h-email" name="email" type="email" autocomplete="email" required>')
    if page == 'contact':
        h = h.replace('<form class="card form" id="contactForm" aria-label="Full inquiry">',
                      '<form class="card form js-inquiry" id="contactForm" aria-label="Full inquiry" method="POST" action="/thank-you" data-form="inquiry" data-start="inquiry-start" novalidate>'
                      + hidden_fields('inquiry'))
        h = h.replace('<div class="cstep" data-cstep="1">', '<div class="fstep" data-fstep="1">')
        h = h.replace('<div class="cstep" data-cstep="2" hidden>', '<div class="fstep" data-fstep="2" hidden>')
        h = h.replace('<span id="c-stepmeta">', '<span data-stepmeta>')
        h = h.replace('<button class="btn btn-block" type="button" id="c-continue">', '<button class="btn btn-block" type="button" data-next>')
        h = h.replace('<a class="textlink" href="#" id="c-back">', '<a class="textlink" href="#contact-form" data-back>')
        h = name_fields(h, {'c-name': 'name', 'c-partner': 'partner', 'c-email': 'email', 'c-phone': 'phone',
                            'c-type': 'celebration', 'c-date': 'event_date', 'c-venue': 'venue', 'c-guests': 'guests',
                            'c-budget': 'budget', 'c-pkg': 'package', 'c-heard': 'heard', 'c-msg': 'message'})
        ev = ['welcome', 'mehndi', 'nikkah', 'church', 'ceremony', 'baraat', 'shaadi', 'valima', 'rehearsal', 'brunch', 'after', 'other']
        for e in ev:
            h = h.replace('<input type="checkbox" id="ev-%s">' % e, '<input type="checkbox" id="ev-%s" name="events[]" value="%s">' % (e, e))
    # short forms (services / about)
    def short(m):
        inner = m.group(2)
        inner = re.sub(r'id="[sa]-name"', r'\g<0> name="name" required', inner)
        inner = re.sub(r'id="[sa]-phone"', r'\g<0> name="phone" required', inner)
        inner = re.sub(r'id="[sa]-date"', r'\g<0> name="event_date"', inner)
        return ('<form class="grid3 js-inquiry" aria-label="Short inquiry" method="POST" action="/thank-you" data-form="quick-inquiry" novalidate>'
                + hidden_fields('quick-inquiry') + inner + '</form>')
    h = re.sub(r'(<form class="grid3" aria-label="Short inquiry">)(.*?)</form>', short, h, flags=re.S)
    h = h.replace('<form class="guide-form" aria-label="Request the services guide">',
                  '<form class="guide-form js-guide" aria-label="Request the services guide" method="POST" action="/thank-you" data-form="guide-request" novalidate>'
                  + hidden_fields('guide-request'))
    h = h.replace('id="guide-email" aria-label', 'id="guide-email" name="email" required aria-label')
    return h

def forms_definition():
    """Static skeletons so Netlify registers every form + field at deploy (forms are submitted by JS)."""
    common = ''.join('<input type="hidden" name="%s">' % f for f in HIDDEN_ATTR)
    inquiry_fields = ['name', 'partner', 'email', 'phone', 'celebration', 'event_date', 'venue', 'guests', 'budget',
                      'package', 'heard', 'message', 'events_list', 'value']
    def f(name, fields):
        return ('<form name="%s" data-netlify="true" netlify-honeypot="bot-field" hidden>'
                '<input name="bot-field">%s%s</form>\n' % (name, ''.join('<input name="%s">' % x for x in fields), common))
    return (f('inquiry', inquiry_fields) + f('inquiry-start', ['email', 'phone', 'name', 'celebration', 'event_date'])
            + f('quick-inquiry', ['name', 'phone', 'event_date']) + f('guide-request', ['email']))


# ---------------------------------------------------------------- schema
def org_schema():
    return {
        "@context": "https://schema.org",
        "@type": ["ProfessionalService", "LocalBusiness"],
        "@id": SITE + "/#business",
        "name": "Miraj Events",
        "legalName": "Miraj Events, LLC",
        "url": SITE + "/",
        "logo": SITE + "/assets/miraj-logo-512.png",
        "image": SITE + "/assets/og-image.png",
        "description": "Wedding planner and day-of coordinator for multicultural, multi-event weddings across Metro Detroit, Toledo and Chicago.",
        "telephone": "+1-586-504-0207",
        "email": EMAIL,
        "priceRange": "$1,975–$9,500+",
        "address": {"@type": "PostalAddress", "addressLocality": "Sterling Heights", "addressRegion": "MI", "postalCode": "48314", "addressCountry": "US"},
        "areaServed": [{"@type": "City", "name": c} for c in [
            "Detroit, MI", "Sterling Heights, MI", "Troy, MI", "Rochester Hills, MI", "Dearborn, MI", "Ann Arbor, MI",
            "Novi, MI", "Farmington Hills, MI", "Bloomfield Hills, MI", "Toledo, OH", "Chicago, IL"]],
        "founder": {"@type": "Person", "name": "Mehreen Buksh"},
        "sameAs": [IG, FB],
        "knowsAbout": ["Wedding planning", "Day-of wedding coordination", "Multi-event wedding weekends",
                       "South Asian weddings", "Arab and Chaldean weddings", "Interfaith weddings", "Event planning"],
    }

PACKAGES = [
    ('day-of', 'Day-of Coordination', 1975, 'You planned it. We run it. The final month and the day: confirmations, timeline, rehearsal, setup to send-off.'),
    ('design', 'Design + Coordination', 4750, 'Everything in Day-of, plus the look: concept, floor plan, décor team and the install.'),
    ('planning', 'Planning + Design', 6500, 'Everything in Design + Coordination, plus planning with you from signing: vendors, budget, portal, hotel block.'),
    ('full', 'Full Planning', 9500, 'Everything in Planning + Design. We lead; you choose.'),
]

def services_schema():
    return {
        "@context": "https://schema.org", "@type": "OfferCatalog", "name": "Wedding planning packages",
        "itemListElement": [{
            "@type": "Offer", "url": "%s/services#%s" % (SITE, k),
            "priceSpecification": {"@type": "PriceSpecification", "minPrice": p, "priceCurrency": "USD"},
            "itemOffered": {"@type": "Service", "name": n, "description": d, "provider": {"@id": SITE + "/#business"},
                            "areaServed": "Metro Detroit, Toledo and Chicago"}} for k, n, p, d in PACKAGES]}

def faq_schema(h):
    qs = re.findall(r'<details[^>]*><summary>(.*?)</summary><p class="ans">(.*?)</p></details>', h, re.S)
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": html.unescape(re.sub('<.*?>', '', q)),
         "acceptedAnswer": {"@type": "Answer", "text": html.unescape(re.sub('<.*?>', '', a)).strip()}} for q, a in qs]}

def ld(obj):
    return '<script type="application/ld+json">%s</script>' % json.dumps(obj, ensure_ascii=False, separators=(',', ':'))


# ---------------------------------------------------------------- page chrome
def head(title, desc, path, view, schema=(), noindex=False):
    canonical = SITE + (path if path != '/' else '/')
    robots = '<meta name="robots" content="noindex, follow">' if noindex else '<meta name="robots" content="index, follow, max-image-preview:large">'
    return f'''<!doctype html>
<html lang="en" data-theme="lightink" data-copy="min">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canonical}">
{robots}
<meta name="theme-color" content="#2C2E31">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Miraj Events">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{SITE}/assets/og-image.png">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;1,300;1,400&family=DM+Sans:wght@300;400;500&display=swap">
<link rel="stylesheet" href="/assets/site.css?v={VERSION}">
<!-- Google tag (GA4 {GA4} + Google Ads {ADS}) -->
<script async src="https://www.googletagmanager.com/gtag/js?id={GA4}"></script>
<script>
window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}
window.MIRAJ_LIVE=/(^|\.)mirajevent\.com$/.test(location.hostname);
gtag('js',new Date());
if(window.MIRAJ_LIVE){{gtag('config','{GA4}');gtag('config','{ADS}',{{allow_enhanced_conversions:true}});}}
else{{console.info('Miraj: staging/preview host, Google Analytics + Ads not sending.');}}
</script>
<!-- OpenAI Ads measurement pixel ({OAI_PIXEL}); live domain only -->
<script>
(function(w,d,s,u){{if(!w.MIRAJ_LIVE||w.oaiq){{return;}}var q=function(){{q.q.push(arguments);}};q.q=[];w.oaiq=q;
var js=d.createElement(s);js.async=true;js.src=u;var f=d.getElementsByTagName(s)[0];f.parentNode.insertBefore(js,f);
}})(window,document,'script','https://bzrcdn.openai.com/sdk/oaiq.min.js');
if(window.oaiq){{oaiq('init',{{pixelId:'{OAI_PIXEL}'}});}}
</script>
{''.join(ld(s) for s in schema)}
</head>
<body data-view="{view}">
<a class="skip" href="#main">Skip to content</a>
'''

def header():
    h = between(src, '<header class="site-header">', '</header>')
    h = relink(h, 'x')
    h = logo_use(h)
    h = h.replace('href="#home"', 'href="/"')
    return '<header class="site-header">' + h + '</header>\n'

def footer(page):
    f = between(src, '<footer class="rule-top">', '</footer>')
    f = relink(f, page)
    f = logo_use(f)
    f = f.replace('<span id="yr">2026</span>', '<span id="yr">%s</span>' % datetime.date.today().year)
    f = f.replace(' title="Privacy policy page to be added at build"', '')
    f = f.replace('<span>admin@mirajevent.com · (586) 504-0207</span>',
                  '<span><a href="mailto:%s">%s</a> · <a href="tel:%s">%s</a></span>' % (EMAIL, EMAIL, TEL, PHONE))
    sticky = '<a class="sticky-cta" href="%s">Check availability</a>' % ('#inquire' if page in ('home', 'dayof') else '/contact#contact-form')
    return ('<footer class="rule-top">' + f + '</footer>\n' + sticky + '\n'
            '<script src="/assets/site.js?v=%s" defer></script>\n</body>\n</html>\n' % VERSION)

def page(fname, title, desc, path, view, main_html, schema=(), noindex=False, extra_js=''):
    out = head(title, desc, path, view, schema, noindex) + header() + '<main id="main">\n' + main_html + '\n</main>\n' + footer(view)
    if extra_js:
        out = out.replace('</body>', extra_js + '\n</body>')
    os.makedirs(os.path.dirname(os.path.join(OUT, fname)), exist_ok=True)
    open(os.path.join(OUT, fname), 'w', encoding='utf-8').write(out)
    return out


# ---------------------------------------------------------------- build
def prep(name):
    h = body[name]
    h = strip_variants(h)
    h = relink(h, name)
    h = logo_use(h)
    h = wire_forms(h, name)
    return h

if os.path.isdir(OUT):
    shutil.rmtree(OUT)
os.makedirs(os.path.join(OUT, 'assets'))

REV_URL = esc(reviews['reviews_url'])

PRESS = [('Bloomberg', 'https://www.bloomberg.com/news/articles/2025-04-16/stock-market-drop-has-couples-cutting-wedding-costs'),
         ('Voyage Michigan', 'https://voyagemichigan.com/interview/meet-mehreen-buksh-of-miraj-events'),
         ('Peerspace · #2 in Detroit', 'https://www.peerspace.com/resources/wedding-planners-in-detroit/')]
LISTINGS = [('The Knot', 'K', 'https://www.theknot.com/marketplace/miraj-events-llc-sterling-heights-mi-2089876'),
            ('WeddingWire', 'W', 'https://www.weddingwire.com/biz/miraj-events-llc/e0bb1fcf9e27fb41.html')]
def press_html(cls):
    links = ''.join('<a class="%s" href="%s" target="_blank" rel="noopener">%s</a>' % (cls, esc(u), esc(n)) for n, u in PRESS)
    marks = ''.join('<a class="lst-mark" href="%s" target="_blank" rel="noopener" aria-label="Miraj Events on %s" title="Miraj Events on %s">'
                    '<span aria-hidden="true">%s</span></a>' % (esc(u), n, n, ch) for n, ch, u in LISTINGS)
    return links + '<span class="lst-marks">' + marks + '</span>'

# HOME
home = prep('home')
home = home.replace('<p class="lead">Multicultural, multi-event weddings. One team.</p>', '<p class="lead">Wedding planning and day-of coordination for multicultural, multi-event weddings.</p>', 1)
home = home.replace('<span class="hp-logo">The Knot</span><span class="hp-logo">WeddingWire</span><span class="hp-logo">Bloomberg</span><span class="hp-logo">Voyage Michigan</span>', press_html('hp-logo'))
# Section order (Tariq, Oct 24): hero -> packages -> why Miraj -> weekend traditions -> proof/reviews -> inquire
_wk_i = home.index('<div class="band" id="weekend">')
_why_i = home.index('<div class="band band-white rule-top"><div class="wrap">\n    <div class="why-head')
_pk_i = home.index('<div class="band rule-top" id="packages">')
_pr_i = home.index('<div class="band band-dark proof">')
_wk, _why, _pk = home[_wk_i:_why_i], home[_why_i:_pk_i], home[_pk_i:_pr_i]
_wk = _wk.replace('<div class="band" id="weekend">', '<div class="band rule-top" id="weekend">', 1)
home = home[:_wk_i] + _pk + _why + _wk + home[_pr_i:]
home = home.replace('<a class="rating" href="#" aria-label="Read our Google reviews"><span class="stars" aria-hidden="true">★</span><span>See our Google reviews →</span></a>',
                    '<a class="rating" href="#reviews" aria-label="Rated %.1f out of 5 on Google. Read reviews"><span class="stars" aria-hidden="true">★★★★★</span><span class="r-txt" aria-hidden="true"><strong>%.1f</strong> on Google</span></a>' % (reviews['rating'], reviews['rating']))
home = re.sub(r'<div class="proof-quote reveal">.*?</div>\s*</div></div>',
              '<div class="proof-quote reveal" id="reviews">' + reviews_block('home') + '</div>\n  </div></div>', home, flags=re.S)
page('index.html', 'Miraj Events | Detroit Wedding & Event Planning',
     'Miraj Events specializes in Detroit wedding and event planning, delivering polished, stress free celebrations from start to finish. Day-of coordination to full planning for multi-event weddings.',
     '/', 'home', home, schema=[org_schema(), {"@context": "https://schema.org", "@type": "WebSite", "name": "Miraj Events", "url": SITE + "/"}])

# SERVICES
svc = prep('services')
svc = svc.replace('<h1>Four packages. Each includes the one before it.</h1>',
                  '<h1>Wedding planning packages. Each includes the one before it.</h1>')
svc = svc.replace('<p class="lead">Starting prices for a single event. Multi-event weekends are packaged together on your call.</p>',
                  '<p class="lead">Day-of coordination to full planning in Metro Detroit, Toledo and Chicago. Starting prices for a single event; multi-event weekends are packaged together on your call.</p>')
svc = svc.replace('<h2>Day-of Coordination</h2>', '<h2><a href="/day-of-coordination">Day-of Coordination</a></h2>')
svc = svc.replace('<a class="textlink" href="/contact">Tell us about yours →</a>', '<a class="textlink" href="/contact#contact-form">Tell us about yours →</a>')
page('services.html', 'Wedding Planning Services & Pricing | Miraj Events Detroit',
     'Day-of coordination from $1,975, design + coordination, planning + design and full wedding planning in Metro Detroit, Toledo and Chicago. Multi-event wedding weekends packaged together.',
     '/services', 'services', svc, schema=[services_schema(), faq_schema(svc)])

# ABOUT
ab = prep('about')
ab = ab.replace('<span class="logo-slot">The Knot</span><span class="logo-slot">WeddingWire</span><span class="logo-slot">Bloomberg</span><span class="logo-slot">Voyage Michigan</span>', press_html('logo-slot'))
ARTICLES = [
    ('Bloomberg', 'Stock market drop has couples cutting wedding costs', 'April 2025', PRESS[0][1]),
    ('Voyage Michigan', 'Meet Mehreen Buksh of Miraj Events', 'Interview', PRESS[1][1]),
    ('Peerspace', 'Top wedding planners in Detroit: Miraj Events at #2', 'Ranking', PRESS[2][1]),
    ('Shoutout Michigan', 'Meet Mehreen Buksh, founder and lead coordinator', 'Interview', 'https://shoutoutmichigan.com/meet-mehreen-buksh-founder-lead-coordinator/'),
    ('CanvasRebel', 'Meet Mehreen Buksh', 'Interview', 'https://canvasrebel.com/meet-mehreen-buksh/'),
]
press_list = ('<div class="band rule-top" id="press"><div class="wrap two-col" style="align-items:start">'
              '<div class="stack reveal"><p class="eyebrow">Press</p><h2 class="h2" style="font-size:clamp(28px,3.2vw,40px)">In the news.</h2></div>'
              '<ul class="press-list reveal">' + ''.join(
                  '<li><a href="%s" target="_blank" rel="noopener"><span class="pl-outlet">%s</span><span class="pl-title">%s</span>'
                  '<span class="pl-meta">%s · Read →</span></a></li>' % (esc(u), esc(o), esc(t), esc(m)) for o, t, m, u in ARTICLES)
              + '</ul></div></div>')
# About layout v2 (Oct 24): founder hero with portrait slot, light stats row, how-we-work, press, one CTA band
MONO = '<svg viewBox="0 0 2386 1632" aria-hidden="true" focusable="false"><use href="/assets/sprite.svg?v=%s#me-mark" width="2386" height="1632"/></svg>' % VERSION
ab = (
'<section class="ab-hero"><div class="wrap ab-grid">'
  '<div class="ab-copy reveal">'
    '<p class="eyebrow">About Miraj Events</p>'
    '<h1>An experienced lead planner, on <em>every</em> event.</h1>'
    '<p class="lead">Founded and led by Mehreen Buksh, Miraj Events plans, designs and runs weddings across Metro Detroit, Toledo and Chicago.</p>'
    '<p>Our specialty is the multi-event wedding weekend: South Asian, Arab and Chaldean, Hindu and Sikh, West African and interfaith celebrations, often across several days and two faiths. We also run engagement parties, nonprofit galas and milestone celebrations.</p>'
    '<p>We take a limited number of weddings each season, so every event has a lead planner and one assistant per 100 guests.</p>'
    '<div class="actions"><a class="btn" href="/contact#contact-form">Check your date</a><a class="btn btn-outline" href="/services">Services &amp; pricing</a></div>'
  '</div>'
  '<figure class="ab-portrait reveal" data-photo="mehreen">'
    '<div class="ab-ph">' + MONO + '</div>'
    '<figcaption><strong>Mehreen Buksh</strong><span>Founder &amp; lead planner</span></figcaption>'
  '</figure>'
'</div>'
'<div class="wrap"><dl class="ab-stats reveal">'
  '<div><dt>50+</dt><dd>Multicultural, multi-event weddings in the past two years</dd></div>'
  '<div><dt>900+</dt><dd>Guests at our largest event</dd></div>'
  '<div><dt>3 yrs</dt><dd>Running the same nonprofit gala, year after year</dd></div>'
  '<div><dt>1:100</dt><dd>Assistants to guests on every event</dd></div>'
'</dl></div></section>'
'<div class="band band-white rule-top"><div class="wrap two-col" style="align-items:start">'
  '<div class="stack reveal"><p class="eyebrow">How we work</p><h2 class="h2" style="font-size:clamp(28px,3.2vw,40px)">Calm, prepared, and on your side.</h2></div>'
  '<div class="ab-pillars reveal">'
    '<div><h3>Calm under pressure</h3><p>Problems are solved before they reach you or your family.</p></div>'
    '<div><h3>Every tradition respected</h3><p>Prayer times, seating, halal menus and ritual timing are built into the plan.</p></div>'
    '<div><h3>Clear pricing</h3><p>A flat fee, quoted up front. Never a percentage of your budget.</p></div>'
  '</div>'
'</div></div>'
+ press_list +
'<div class="band band-dark ab-cta"><div class="wrap ab-cta-in">'
  '<div><h2 class="h2" style="font-size:clamp(28px,3.4vw,44px)">Let&#8217;s talk about your celebration.</h2>'
  '<p class="lead">A 30-minute call about your events, your families and your budget.</p></div>'
  '<div class="actions"><a class="btn btn-gold" href="/contact#contact-form">Check your date</a><a class="btn btn-ivory" href="tel:+15865040207">Call (586) 504-0207</a></div>'
'</div></div>'
)
page('about.html', 'About Miraj Events | Mehreen Buksh, Detroit Wedding Planner',
     'Founded by Mehreen Buksh, Miraj Events plans and runs multicultural, multi-event weddings across Metro Detroit, Toledo and Chicago. 50+ weddings in two years; largest event 900+ guests.',
     '/about', 'about', ab, schema=[org_schema()])

# CONTACT
ct = prep('contact')
# Contact layout v2 (Oct 24): form above the fold; compact package strip; reviews below
_form = re.search(r'<form class="card form js-inquiry" id="contactForm".*?</form>', ct, re.S).group(0)
_tiers = ct[ct.index('<div class="tiers">'):ct.index('<p class="small" style="text-align:center;margin-top:16px">')]
ct = (
'<section class="ct-rv"><div class="wrap">' + reviews_block('wide') + '</div></section>'
'<section class="ct-top" id="contact-form"><div class="wrap ct-grid">'
  '<div class="ct-copy">'
    '<p class="eyebrow">Contact</p>'
    '<h1>Let&#8217;s check <em>your</em> date.</h1>'
    '<p class="lead">Two short steps. We reply within 24 hours with availability and next steps.</p>'
  '</div>'
  '<div class="ct-formwrap">'
    '<p class="ct-note">Package descriptions and starting prices are <a href="#packages-ct">below&nbsp;&darr;</a></p>'
    + _form +
  '</div>'
  '<div class="ct-more">'
    '<ol class="ct-steps"><li><span>1</span>We reply within 24 hours</li><li><span>2</span>A 30-minute call about your events</li><li><span>3</span>Your customized package within 48 hours</li></ol>'
    '<ul class="ct-direct">'
      '<li><span class="eyebrow">Call or text</span><a href="tel:+15865040207">(586) 504-0207</a></li>'
      '<li><span class="eyebrow">WhatsApp</span><a href="https://wa.me/15865040207">Message us</a></li>'
      '<li><span class="eyebrow">Email</span><a href="mailto:admin@mirajevent.com">admin@mirajevent.com</a></li>'
    '</ul>'
  '</div>'
'</div></section>'
'<div class="band rule-top" id="packages-ct"><div class="wrap">'
  '<div class="ct-pk-head"><p class="eyebrow">Our packages</p><p class="small">Starting prices for a single event. Tap one for details; "Choose" adds it to your inquiry.</p></div>'
  + _tiers +
'</div></div>'
)
page('contact.html', 'Contact Miraj Events | Check Your Wedding Date',
     'Tell us your date and traditions. Miraj Events replies within 24 hours. Call (586) 504-0207 or WhatsApp. Wedding planning and day-of coordination in Metro Detroit.',
     '/contact', 'contact', ct, schema=[org_schema()])

# DAY-OF landing page (keeps the indexed /day-of-coordination URL alive)
dayof = open(os.path.join(ASSETS_SRC, 'day-of.html'), encoding='utf-8').read()
dayof = dayof.replace('{{REVIEWS}}', reviews_block('dayof'))
dayof_form = re.search(r'<div class="band band-white rule-top" id="inquire">.*?</div></div>', home, re.S).group(0)
dayof_form = dayof_form.replace('id="inquire"', 'id="inquire"').replace('<option>Wedding weekend (multiple events)</option><option>Wedding (single event)</option>',
                                                                        '<option>Wedding (single event)</option><option>Wedding weekend (multiple events)</option>')
dayof_form = dayof_form.replace('data-start="inquiry-start" novalidate>', 'data-start="inquiry-start" data-package="Day-of Coordination" novalidate>')
dayof = dayof.replace('{{FORM}}', dayof_form)
dayof_faq = [q for q in re.findall(r'<details[^>]*>.*?</details>', svc, re.S)
             if any(k in q for k in ['How do payments work', 'Do we have to use your vendors', 'Can you run our whole wedding weekend', 'Do you travel', 'postpone'])]
dayof = dayof.replace('{{FAQ}}', '\n'.join(dayof_faq).replace('<details open>', '<details>'))
page('day-of-coordination.html', 'Day-of Wedding Coordinator in Detroit, MI | Miraj Events',
     'Day-of wedding coordination in Metro Detroit from $1,975. We take over the final month and run your wedding day from setup to send-off, so you can be a guest at your own wedding.',
     '/day-of-coordination', 'dayof', dayof, schema=[org_schema(), {
         "@context": "https://schema.org", "@type": "Service", "name": "Day-of Wedding Coordination",
         "serviceType": "Day-of wedding coordinator", "provider": {"@id": SITE + "/#business"},
         "areaServed": "Metro Detroit, Toledo and Chicago",
         "offers": {"@type": "Offer", "priceSpecification": {"@type": "PriceSpecification", "minPrice": 1975, "priceCurrency": "USD"}}},
         faq_schema(dayof)])

# THANK YOU (Google Ads Form Fill conversion fires here, same send_to as the Squarespace site)
th = prep('thanks')
th = th.replace('<a class="btn" href="/services">How it works</a>', '<a class="btn" href="/services">How it works</a>')
th = th.replace('<p class="small">admin@mirajevent.com · (586) 504-0207 · Instagram @miraj.events</p>',
                '<p class="small"><a href="mailto:%s">%s</a> · <a href="tel:%s">%s</a> · <a href="%s">Instagram @miraj.events</a></p>' % (EMAIL, EMAIL, TEL, PHONE, IG))
conv_js = '''<script>
/* Google Ads "Form Fill" conversion (unchanged send_to from the Squarespace site) + GA4 generate_lead.
   Fires once per submission. Value = proxy by package chosen; enhanced conversions use the email/phone just submitted. */
(function(){
  var lead=null; try{ lead=JSON.parse(sessionStorage.getItem('miraj_lead')||'null'); }catch(e){}
  var fromSite=document.referrer && document.referrer.indexOf(location.hostname)>-1;
  var nav=(performance.getEntriesByType&&performance.getEntriesByType('navigation')[0])||{};
  if(!window.MIRAJ_LIVE){ console.info('Miraj: conversion skipped on staging', lead); return; }
  if(!lead && (!fromSite || nav.type==='reload' || nav.type==='back_forward')){ return; }
  lead=lead||{};
  var tid=lead.id||('ty-'+Date.now());
  try{ if(sessionStorage.getItem('miraj_conv_'+tid)){ return; } sessionStorage.setItem('miraj_conv_'+tid,'1'); }catch(e){}
  var ud={}; if(lead.email){ ud.email=lead.email; } if(lead.phone){ ud.phone_number=lead.phone; }
  if(ud.email||ud.phone_number){ gtag('set','user_data',ud); }
  gtag('event','conversion',{'send_to':'%s','value':lead.value||1,'currency':'USD','transaction_id':tid});
  if(window.oaiq){ oaiq('measure','lead_created',{type:'customer_action'},{event_id:tid}); }
  gtag('event','generate_lead',{'value':lead.value||1,'currency':'USD','form_name':lead.form||'inquiry','package':lead.pkg||''});
  try{ sessionStorage.removeItem('miraj_lead'); }catch(e){}
})();
</script>''' % ADS_FORM_LABEL
page('thank-you.html', 'Thank You | Miraj Events', 'Thank you for your inquiry. Miraj Events will be in touch within 24 hours.',
     '/thank-you', 'thanks', th, noindex=True, extra_js=conv_js)

# PRIVACY
pv = open(os.path.join(ASSETS_SRC, 'privacy.html'), encoding='utf-8').read()
page('privacy.html', 'Privacy Policy | Miraj Events', 'How Miraj Events, LLC collects and uses information submitted through mirajevent.com.',
     '/privacy', 'privacy', pv)

# 404
nf = '''<section class="band"><div class="wrap"><div class="thanks">
<p class="eyebrow">Page not found</p><h1 class="h1">This page has moved.</h1>
<p class="lead">The page you were looking for isn't here, but everything you need is a click away.</p>
<div class="actions"><a class="btn" href="/">Home</a><a class="btn btn-outline" href="/services">Services &amp; pricing</a><a class="btn btn-outline" href="/contact">Contact</a></div>
</div></div></section>'''
page('404.html', 'Page Not Found | Miraj Events', 'This page could not be found.', '/404', 'thanks', nf, noindex=True)

# Netlify form skeletons (not linked, noindex)
open(os.path.join(OUT, 'netlify-forms.html'), 'w').write(
    '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="robots" content="noindex"><title>Forms</title></head><body>\n'
    + forms_definition() + '</body></html>\n')

# ---------------------------------------------------------------- assets
open(os.path.join(OUT, 'assets', 'site.css'), 'w', encoding='utf-8').write(css)
shutil.copy(os.path.join(ASSETS_SRC, 'site.js'), os.path.join(OUT, 'assets', 'site.js'))
sprite = ('<svg xmlns="http://www.w3.org/2000/svg"><defs>%s</defs>%s</svg>\n' % (grad, sprite_symbol))
open(os.path.join(OUT, 'assets', 'sprite.svg'), 'w').write(sprite)
path_d = re.search(r'<path fill="url\(#meg\)" d="([^"]+)"', sprite_symbol).group(1)
fav = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="-283 -659 3040 3040"><rect x="-283" y="-659" width="3040" height="3040" rx="430" fill="#2C2E31"/>'
       '<defs>%s</defs><g transform="translate(0,0)"><path fill="url(#meg)" d="%s"/></g></svg>\n' % (grad, path_d))
open(os.path.join(OUT, 'favicon.svg'), 'w').write(fav)
for f in os.listdir(os.path.join(ASSETS_SRC, 'static')):
    s = os.path.join(ASSETS_SRC, 'static', f)
    shutil.copy(s, os.path.join(OUT, f if not f.startswith('assets__') else os.path.join('assets', f[8:])))

# sitemap + robots + llms
today = datetime.date.today().isoformat()
urls = [('/', '1.0'), ('/services', '0.9'), ('/day-of-coordination', '0.9'), ('/contact', '0.8'), ('/about', '0.7'), ('/privacy', '0.2')]
open(os.path.join(OUT, 'sitemap.xml'), 'w').write(
    '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + ''.join('  <url><loc>%s%s</loc><lastmod>%s</lastmod><priority>%s</priority></url>\n' % (SITE, u if u != '/' else '/', today, p) for u, p in urls)
    + '</urlset>\n')
open(os.path.join(OUT, 'robots.txt'), 'w').write(
    'User-agent: *\nAllow: /\nDisallow: /thank-you\nDisallow: /netlify-forms.html\n\nSitemap: %s/sitemap.xml\n' % SITE)
llms = open(os.path.join(ASSETS_SRC, 'llms.txt'), encoding='utf-8').read()
open(os.path.join(OUT, 'llms.txt'), 'w').write(llms)
print('built', sorted(os.listdir(OUT)))
