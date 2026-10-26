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
# Nav label (Tariq, Oct 25): "Inquire" -> "Contact Us" everywhere it is a link/label
src = src.replace('data-nav="contact">Inquire</a>', 'data-nav="contact">Contact Us</a>')
src = src.replace('<a href="#contact">Inquire</a>', '<a href="#contact">Contact Us</a>')
src = src.replace('<p class="eyebrow">Inquire</p>', '<p class="eyebrow">Contact us</p>')
src = src.replace('<li><strong>Inquire</strong>', '<li><strong>Contact us</strong>')
# Nav order (Tariq, Oct 25): About before Services (desktop nav, mobile dropdown, footer)
for _a, _b in [('<a href="#services" data-nav="services">Services</a>\n      <a href="#about" data-nav="about">About</a>',
                '<a href="#about" data-nav="about">About</a>\n      <a href="#services" data-nav="services">Services</a>'),
               ('<a href="#services">Services</a>\n    <a href="#about">About</a>',
                '<a href="#about">About</a>\n    <a href="#services">Services</a>'),
               ('<a href="#services">Services</a><a href="#about">About</a>',
                '<a href="#about">About</a><a href="#services">Services</a>')]:
    assert _a in src, _a
    src = src.replace(_a, _b)
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
<link rel="preload" href="/assets/font-cg-300.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/font-cg-300-i.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/font-dm-300.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/font-dm-400.woff2" as="font" type="font/woff2" crossorigin>
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

MENU_ITEMS = [('/', 'home', '01', 'Home', 'Welcome'),
              ('/about', 'about', '02', 'About', 'Mehreen &amp; the team'),
              ('/services', 'services', '03', 'Services', 'Packages &amp; pricing'),
              ('/design', 'design', '04', 'Design', 'Mood boards &amp; floor plans'),
              ('/contact', 'contact', '05', 'Contact Us', 'Start planning')]
def header():
    h = between(src, '<header class="site-header">', '</header>')
    h = relink(h, 'x')
    h = logo_use(h)
    h = h.replace('href="#home"', 'href="/"')
    # Design page (Tariq, Oct 25): in the main nav after Services
    h, n = re.subn(r'(<a href="/services" data-nav="services">Services</a>)', r'\1\n      <a href="/design" data-nav="design">Design</a>', h, count=1)
    assert n == 1
    # Phone menu v2 (Tariq, Oct 25): compact serif items with gold numerals and gold hairlines + one slim CTA
    mob = ('<nav id="mobnav" class="mobnav" hidden aria-label="Mobile"><div class="wrap mobnav-in">'
           '<ul class="mn-list">' + ''.join(
               '<li><a href="%s" data-nav="%s"><span class="mn-n">%s</span><span class="mn-t">%s</span></a></li>' % it[:4]
               for it in MENU_ITEMS) + '</ul>'
           '<div class="mn-foot"><a class="btn btn-gold btn-block" href="/contact#contact-form">Check availability</a></div>'
           '</div></nav>')
    h, n = re.subn(r'<nav id="mobnav".*?</nav>', mob, h, flags=re.S)
    assert n == 1
    # menu button: elegant hamburger (short middle line) that turns into a close X when open
    h, n = re.subn(r'(<button type="button" class="iconbtn" id="menuBtn"[^>]*>).*?(</button>)',
                   r'\1<svg class="ic-open" aria-hidden="true" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3 7h18M9 12h12M3 17h18"/></svg>'
                   r'<svg class="ic-close" aria-hidden="true" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M6 6l12 12M18 6L6 18"/></svg>\2', h, flags=re.S)
    assert n == 1
    return '<header class="site-header">' + h + '</header>\n'

def footer(page):
    # Footer v2 (Tariq, Oct 25): two tidy rows — brand + links, then a hairline with legal + contact;
    # centered and stacked on phones, split left/right on desktop
    links = [('/about', 'About'), ('/services', 'Services'), ('/design', 'Design'), ('/contact', 'Contact Us'),
             (IG, 'Instagram'), (FB, 'Facebook'), ('/privacy', 'Privacy')]
    f = ('<div class="wrap foot2">'
         '<div class="f2-top">'
           '<a class="lockup" href="/" aria-label="Miraj Events home"><svg class="lk-logo" width="110" height="75" viewBox="0 0 2386 1632" role="img" aria-label="Miraj Events monogram">'
           '<use href="/assets/sprite.svg?v=%s#me-mark" width="2386" height="1632"/></svg><span class="lk-name">MIRAJ EVENTS</span></a>'
           '<nav class="foot-links" aria-label="Footer">%s</nav>'
         '</div>'
         '<div class="f2-bottom">'
           '<span class="f2-contact"><a href="mailto:%s">%s</a><span class="f2-dot" aria-hidden="true">·</span><a href="tel:%s">%s</a></span>'
           '<span class="f2-legal">© <span id="yr">%s</span> Miraj Events, LLC · Metro Detroit, Michigan</span>'
         '</div>'
         '</div>') % (VERSION, ''.join('<a href="%s">%s</a>' % (u, t) for u, t in links), EMAIL, EMAIL, TEL, PHONE,
                      datetime.date.today().year)
    sticky = '<a class="sticky-cta" href="%s">Check availability</a>' % ('#inquire' if page in ('home', 'dayof') else '/contact#contact-form')
    return ('<footer class="rule-top">' + f + '</footer>\n' + sticky + '\n'
            '<script src="/assets/site.js?v=%s" defer></script>\n</body>\n</html>\n' % VERSION)

NODATE = '<label class="nodate"><input type="checkbox" data-nodate> No date yet</label>'
def nodate(h):
    """Date field: people without a date tick 'No date yet' (fills the field, so the inquiry still says so)."""
    h = h.replace('<label for="c-date">Event date(s) or season *</label><input id="c-date" name="event_date" type="text" placeholder="e.g. June 2027" required>',
                  '<label for="c-date">Event date or season *</label><input id="c-date" name="event_date" type="text" placeholder="e.g. June 2027" required>' + NODATE)
    h = h.replace('<label for="h-date">Event date or season</label><input id="h-date" name="event_date" type="text" placeholder="e.g. June 2027" autocomplete="off">',
                  '<label for="h-date">Event date or season</label><input id="h-date" name="event_date" type="text" placeholder="e.g. June 2027" autocomplete="off">' + NODATE)
    return h

