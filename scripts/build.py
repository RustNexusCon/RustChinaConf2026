#!/usr/bin/env python3
"""Build index.html, the bilingual RustChinaConf 2026 agenda page.

Talks come from the speaker tables in data/talks-zh.md and data/talks-en.md (same rows, same order).
Fixed schedule items (Day 0, opening, breaks, lunch, closing) live in src/template.html.
Speaker photos (assets/speakers/<name>.jpg) and the key visual (assets/kv.jpg) are embedded as data URIs,
so the output is a single self-contained file.

Usage: python3 scripts/build.py [--fragment PATH]
  --fragment  also write the page without <html>/<head>/<body> (for hosts that add their own skeleton)
"""
import argparse, base64, json, os, re, shutil, subprocess, sys, tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AVATAR_PX, AVATAR_Q = 240, 72

TAGS = [  # (tag, zh title prefix, en title prefix) — prefix is stripped and shown as a badge instead
    ('keynote', r'^K\d+ · ', r'^K\d+ · '),
    ('demo', r'^特别演示 · ', r'^Special Demo · '),
    ('lightning', r'^⚡ ', r'^⚡ '),
    ('panel', r'^🔥 圆桌讨论：', r'^🔥 Panel: '),
    ('fireside', r'^炉边对话：', r'^Fireside Chat: '),
]


def rows(path):
    out, day = [], None
    for line in open(path, encoding='utf-8'):
        if line.startswith('## Day 1'):
            day = 1
        elif line.startswith('## Day 2'):
            day = 2
        if not day or not line.startswith('| ') or line.startswith('| 时间') or line.startswith('| Time'):
            continue
        cells = [c.strip() for c in line.strip().replace('\\|', '¦').strip('|').split('|')]
        if len(cells) >= 8:
            out.append((day, cells))
    return out


def norm_time(s):
    return re.sub(r'\s*[-–]\s*', '–', s)


def br(s):
    return [p.strip() for p in s.split('<br>')]


def parse_talks():
    zh_rows = rows(os.path.join(REPO, 'data/talks-zh.md'))
    en_rows = rows(os.path.join(REPO, 'data/talks-en.md'))
    if len(zh_rows) != len(en_rows):
        sys.exit(f'zh/en tables differ in length: {len(zh_rows)} vs {len(en_rows)}')
    talks = []
    for i, ((day, z), (day2, e)) in enumerate(zip(zh_rows, en_rows)):
        time = norm_time(z[0])
        if day != day2 or time != norm_time(e[0]):
            sys.exit(f'row {i}: zh/en mismatch ({day} {time} vs {day2} {e[0]})')
        track = 'P' if z[1] in ('主会场', 'Plenary') else z[1][:2]
        tz, te = z[4].strip('*'), e[4].strip('*')
        tag = None
        for name, pz, pe in TAGS:
            if re.match(pz, tz):
                tag, tz, te = name, re.sub(pz, '', tz), re.sub(pe, '', te)
                break
        avs = [a for a in re.findall(r'讲师头像/([^¦\]]+?)\.(?:jpe?g|png)', z[2])]
        names_z, names_e = br(z[3]), br(e[3])
        host = None
        if names_z[0].startswith('主持'):  # panel: moderator only
            host = {'zh': names_z[0], 'en': names_e[0]}
            names_z, names_e = [], []
        elif len(names_z) > 1:  # speaker<br>moderators
            host = {'zh': names_z[1], 'en': names_e[1]}
            names_z, names_e = names_z[:1], names_e[:1]
        speakers = []
        if names_z:
            nz, ne = names_z[0].split(' + '), names_e[0].split(' + ')
            rz, ren = br(z[6]), br(e[6])
            for j, (a, b) in enumerate(zip(nz, ne)):
                speakers.append({'name': {'zh': a, 'en': b},
                                 'role': {'zh': re.sub(r'^\w+：', '', rz[j] if j < len(rz) else ''),
                                          'en': re.sub(r'^\w+: ', '', ren[j] if j < len(ren) else '')},
                                 'bio': {'zh': z[7], 'en': e[7]},
                                 'av': avs[j] if j < len(avs) else None})
        if len(speakers) == 2:  # Kevin Boos + Gregory Terzian share one bio cell
            speakers[0]['bio'] = {'zh': 'Futurewei 首席架构师、Theseus OS 创始人、Robius 项目技术负责人。',
                                  'en': 'Chief Architect at Futurewei, creator of Theseus OS, and technical lead of the Robius project.'}
            speakers[1]['bio'] = {'zh': 'Servo 贡献者，Formal Web 开发者。',
                                  'en': 'Servo contributor and developer of Formal Web.'}
        slot = time.split('–')[0]
        talks.append({'id': f'd{day}-{track}-{time[:5].replace(":", "")}-{i}', 'day': day, 'time': time,
                      'slot': slot, 'track': track, 'tag': tag,
                      'title': {'zh': tz, 'en': te}, 'abs': {'zh': z[5], 'en': e[5]},
                      'speakers': speakers, 'host': host})
    # consecutive lightning talks in one track share a single grid slot, starting with the first of them
    for k in talks:
        if k['tag'] == 'lightning':
            k['slot'] = min(x['slot'] for x in talks if x['tag'] == 'lightning' and x['day'] == k['day'] and x['track'] == k['track'])
    return talks


