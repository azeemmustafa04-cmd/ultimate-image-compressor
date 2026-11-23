"""Builds the size landing pages (compress-image-to-20kb.html etc.) from the main index.html."""
import json, re, shutil, sys
from pathlib import Path

SRC = Path('/home/claude/compressor/index.html')
OUT = Path('/home/claude/deploy')
BASE = 'https://unlimitedimagecompressor.vercel.app'
SIZES = [10, 20, 30, 50, 100, 200, 500, 1000]

html = SRC.read_text(encoding='utf-8')


def label(kb):
    return '1 MB' if kb == 1000 else f'{kb} KB'


def slug(kb):
    return 'compress-image-to-1mb' if kb == 1000 else f'compress-image-to-{kb}kb'


def uses(kb):
    if kb <= 50:
        return 'online forms, job and university applications, exam and visa portals'
    if kb <= 200:
        return 'online forms, applications, email attachments and website uploads'
    return 'websites, email, WhatsApp and uploads with a size limit'


GENERAL_FAQ = [
    ('Is it free?', 'Yes. It is free, needs no sign-up, adds no watermark, and has no limit on the number of images.'),
    ('Is my photo uploaded anywhere?', 'No. Everything runs inside your browser, so your photos never leave your device.'),
    ('Can I compress iPhone HEIC photos?', 'Yes. HEIC photos from iPhone and Samsung phones are opened in the browser and saved as JPG.'),
    ('Does it work on mobile phones?', 'Yes. It works in any modern browser on Android, iPhone, Windows and Mac.'),
]


def size_faq(kb):
    L = label(kb)
    return [
        (f'How do I compress an image to {L}?',
         f'Drop your photo on this page. The target is already set to {L}, so the tool finds the highest quality and size that fit under {L} and gives you a JPG to download.'),
        (f'Will a {L} photo look blurry?',
         f'To fit {L} the tool first lowers the JPG quality a little and, only if needed, the dimensions. It keeps quality at 60 or higher whenever possible and shows a similarity score for every photo, so you can check it before you download.'),
        (f'Can I compress many photos to {L} at once?',
         f'Yes. Drop as many photos or whole folders as you like. Every one comes out under {L}, and you can download them all as one ZIP file.'),
        (f'What if my photo is already smaller than {L}?',
         'Then it is returned untouched, so it never loses quality for no reason.'),
    ] + GENERAL_FAQ


def sub(pattern, repl, text, count=1):
    new, n = re.subn(pattern, repl, text, count=count, flags=re.S)
    if n != count:
        sys.exit(f'pattern not found: {pattern[:60]}')
    return new


def page(kb):
    L, s = label(kb), slug(kb)
    url = f'{BASE}/{s}'
    title = f'Compress Image to {L} Online, Free | Unlimited Image Compressor'
    desc = (f'Reduce any JPG, PNG, HEIC or WebP photo to {L} or less in seconds. Free, no upload, no sign-up, '
            f'and the best quality that fits in {L}. Ideal for {uses(kb)}.')
    lede = (f'Make any photo {L} or smaller for {uses(kb)}. It runs in your browser, so nothing is uploaded, '
            f'and every image keeps the best quality that fits in {L}.')
    faq = size_faq(kb)
    t = html
    t = sub(r'<html lang="en">', f'<html lang="en" data-target-kb="{kb}">', t)
    t = sub(r'<title>.*?</title>', f'<title>{title}</title>', t)
    t = sub(r'<meta name="description" content=".*?">', f'<meta name="description" content="{desc}">', t)
    t = sub(r'<link rel="canonical" href=".*?">', f'<link rel="canonical" href="{url}">', t)
    t = sub(r'<meta property="og:url" content=".*?">', f'<meta property="og:url" content="{url}">', t)
    t = sub(r'<meta property="og:title" content=".*?">', f'<meta property="og:title" content="Compress Image to {L}: free, no upload">', t)
    t = sub(r'<meta property="og:description" content=".*?">', f'<meta property="og:description" content="{desc}">', t)
    app = {
        '@context': 'https://schema.org', '@type': 'WebApplication', 'name': f'Compress Image to {L} (Unlimited Image Compressor)',
        'url': url, 'applicationCategory': 'MultimediaApplication', 'operatingSystem': 'Any (runs in the browser)',
        'browserRequirements': 'Requires a modern web browser', 'offers': {'@type': 'Offer', 'price': '0', 'priceCurrency': 'USD'},
        'description': desc, 'isPartOf': {'@type': 'WebSite', 'name': 'Unlimited Image Compressor', 'url': BASE + '/'},
    }
    faq_ld = {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
        {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in faq]}
    t = sub(r'<script type="application/ld\+json">\{"@context":"https://schema.org","@type":"WebApplication".*?</script>',
            '<script type="application/ld+json">' + json.dumps(app, ensure_ascii=False) + '</script>', t)
    t = sub(r'<script type="application/ld\+json">\{"@context":"https://schema.org","@type":"FAQPage".*?</script>',
            '<script type="application/ld+json">' + json.dumps(faq_ld, ensure_ascii=False) + '</script>', t)
    t = sub(r'<h1>.*?</h1>', f'<h1>Compress Image to {L}</h1>', t)
    t = sub(r'<p class="lede">.*?</p>', f'<p class="lede">{lede}</p>', t)
    # navigation: mark this page, add a link back to the main tool
    t = sub(r'<span>Need an exact size\?</span>', f'<a href="{BASE}/">All sizes</a>', t)
    t = sub(rf'<a href="{re.escape(url)}">', f'<a href="{url}" aria-current="page">', t)
    faq_html = '\n'.join(f'      <div><h3>{q}</h3><p>{a}</p></div>' for q, a in faq)
    t = sub(r'(<section class="faq" aria-labelledby="faq-title">\s*<h2 id="faq-title">).*?(</h2>\s*<div class="faq-grid">).*?(</div>\s*</section>)',
            lambda m: m.group(1) + f'Compress to {L}: questions' + m.group(2) + '\n' + faq_html + '\n    ' + m.group(3), t)
    return s, t


OUT.mkdir(exist_ok=True)
shutil.copy(SRC, OUT / 'index.html')
urls = [BASE + '/']
for kb in SIZES:
    s, t = page(kb)
    (OUT / f'{s}.html').write_text(t, encoding='utf-8')
    urls.append(f'{BASE}/{s}')
sitemap = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for i, u in enumerate(urls):
    sitemap += ['  <url>', f'    <loc>{u}</loc>', '    <lastmod>2026-11-23</lastmod>', '    <changefreq>weekly</changefreq>',
                f'    <priority>{"1.0" if i == 0 else "0.8"}</priority>', '  </url>']
sitemap.append('</urlset>')
(OUT / 'sitemap.xml').write_text('\n'.join(sitemap) + '\n', encoding='utf-8')
print('\n'.join(urls))