def page(fname, title, desc, path, view, main_html, schema=(), noindex=False, extra_js=''):
    main_html = nodate(main_html)
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


def pic(name, alt, w, h, cls='', eager=False):
    # phones get a 600px file when one exists (assets__img-NAME-600.webp)
    ss = ''
    if os.path.exists(os.path.join(ASSETS_SRC, 'static', 'assets__img-%s-600.webp' % name)):
        ss = (' srcset="/assets/img-%s-600.webp 600w, /assets/img-%s.webp %dw" sizes="(max-width:700px) 72vw, (max-width:1240px) 34vw, 420px"'
              % (name, name, w))
    return ('<img class="%s" src="/assets/img-%s.webp"%s alt="%s" width="%d" height="%d"%s decoding="async">'
            % (cls, name, ss, esc(alt), w, h, '' if eager else ' loading="lazy"'))
def photo_strip(items):
    # items: (name, alt, title) or (name, alt, title, description)
    has_desc = any(len(it) > 3 for it in items)
    figs = ''
    for it in items:
        href = it[4] if len(it) > 4 else None
        title = ('<a href="%s">%s</a>' % (href, esc(it[2]))) if href else esc(it[2])
        cap = ('<strong>%s</strong><span>%s</span>' % (title, esc(it[3]))) if len(it) > 3 else title
        img = pic(it[0], it[1], 900, 1200)
        if href:
            img = '<a class="ps-link" href="%s" tabindex="-1" aria-hidden="true">%s</a>' % (href, img)
        figs += '<figure>%s<figcaption>%s</figcaption></figure>' % (img, cap)
    return '<div class="photo-strip%s reveal">' % (' has-desc' if has_desc else '') + figs + '</div>'
_ico = lambda d: '<svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="%s"/></svg>' % d
QUICK = ('<div class="ct4-quick">'
         '<a class="ct4-btn" href="tel:+15865040207">' + _ico('M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2z') + 'Call</a>'
         '<a class="ct4-btn" href="sms:+15865040207">' + _ico('M4 5h16v11H9l-5 4z') + 'Text</a>'
         '<a class="ct4-btn" href="https://wa.me/15865040207">' + _ico('M4 20l1.5-4A8 8 0 1 1 8 18.5L4 20z') + 'WhatsApp</a>'
         '</div>')
STEPS = ('<ol class="ct-steps"><li><span>1</span>We reply within 24 hours</li><li><span>2</span>A 30-minute call about your events</li>'
         '<li><span>3</span>Your customized package within 48 hours</li></ol>')
def inq_upgrade(h, slim=False):
    """Inquiry section v2 (Tariq, Oct 25): linen band, photo-backed heading on phones, Call/Text/WhatsApp buttons,
    what-happens-next steps, and an elevated white form card instead of a plain list + flat card."""
    h, n = re.subn(r'<div class="band band-white rule-top" id="inquire"><div class="wrap two-col" style="align-items:start">',
                   '<div class="band inq2%s" id="inquire"><div class="wrap inq2-grid">' % (' inq2-slim' if slim else ''), h, count=1)
    assert n == 1
    def left(m):
        if slim:  # Home (Tariq, Oct 25): heading + one line only; no steps, no call/text/WhatsApp boxes
            return ('<div class="inq2-head reveal"><p class="eyebrow">Contact us</p>' + m.group(1) +
                    '<p class="lead">Date in mind or still deciding? Either way, we&#8217;d love to hear from you.</p></div>')
        return ('<div class="inq2-head reveal"><p class="eyebrow">Contact us</p>' + m.group(1) +
                '<p class="lead">Have a date in mind or still deciding? Tell us a little about your plans and we&#8217;ll reply within 24 hours.</p>'
                + QUICK + STEPS + '</div>')
    h, n = re.subn(r'<div class="stack reveal">\s*<p class="eyebrow">Contact us</p>\s*(<h2 class="h2">.*?</h2>)\s*<ul class="contact-list">.*?</ul>\s*</div>',
                   left, h, count=1, flags=re.S)
    assert n == 1
    return h

# HOME
home = prep('home')
# Package ladder v2 (Tariq, Oct 25): segmented "what's included" meter instead of plain bars; spacing fixed;
# no prices on Home (Tariq, Oct 25); pricing lives on Services
LAYERS = ['The day', 'Design', 'Planning', 'All of it']
LADDER = [('01', 'Day-of Coordination', 'The final month and the day, setup to send-off.', '$1,975'),
          ('02', 'Design + Coordination', 'Adds design direction: concept, floor plan and décor team.', '$4,750'),
          ('03', 'Planning + Design', 'Adds planning from signing: vendors, budget, hotel block.', '$6,500'),
          ('04', 'Full Planning', 'All of it. You make the choices; we carry the rest.', '$9,500')]
def ladder2():
    rows = ''
    for i, (n, name, adds, price) in enumerate(LADDER):
        cells = ''.join('<span%s>%s</span>' % (' class="on"' if j <= i else '', LAYERS[j]) for j in range(4))
        tag = '<span class="tag">Most couples choose</span>' if n == '03' else ''
        rows += ('<li%s><div class="lad2-top"><span class="n">%s</span>%s</div><h3>%s</h3>'
                 '<div class="lad2-meter" aria-hidden="true">%s</div>'
                 '<p class="lad2-adds">%s</p></li>'
                 % (' class="is-pop"' if n == '03' else '', n, tag, esc(name), cells, esc(adds)))
    return '<ol class="lad2 reveal">' + rows + '</ol>\n    '
# Packages heading (Tariq, Oct 25): friendlier, flows better
_pk_old = ('<p class="eyebrow">Wedding planning services</p>\n      <h2 class="h2" style="font-size:clamp(28px,3.4vw,42px)">Four packages. Each includes the one before it.</h2>')
assert home.count(_pk_old) == 1
home = home.replace(_pk_old, '<p class="eyebrow">What we offer</p>\n      <h2 class="h2" style="font-size:clamp(28px,3.4vw,42px)">From the day itself to the whole weekend.</h2>'
                    '\n      <p class="lead pk-lead">Pick how much you&#8217;d like us to take on. Each package includes everything before it.</p>')