def shrink(src, dst):
    """Downscale a photo to AVATAR_PX with sips (macOS) or Pillow; fall back to the original."""
    if shutil.which('sips'):
        r = subprocess.run(['sips', '-s', 'format', 'jpeg', '-s', 'formatOptions', str(AVATAR_Q),
                            '--resampleHeightWidthMax', str(AVATAR_PX), src, '--out', dst], capture_output=True)
        if r.returncode == 0:
            return dst
    try:
        from PIL import Image
        im = Image.open(src).convert('RGB')
        im.thumbnail((AVATAR_PX, AVATAR_PX))
        im.save(dst, 'JPEG', quality=AVATAR_Q)
        return dst
    except ImportError:
        return src


def data_uri(path):
    return 'data:image/jpeg;base64,' + base64.b64encode(open(path, 'rb').read()).decode()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--fragment', help='also write a skeleton-less copy to this path')
    args = ap.parse_args()

    talks = parse_talks()
    used = sorted({s['av'] for k in talks for s in k['speakers'] if s['av']})
    photos = {a: os.path.join(REPO, 'assets/speakers', a + '.jpg') for a in used}
    missing = [p for p in photos.values() if not os.path.exists(p)]
    if missing:
        sys.exit('missing speaker photos:\n  ' + '\n  '.join(missing))
    with tempfile.TemporaryDirectory() as tmp:
        AV = {a: data_uri(shrink(p, os.path.join(tmp, a + '.jpg'))) for a, p in photos.items()}

    tpl = open(os.path.join(REPO, 'src/template.html'), encoding='utf-8').read()
    frag = (tpl.replace('/*__DATA__*/', 'const TALKS=' + json.dumps(talks, ensure_ascii=False) + ';\nconst AV=' + json.dumps(AV) + ';')
            .replace('__KV__', data_uri(os.path.join(REPO, 'assets/kv.jpg'))))
    if args.fragment:
        open(args.fragment, 'w', encoding='utf-8').write(frag)

    i = frag.index('</style>') + len('</style>')
    head = frag[:i].replace('<title>', '<meta name="description" content="RustChinaConf 2026 深圳 · 10 月 15–17 日 · 中英双语大会议程 / Bilingual schedule for RustChinaConf 2026 in Shenzhen, Oct 15–17.">\n'
                            '<meta property="og:title" content="RustChinaConf 2026 议程 / Schedule">\n'
                            '<meta property="og:description" content="深圳南山伊敦酒店 · 与 GOSIM Shenzhen 2026 同期举办 · Co-located with GOSIM Shenzhen 2026">\n<title>', 1)
    out = os.path.join(REPO, 'index.html')
    open(out, 'w', encoding='utf-8').write('<!doctype html>\n<html lang="zh-CN">\n<head>\n' + head + '\n</head>\n<body>\n' + frag[i:].strip() + '\n</body>\n</html>\n')
    print(f'{len(talks)} talks, {len(AV)} photos, {os.path.getsize(out) / 1024:.0f} KB -> {out}')


if __name__ == '__main__':
    main()