home, _n = re.subn(r'<div class="ladder reveal">.*?(?=<div class="pk-foot reveal">)', lambda m: ladder2(), home, count=1, flags=re.S)
assert _n == 1
home = home.replace('<p class="lead">Multicultural, multi-event weddings. One team.</p>', '<p class="lead">Wedding planning, design and day&#8209;of coordination for multicultural, multi&#8209;event weddings.</p>', 1)
home = home.replace('<span class="hp-logo">The Knot</span><span class="hp-logo">WeddingWire</span><span class="hp-logo">Bloomberg</span><span class="hp-logo">Voyage Michigan</span>', press_html('hp-logo'))
# Section order (Tariq, Oct 24): hero -> packages -> why Miraj -> weekend traditions -> proof/reviews -> inquire
_wk_i = home.index('<div class="band" id="weekend">')
_why_i = home.index('<div class="band band-white rule-top"><div class="wrap">\n    <div class="why-head')
_pk_i = home.index('<div class="band rule-top" id="packages">')
_pr_i = home.index('<div class="band band-dark proof">')
_wk, _why, _pk = home[_wk_i:_why_i], home[_why_i:_pk_i], home[_pk_i:_pr_i]
_wk = _wk.replace('<div class="band" id="weekend">', '<div class="band rule-top" id="weekend">', 1)
home = home[:_wk_i] + _pk + _why + _wk + home[_pr_i:]
# Hero eyebrow (Tariq, Oct 25): cities on their own line under "Wedding planner"
home = home.replace('<p class="eyebrow">Wedding planner · Detroit · Toledo · Chicago</p>',
                    '<div class="hero-ey"><p class="eyebrow">Wedding planner</p><p class="hero-cities">Detroit · Toledo · Chicago</p></div>', 1)
home = home.replace('<div class="hero">', '<div class="hero has-photo">', 1)
home = home.replace('<div class="hero-shade" aria-hidden="true"></div>',
    '<picture class="hero-photo" aria-hidden="true"><source media="(max-width:700px)" srcset="/assets/img-hero-sm.webp">'
    '<img src="/assets/img-hero-md.webp" srcset="/assets/img-hero-md.webp 1400w, /assets/img-hero-lg.webp 2400w" sizes="100vw" alt="" width="2400" height="1350" fetchpriority="high" decoding="async"></picture>'
    '<div class="hero-shade" aria-hidden="true"></div>', 1)
_strip = ('<div class="band band-white rule-top"><div class="wrap">' + photo_strip([
    ('stage-white', 'Sweetheart table with gold oval chairs before a wall of white blossoms', 'Design direction',
     'We shape the look with you and oversee the décor team that brings it to life.', '/design'),
    ('ballroom-chandeliers', 'Wood-paneled ballroom with crystal chandeliers and white round tables', 'Reception management',
     'From the grand entrance to the send-off, we run the timeline with your venue and vendors.'),
    ('details-gold', 'Place setting with a gold charger, blush napkin, place card and gold flatware', 'Focus on details',
     'Seating, ritual timing and the finishing touches, checked before your guests arrive.')]) + '</div></div>')
home = home.replace('<div class="band band-white rule-top"><div class="wrap">\n    <div class="why-head', _strip + '\n\n  <div class="band rule-top"><div class="wrap">\n    <div class="why-head', 1)
home = home.replace('<a class="rating" href="#" aria-label="Read our Google reviews"><span class="stars" aria-hidden="true">★</span><span>See our Google reviews →</span></a>',
                    '<a class="rating" href="#reviews" aria-label="Rated %.1f out of 5 on Google. Read reviews"><span class="stars" aria-hidden="true">★★★★★</span><span class="r-txt" aria-hidden="true"><strong>%.1f</strong> on Google</span></a>' % (reviews['rating'], reviews['rating']))
home = re.sub(r'<div class="proof-quote reveal">.*?</div>\s*</div></div>',
              '<div class="proof-quote reveal" id="reviews">' + reviews_block('home') + '</div>\n  </div></div>', home, flags=re.S)
page('index.html', 'Miraj Events | Detroit Wedding & Event Planning',
     'Miraj Events specializes in Detroit wedding and event planning, delivering polished, stress free celebrations from start to finish. Day-of coordination to full planning for multi-event weddings.',
     '/', 'home', inq_upgrade(slim=True, h=home.replace('<h2 class="h2">Let\'s check your date.</h2>', '<h2 class="h2">Let&#8217;s start planning your celebration.</h2>', 1)),
     schema=[org_schema(), {"@context": "https://schema.org", "@type": "WebSite", "name": "Miraj Events", "url": SITE + "/"}])

# SERVICES
svc = prep('services')
_sh_start = svc.index('<div class="svc-head reveal">')
_sh_end = svc.index('</div>', svc.index('<p class="lead">', _sh_start)) + len('</div>')
_svc_head = svc[_sh_start:_sh_end]
svc = svc[:_sh_start] + svc[_sh_end:]
svc = ('<section class="svc-hero">'
       '<picture class="svc-hero-photo" aria-hidden="true"><source media="(max-width:700px)" srcset="/assets/img-svc-sm.webp">'
       '<img src="/assets/img-svc-md.webp" srcset="/assets/img-svc-md.webp 1400w, /assets/img-svc-lg.webp 2400w" sizes="100vw" alt="" width="2400" height="1050" fetchpriority="high" decoding="async"></picture>'
       '<div class="svc-hero-shade" aria-hidden="true"></div>'
       '<div class="wrap svc-hero-inner">' + _svc_head.replace(' reveal', '') + '</div></section>\n') + svc
svc = svc.replace('<div class="band band-white rule-top rule-bottom"><div class="wrap">\n    <div class="hiw-head',
    '<div class="band"><div class="wrap">' + photo_strip([
        ('design-stage', 'White stage with a floral arch of ivory and blush roses, a curved loveseat and a crystal chandelier', 'Design direction',
         'Concept, floor plan and the décor team, from Design + Coordination up.', '/design'),
        ('ballroom-library', 'Library ballroom with chandelier, white tables and floral centerpieces', 'The run of show',
         'One timeline for every event, shared with every vendor and run on the day.'),
        ('white-florals', 'White floral centerpiece with taper candles and crystal glassware', 'Finishing touches',
         'Linens, chairs, backdrops and staging, delivered, set up and picked up.')]) + '</div></div>\n\n  <div class="band band-white rule-top rule-bottom"><div class="wrap">\n    <div class="hiw-head', 1)
svc = svc.replace('<h1>Four packages. Each includes the one before it.</h1>',
                  '<h1>Wedding planning packages. Each includes the one before it.</h1>')
svc = svc.replace('<p class="lead">Starting prices for a single event. Multi-event weekends are packaged together on your call.</p>',
                  '<p class="lead">Day-of coordination to full planning in Metro Detroit, Toledo and Chicago. Starting prices for a single event; multi-event weekends are packaged together on your call.</p>')
svc = svc.replace('<h2>Day-of Coordination</h2>', '<h2><a href="/day-of-coordination">Day-of Coordination</a></h2>')
svc = svc.replace('<a class="textlink" href="/contact">Tell us about yours →</a>', '<a class="textlink" href="/contact#contact-form">Tell us about yours →</a>')
# FAQ cut to 8 key questions (Tariq, Oct 25); cancel + postpone merged into one answer
_faq_items = {html.unescape(re.sub(r'<[^>]+>', '', m.group(1))).strip(): m.group(0)
              for m in re.finditer(r'<details[^>]*><summary>(.*?)</summary>.*?</details>', svc, re.S)}
assert len(_faq_items) == 12, len(_faq_items)
_merged = ('<details><summary>What if we need to postpone or cancel?</summary><p class="ans">We know plans change. Postponing is free: '
           'everything you&#8217;ve paid moves to your new date, as long as it&#8217;s within 12 months. If you cancel, the retainer is '
           'non-refundable; more than 90 days out we keep what&#8217;s been paid to date, and within 90 days the full fee is due.</p></details>')
_keep = ['Can you run our whole wedding weekend?', "We've already booked our venue and caterer. Can you take it from here?",
         'Do you plan weddings that blend two cultures or faiths?', 'Do you help with design?', 'How do payments work?',
         None, 'Do you travel?', 'Do you do events other than weddings?']
_new_faq = '\n'.join(_merged if k is None else _faq_items[k] for k in _keep)
_all = list(re.finditer(r'<details[^>]*><summary>.*?</details>', svc, re.S))
svc = svc[:_all[0].start()] + _new_faq + svc[_all[-1].end():]
_dc = 'The look: concept, floor plan, décor team and the install. Décor is billed by the vendor.</p></div>'
assert svc.count(_dc) == 1
svc = svc.replace(_dc, _dc + '\n        <a class="textlink pk-link" href="/design">See design direction &#8594;</a>')
_dq = 'and oversee the décor team that brings it to life. Décor itself is billed by the vendor.</p></details>'
assert svc.count(_dq) == 1
svc = svc.replace(_dq, 'and oversee the décor team that brings it to life. Décor itself is billed by the vendor. <a href="/design">See how design direction works</a>.</p></details>')
page('services.html', 'Wedding Planning Services & Pricing | Miraj Events Detroit',
     'Day-of coordination from $1,975, design + coordination, planning + design and full wedding planning in Metro Detroit, Toledo and Chicago. Multi-event wedding weekends packaged together.',
     '/services', 'services', svc, schema=[services_schema(), faq_schema(svc)])

# ABOUT
ab = prep('about')
ab = ab.replace('<span class="logo-slot">The Knot</span><span class="logo-slot">WeddingWire</span><span class="logo-slot">Bloomberg</span><span class="logo-slot">Voyage Michigan</span>', press_html('logo-slot'))
ARTICLES = [
    ('Peerspace', 'Top wedding planners in Detroit', 'Ranked #2 · Ranking', PRESS[2][1]),
    ('Voyage Michigan', 'Meet Mehreen Buksh of Miraj Events', 'Interview · How Mehreen got started and what sets Miraj apart', PRESS[1][1]),
    ('Bloomberg', 'Stock market drop has couples cutting wedding costs', 'April 2025 · Feature', PRESS[0][1]),
    ('Shoutout Michigan', 'Meet Mehreen Buksh, founder and lead coordinator', 'Interview', 'https://shoutoutmichigan.com/meet-mehreen-buksh-founder-lead-coordinator/'),
    ('CanvasRebel', 'Meet Mehreen Buksh', 'Interview', 'https://canvasrebel.com/meet-mehreen-buksh/'),
]
# Press v2 (Tariq, Oct 25): Peerspace #2 and Bloomberg featured on top, three interviews below
press_list = ('<div class="band ab3-linen ab3-press" id="press"><div class="wrap">'
              '<div class="ab3-press-head reveal"><p class="eyebrow">Press</p><h2 class="h2">In the news.</h2>'
              '<p class="lead">Ranked #2 among Detroit wedding planners by Peerspace, featured in Bloomberg, and interviewed by Michigan&#8217;s local press.</p></div>'
              '<div class="press-grid reveal">' + ''.join(
                  '<a class="press-card%s" href="%s" target="_blank" rel="noopener"><span class="pc-outlet">%s</span>%s'
                  '<span class="pc-title">%s</span><span class="pc-meta">%s</span><span class="pc-read">Read%s &#8594;</span></a>'
                  % (' feat dark' if i == 0 else (' feat' if i == 1 else ''), esc(u), esc(o), '<span class="pc-big">#2</span>' if o == 'Peerspace' else '',
                     esc(t), esc(m), (' on ' + esc(o)) if i < 2 else '')
                  for i, (o, t, m, u) in enumerate(ARTICLES))
              + '</div></div></div>')
# About layout v4 (Tariq, Oct 25): photo hero with stats; Meet the founder (bio) on linen; team on dark;
# design direction on ivory (replaces How we work); press cards on linen; dark CTA band
MONO = '<svg viewBox="0 0 2386 1632" aria-hidden="true" focusable="false"><use href="/assets/sprite.svg?v=%s#me-mark" width="2386" height="1632"/></svg>' % VERSION
def team_fig(name, alt, cap, w=900, h=1200):
    return '<figure>%s<figcaption>%s</figcaption></figure>' % (pic(name, alt, w, h), esc(cap))
ab = (
'<section class="ab3-hero">'
  '<picture class="ab3-photo" aria-hidden="true"><source media="(max-width:700px)" srcset="/assets/img-about-sm.webp">'
  '<img src="/assets/img-about-md.webp" srcset="/assets/img-about-md.webp 1400w, /assets/img-about-lg.webp 2400w" sizes="100vw" alt="" width="2400" height="1200" fetchpriority="high" decoding="async"></picture>'
  '<div class="ab3-shade" aria-hidden="true"></div>'
  '<div class="wrap ab3-inner">'
    '<div class="ab3-copy">'
      '<p class="eyebrow">About Miraj Events</p>'
      '<h1>An experienced lead planner, on <em>every</em> event.</h1>'
      '<p class="lead">Founded and led by Mehreen Buksh, Miraj Events plans, designs and runs weddings across Metro Detroit, Toledo and Chicago.</p>'
      '<div class="actions"><a class="btn btn-gold" href="/contact#contact-form">Check your date</a><a class="btn btn-ivory" href="/services">Services &amp; pricing</a></div>'
    '</div>'
    '<dl class="ab3-stats">'
      '<div><dt>50+</dt><dd>Multicultural, multi-event weddings in the past two years</dd></div>'
      '<div><dt>900+</dt><dd>Guests at our largest event</dd></div>'
      '<div><dt>#2</dt><dd>Detroit wedding planner, ranked by Peerspace</dd></div>'
      '<div><dt>1:100</dt><dd>Assistants to guests on every event</dd></div>'
    '</dl>'
  '</div>'
'</section>'
'<div class="band ab3-founder"><div class="wrap ab3-fgrid">'
  '<figure class="ab-portrait reveal" data-photo="mehreen">'
    '<div class="ab-ph has-img">' + pic('mehreen', 'Mehreen Buksh, founder and lead planner of Miraj Events', 1000, 1250) + '</div>'
    '<figcaption><strong>Mehreen Buksh</strong><span>Founder &amp; lead planner</span></figcaption>'
  '</figure>'
  '<div class="ab3-story reveal">'
    '<p class="eyebrow">Meet the founder</p>'
    '<h2 class="h2">More than a decade of <em>planning</em>.</h2>'
    '<p>Mehreen Buksh has been planning events for more than ten years. She started young, organizing youth and community events (booking speakers, building timelines and managing budgets) and went on to lead community, public, private and corporate events before focusing on weddings.</p>'
    '<p>Couples know her for a calm presence, a sharp eye for detail and a habit of solving problems before anyone notices them. She works with a trusted network of vendors across Michigan.</p>'
    '<p>Today her specialty is the multi-event wedding weekend: South Asian, Arab and Chaldean, Hindu and Sikh, West African and interfaith celebrations, often across several days and two faiths. We also run engagement parties, nonprofit galas and milestone celebrations.</p>'
  '</div>'
'</div></div>'
'<div class="band band-dark ab3-team" id="team"><div class="wrap">'
  '<div class="ab3-team-head reveal">'
    '<p class="eyebrow">The team</p>'
    '<h2 class="h2">A Miraj team on every event.</h2>'
    '<p class="lead">We take a limited number of weddings each season, so every event has a lead planner and one assistant per 100 guests, on site from setup to send-off.</p>'
    '<p class="ab3-team-sub">Vendors, venue and family stay on one timeline, and problems are solved before they reach you.</p>'
  '</div>'
  '<div class="photo-strip ab3-strip reveal">'
    + team_fig('team-c', 'Mehreen Buksh with a Miraj Events coordinator, both in uniform with name badges', 'Mehreen with the team', 675, 900)
    + '<figure class="wide">' + pic('team-group', 'The Miraj Events team in black uniforms with gold name badges at a venue', 1800, 1200)
    + '<figcaption>The Miraj team</figcaption></figure>'
    + team_fig('team-a', 'Two Miraj Events team members on site in a vaulted venue hall, one on headset', 'On site, on headset') +
  '</div>'
'</div></div>'
'<div class="band ab3-dslim-band" id="design-direction"><div class="wrap ab3-dslim reveal">'
  '<div><p class="eyebrow">Design direction</p><h2 class="h2">Professional design <em>direction</em>.</h2></div>'
  '<div class="ab3-dslim-txt"><p class="lead">From Design + Coordination up, we shape the look of your celebration with you, from colors and centerpieces to the stage, and direct the décor team that brings it to life.</p>'
    '<a class="textlink" href="/design">See design direction &#8594;</a></div>'
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

# DESIGN (Tariq, Oct 25): standalone Design direction page, from the approved sample
def dzimg(name, alt, w, h, small=None, sizes='', eager=False):
    ss = (' srcset="/assets/img-%s-%d.webp %dw, /assets/img-%s.webp %dw" sizes="%s"' % (name, small, small, name, w, sizes)) if small else ''
    return ('<img src="/assets/img-%s.webp"%s alt="%s" width="%d" height="%d"%s decoding="async">'
            % (name, ss, esc(alt), w, h, '' if eager else ' loading="lazy"'))
DZ_STEPS = [('01', 'Discover', 'Your story, venue, guest count and the feel you want.'),
            ('02', 'Concept', 'A mood board and palette to react to and refine.'),
            ('03', 'Plan', 'Floor plan, stage and tables, drawn to your room.'),
            ('04', 'Install', 'We brief the décor team and oversee setup.')]
DZ_MOOD = [('dz-mood-1', 'Candlelit table with white florals and gold votives'),
           ('dz-mood-2', 'Ivory benches beneath a soft blush drape'),
           ('dz-mood-3', 'Crystal chandeliers over a wood-paneled ballroom'),
           ('dz-mood-4', 'Gold beaded charger with a blank place card and greenery')]
DZ_PALETTE = [('#F6F1E7', 'Ivory'), ('#E7D9BF', 'Champagne'), ('#E6CFC4', 'Blush'), ('#A8873C', 'Antique gold'), ('#A3AE95', 'Sage')]
DZ_NOTES = [('Feel', 'Warm, candlelit and quietly grand.'), ('Stage', 'Soft ivory drape and a full floral arch.'),
            ('Tables', 'Gold chargers, ivory linen, taper candles.'), ('Florals', 'White garden roses and greenery, kept low.'),
            ('Lighting', 'Warm uplighting; candlelight on every table.')]
DZ_WHY = [('Stage faces the entrance,', 'so it&#8217;s the first thing guests see.'),
          ('Dance floor in the middle,', 'with every table close to the action.'),
          ('Bar and desserts at the back', 'keep the stage clear for photos.'),
          ('One clear aisle', 'from the door to the dance floor.')]
DZ_MOODS = [('Ceremony', 'Soft florals and a calm, intimate setting.', [('#F6F1E7', 'Ivory'), ('#E6CFC4', 'Blush'), ('#A3AE95', 'Sage'), ('#C6A15A', 'Gold')]),
            ('Reception', 'Candlelight, crystal and a statement stage.', [('#E7D9BF', 'Champagne'), ('#A8873C', 'Gold'), ('#F6F1E7', 'Ivory'), ('#2C2E31', 'Charcoal')]),
            ('Mehndi &amp; sangeet', 'Bold color, floor seating and room to dance.', [('#E3A23B', 'Marigold'), ('#C23F78', 'Fuchsia'), ('#1F5C4B', 'Emerald'), ('#F6F1E7', 'Ivory')]),
            ('Gala', 'Clean lines, a branded stage, room for the program.', [('#1F2A44', 'Navy'), ('#C6A15A', 'Gold'), ('#FFFFFF', 'White'), ('#8A929C', 'Slate')])]
DZ_WORK = [('dz-stage', 'White stage with a floral arch of ivory and blush roses, a curved loveseat and a crystal chandelier', 'Floral stage', 'White arches, ivory and blush roses'),
           ('dz-florals', 'Cascading ivory and blush roses around white arches beside an ivory chair', 'Floral installation', 'Garden roses, full and cascading'),
           ('dz-ceremony', 'Gold and ivory chair framed by white florals against soft gray drape', 'Ceremony seating', 'Ivory and gold, framed in white blooms'),
           ('dz-candles', 'Clusters of pillar candles in tall glass among white flowers', 'Candlelight', 'Clustered pillars in glass'),
           ('dz-tables', 'Round table with burgundy napkins, gold candleholders and a framed table number by tall windows', 'Tablescapes', 'Burgundy, gold and taper candles'),
           ('dz-room', 'Ballroom set with gold chairs, ivory linen and candlelit tables beneath a chandelier', 'Room setup', 'Gold chairs, ivory linen, crystal'),
           ('dz-lounge', 'Velvet lounge sofa on a rug beneath a tall arched window with floral stands', 'Lounge seating', 'Velvet and a grand arched window'),
           ('dz-centerpiece', 'Tall garden-style centerpiece with lilies and trailing amaranthus on a long table', 'Centerpieces', 'Tall, garden-style arrangements')]
_tb = ''.join('<use href="#dztb" x="%d" y="%d" width="42" height="42"/>' % (cx - 21, cy - 21)
              for cx in (36, 84, 276, 324) for cy in (106, 156, 206, 256, 306))
DZ_PLAN = (
 '<svg class="dz-plan" viewBox="0 0 360 480" role="img" aria-labelledby="dzPlanT">'
 '<title id="dzPlanT">Sample reception floor plan: the stage faces the entrance, the dance floor is in the center with twenty round tables on both sides, and the bar, dessert table, photo booth and welcome table sit at the back.</title>'
 '<defs><pattern id="dzdf" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M10 0H0V10" fill="none" stroke="#E2D6BF" stroke-width=".7"/></pattern>'
 '<symbol id="dztb" viewBox="-21 -21 42 42"><g fill="#FCFAF6" stroke="#BCA77C" stroke-width=".9">'
 '<circle cx="0" cy="-17" r="3.3"/><circle cx="12" cy="-12" r="3.3"/><circle cx="17" cy="0" r="3.3"/><circle cx="12" cy="12" r="3.3"/>'
 '<circle cx="0" cy="17" r="3.3"/><circle cx="-12" cy="12" r="3.3"/><circle cx="-17" cy="0" r="3.3"/><circle cx="-12" cy="-12" r="3.3"/></g>'
 '<circle r="11.5" fill="#F3ECDD" stroke="#A8873C" stroke-width="1"/></symbol></defs>'
 '<rect x="8" y="8" width="344" height="462" fill="#FBF8F2"/>'
 '<path d="M150 470H8V8H352V470H210" fill="none" stroke="#2C2E31" stroke-width="1.6"/><path d="M150 463v14M210 463v14" stroke="#2C2E31" stroke-width="1.6"/>'
 '<rect x="96" y="20" width="168" height="46" fill="#EFE4CF" stroke="#A8873C"/>'
 '<circle cx="110" cy="33" r="6.5" fill="#A3AE95"/><circle cx="119" cy="42" r="4.5" fill="#E6CFC4"/>'
 '<circle cx="250" cy="33" r="6.5" fill="#A3AE95"/><circle cx="241" cy="42" r="4.5" fill="#E6CFC4"/>'
 '<rect x="156" y="46" width="48" height="12" rx="3" fill="#FCFAF6" stroke="#A8873C"/><text x="180" y="37" class="lb">STAGE</text>'
 '<rect x="286" y="24" width="50" height="24" fill="#FCFAF6" stroke="#8C877E"/><text x="311" y="39.5" class="lb">DJ</text>'
 '<rect x="118" y="88" width="124" height="110" fill="#F4EEE2"/><rect x="118" y="88" width="124" height="110" fill="url(#dzdf)" stroke="#BCA77C"/>'
 '<circle cx="180" cy="137" r="18" fill="#FCFAF6" stroke="#A8873C"/><text x="180" y="141.5" class="mono">A&amp;J</text>'
 '<text x="180" y="184" class="lb">DANCE FLOOR</text>' + _tb +
 '<path d="M180 452V213" stroke="#A8873C" stroke-width="1.2" stroke-dasharray="3 4"/><path d="M175.5 214.5L180 206.5L184.5 214.5" fill="none" stroke="#A8873C" stroke-width="1.2"/>'
 '<rect x="20" y="360" width="104" height="22" fill="#FCFAF6" stroke="#8C877E"/><text x="72" y="374.5" class="lb">BAR</text>'
 '<rect x="236" y="360" width="104" height="22" fill="#FCFAF6" stroke="#8C877E"/><text x="288" y="374.5" class="lb">DESSERT</text>'
 '<rect x="20" y="412" width="88" height="32" fill="#FCFAF6" stroke="#8C877E"/><text x="64" y="431.5" class="lb">PHOTO BOOTH</text>'
 '<rect x="252" y="412" width="88" height="32" fill="#FCFAF6" stroke="#8C877E"/><text x="296" y="431.5" class="lb">WELCOME</text>'
 '<text x="180" y="461" class="lb">ENTRANCE</text>'
 '<g class="mk"><circle cx="96" cy="20" r="8"/><text x="96" y="23.4">1</text></g><g class="mk"><circle cx="242" cy="88" r="8"/><text x="242" y="91.4">2</text></g>'
 '<g class="mk"><circle cx="124" cy="360" r="8"/><text x="124" y="363.4">3</text></g><g class="mk"><circle cx="180" cy="300" r="8"/><text x="180" y="303.4">4</text></g>'
 '</svg>')
dz = (
'<section class="dz-hero">'
  '<picture class="dz-hero-photo" aria-hidden="true"><source media="(max-width:700px)" srcset="/assets/img-dz-hero-sm.webp">'
  '<img src="/assets/img-dz-hero-md.webp" srcset="/assets/img-dz-hero-md.webp 1400w, /assets/img-dz-hero-lg.webp 2400w" sizes="100vw" alt="" width="2400" height="1350" fetchpriority="high" decoding="async"></picture>'
  '<div class="dz-hero-shade" aria-hidden="true"></div>'
  '<div class="wrap dz-hero-inner"><div class="dz-hero-copy">'
    '<p class="eyebrow">Design direction</p>'
    '<h1>The look of your celebration, <em>designed</em> with you.</h1>'
    '<p class="lead">Concept, palette, floor plan and the d&eacute;cor team that brings it all to life.</p>'
    '<div class="actions"><a class="btn btn-gold" href="/contact#contact-form">Check your date</a><a class="btn btn-ivory" href="#work">See our work</a></div>'
  '</div></div>'
'</section>'
'<div class="band dz-band" id="how"><div class="wrap">'
  '<div class="dz-head reveal"><p class="eyebrow">How it works</p><h2 class="h2">From a feeling to a <em>finished room</em>.</h2></div>'
  '<ol class="dz-steps reveal">' + ''.join('<li><span class="n">%s</span><h3>%s</h3><p>%s</p></li>' % (n, t, esc(d)) for n, t, d in DZ_STEPS) + '</ol>'
'</div></div>'
'<div class="band dz-band dz-linen" id="brief"><div class="wrap">'
  '<div class="dz-head dz-center reveal"><p class="eyebrow">Sample design brief</p><h2 class="h2">What design direction looks like <em>on paper</em>.</h2></div>'
  '<article class="dz-brief reveal" aria-label="Sample design brief">'
    '<header class="dz-brief-head"><div><span class="dz-k">Design brief</span><p class="dz-brief-title">Reception &middot; Ivory &amp; antique gold</p></div><span class="dz-pill">Sample</span></header>'
    '<div class="dz-row">'
      '<div class="dz-cell"><span class="dz-k">Mood board</span><div class="dz-board">'
        + ''.join(dzimg(n, a, 640, 640) for n, a in DZ_MOOD) +
      '</div><p class="dz-note">Inspiration images</p></div>'
      '<div class="dz-cell"><span class="dz-k">Palette</span><ul class="dz-palette">'
        + ''.join('<li><i style="--c:%s"></i><b>%s</b><small>%s</small></li>' % (c, n, c) for c, n in DZ_PALETTE) +
      '</ul><span class="dz-k">Direction</span><dl class="dz-notes">'
        + ''.join('<div><dt>%s</dt><dd>%s</dd></div>' % (k, esc(v)) for k, v in DZ_NOTES) +
      '</dl></div>'
    '</div>'
    '<div class="dz-row">'
      '<div class="dz-cell"><span class="dz-k">Floor plan</span>' + DZ_PLAN + '</div>'
      '<div class="dz-cell dz-why-cell"><span class="dz-k">Why this layout</span><ol class="dz-why">'
        + ''.join('<li><span><strong>%s</strong> %s</span></li>' % (a, b) for a, b in DZ_WHY) +
      '</ol></div>'
    '</div>'
  '</article>'
'</div></div>'
'<div class="band dz-band" id="palettes"><div class="wrap">'
  '<div class="dz-head reveal"><p class="eyebrow">Event palettes</p><h2 class="h2">A different mood for <em>each event</em>.</h2></div>'
  '<div class="dz-moods reveal">' + ''.join(
      '<article class="dz-mood"><div class="bar" aria-hidden="true">%s</div><div class="tx"><h3>%s</h3><p>%s</p><small>%s</small></div></article>'
      % (''.join('<i style="--c:%s"></i>' % c for c, _ in cols), name, esc(line), ' &middot; '.join(n for _, n in cols))
      for name, line, cols in DZ_MOODS) + '</div>'
'</div></div>'
'<div class="band dz-band dz-linen" id="work"><div class="wrap">'
  '<div class="dz-head dz-center reveal"><p class="eyebrow">Our work</p><h2 class="h2">Rooms we&#8217;ve <em>designed</em>.</h2></div>'
  '<ul class="dz-gallery reveal">' + ''.join(
      '<li><figure><div class="ph">%s</div><figcaption><strong>%s</strong><span>%s</span></figcaption></figure></li>'
      % (dzimg(n, a, 800, 1000, 500, '(max-width:900px) 46vw, 280px'), esc(t), esc(d)) for n, a, t, d in DZ_WORK) + '</ul>'
  '<p class="dz-gal-note">All photos from Miraj events.</p>'
'</div></div>'
'<div class="band dz-band" id="included"><div class="wrap">'
  '<div class="dz-inc">'
    '<div class="reveal"><p class="eyebrow">What&#8217;s included</p><h2 class="h2">Included from <em>Design&nbsp;+&nbsp;Coordination</em> and up.</h2>'
      '<p class="dz-small">D&eacute;cor itself is billed by the vendor.</p>'
      '<a class="textlink" href="/services#design">See packages &amp; pricing &#8594;</a></div>'
    '<ul class="dz-inc-list reveal"><li>Concept &amp; mood board</li><li>Color palette</li><li>Floor plan &amp; stage layout</li>'
      '<li>D&eacute;cor team, briefed and directed</li><li>Install, overseen by us</li></ul>'
  '</div>'
  '<div class="dz-addons reveal"><span class="dz-k">Add-ons</span>'
    + ''.join('<span class="dz-chip">%s</span>' % c for c in ['Candy pop-up', 'Photobooth', 'Staging &amp; runways', 'Linens &amp; chairs', 'Backdrops']) +
    '<small>Add to any package. Delivery, setup and pickup included.</small></div>'
'</div></div>'
'<div class="band band-dark ab-cta dz-cta"><div class="wrap ab-cta-in">'
  '<div><h2 class="h2" style="font-size:clamp(28px,3.4vw,44px)">Let&#8217;s design <em>yours</em>.</h2>'
  '<p class="lead">Tell us the feel you want. We&#8217;ll take it from there.</p></div>'
  '<div class="actions"><a class="btn btn-gold" href="/contact#contact-form">Check your date</a><a class="btn btn-ivory" href="tel:+15865040207">Call (586) 504-0207</a></div>'
'</div></div>'
)
page('design.html', 'Wedding Design Direction in Detroit | Miraj Events',
     'Wedding design direction in Metro Detroit: concept, mood board, color palette, floor plan and a décor team we brief and direct. From Design + Coordination up.',
     '/design', 'design', dz, schema=[org_schema(), {
         "@context": "https://schema.org", "@type": "Service", "name": "Wedding design direction",
         "serviceType": "Wedding design and décor direction", "provider": {"@id": SITE + "/#business"},
         "areaServed": "Metro Detroit, Toledo and Chicago", "url": SITE + "/design",
         "description": "Concept, mood board, color palette, floor plan and décor team direction, included from the Design + Coordination package up."}])

# CONTACT
ct = prep('contact')
# Contact layout v2 (Oct 24): form above the fold; compact package strip; reviews below
_form = re.search(r'<form class="card form js-inquiry" id="contactForm".*?</form>', ct, re.S).group(0)
_tiers = ct[ct.index('<div class="tiers">'):ct.index('<p class="small" style="text-align:center;margin-top:16px">')]
# Contact layout v4.1 (Tariq, Oct 25): Google reviews as a light card below the photo (desktop: under the side photo;
# phones: under the photo heading); generic heading for people without a date;
# Call / Text / WhatsApp as simple buttons between the heading and the form; the current site's contact photo
# beside the form (desktop) or behind the heading (phones); warm linen instead of white
_ico = lambda d: '<svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="%s"/></svg>' % d
ct = (
'<section class="ct4" id="contact-form"><div class="wrap ct4-flat">'
  '<div class="ct4-head">'
    '<p class="eyebrow">Contact us</p>'
    '<h1>Let&#8217;s start planning <em>your</em> celebration.</h1>'
    '<p class="lead">Have a date in mind or still deciding? Tell us a little about your plans and we&#8217;ll reply within 24 hours.</p>'
    + QUICK +
  '</div>'
  + reviews_block('ct') +
  '<div class="ct-formwrap">'
    '<p class="ct-note">Package descriptions and starting prices are <a href="#packages-ct">below&nbsp;&darr;</a></p>'
    + _form +
  '</div>'
  '<figure class="ct4-photo"><img src="/assets/img-contact-side.webp" alt="Guests raising a toast at a candlelit long table in a wood-paneled dining room" width="1044" height="1200" loading="lazy" decoding="async"></figure>'
  '<div class="ct4-next">' + STEPS +
    '<p class="ct4-email">Prefer email? <a href="mailto:admin@mirajevent.com">admin@mirajevent.com</a></p>'
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
dayof = dayof.replace('{{REVIEWS}}', reviews_block('dayof')).replace('{{IMG}}', pic('head-table', 'Candlelit head table with draped linens and warm florals', 900, 1200, 'dayof-img'))
dayof_form = re.search(r'<div class="band band-white rule-top" id="inquire">.*?</div></div>', home, re.S).group(0)
dayof_form = dayof_form.replace('id="inquire"', 'id="inquire"').replace('<option>Wedding weekend (multiple events)</option><option>Wedding (single event)</option>',
                                                                        '<option>Wedding (single event)</option><option>Wedding weekend (multiple events)</option>')
dayof_form = dayof_form.replace('data-start="inquiry-start" novalidate>', 'data-start="inquiry-start" data-package="Day-of Coordination" novalidate>')
dayof = inq_upgrade(dayof.replace('{{FORM}}', dayof_form))
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
urls = [('/', '1.0'), ('/services', '0.9'), ('/day-of-coordination', '0.9'), ('/design', '0.8'), ('/contact', '0.8'), ('/about', '0.7'), ('/privacy', '0.2')]
open(os.path.join(OUT, 'sitemap.xml'), 'w').write(
    '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + ''.join('  <url><loc>%s%s</loc><lastmod>%s</lastmod><priority>%s</priority></url>\n' % (SITE, u if u != '/' else '/', today, p) for u, p in urls)
    + '</urlset>\n')
open(os.path.join(OUT, 'robots.txt'), 'w').write(
    'User-agent: *\nAllow: /\nDisallow: /thank-you\nDisallow: /netlify-forms.html\n\nSitemap: %s/sitemap.xml\n' % SITE)
llms = open(os.path.join(ASSETS_SRC, 'llms.txt'), encoding='utf-8').read()
open(os.path.join(OUT, 'llms.txt'), 'w').write(llms)
print('built', sorted(os.listdir(OUT)))
