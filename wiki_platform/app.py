#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jerry Wiki Platform
"""
import os, re, markdown2 as markdown, time, threading
from flask import Flask, render_template, request, abort
from collections import defaultdict

WIKI_ROOT = "/Volumes/256G/gesila_wiki"
SUBDIRS = {
    "02_Knowledge/概念卡": "概念卡",
    "02_Knowledge/方法论": "方法论",
    "02_Knowledge/案例库": "案例库",
    "02_Knowledge/项目复盘": "项目复盘",
    "03_Output": "03_Output",
    "01_Inbox": "01_Inbox",
}

app = Flask(__name__)
app.config['SECRET_KEY'] = 'jerry-wiki-2026'

# ── Cache ──────────────────────────────────────────────────────────────────
_cache = {'cards': [], 'graph': {}, 'loaded_at': 0, 'file_mtimes': {}}
_cache_lock = threading.RLock()
_rebuilding = False

def _mtime(path):
    try:
        return os.stat(path).st_mtime
    except OSError:
        return 0

def _scan_mtimes():
    """Collect mtime of all .md files."""
    mtimes = {}
    for subpath in SUBDIRS:
        d = os.path.join(WIKI_ROOT, subpath)
        if not os.path.exists(d):
            continue
        for root, _, files in os.walk(d):
            for f in files:
                if f.endswith('.md'):
                    mtimes[os.path.join(root, f)] = _mtime(os.path.join(root, f))
    return mtimes

def _files_changed(old_mtimes, new_mtimes):
    """Return True if any file was added/deleted/modified."""
    if set(old_mtimes) != set(new_mtimes):
        return True
    for k, v in new_mtimes.items():
        if old_mtimes.get(k) != v:
            return True
    return False

def get_cards(force_refresh=False):
    global _cache, _rebuilding
    now = time.time()

    with _cache_lock:
        if not force_refresh:
            new_mtimes = _scan_mtimes()
            if (_cache['cards']
                    and not _files_changed(_cache['file_mtimes'], new_mtimes)
                    and now - _cache['loaded_at'] < 3600):
                return _cache['cards']
            elif _rebuilding:
                return _cache['cards']

        if not _rebuilding:
            _rebuilding = True
            threading.Thread(target=_rebuild_cache, args=(new_mtimes if '_scan_mtimes' in locals() else _scan_mtimes(),), daemon=True).start()

    return _cache['cards']

def _rebuild_cache(file_mtimes):
    """Background rebuild — runs outside the request thread."""
    global _cache, _rebuilding
    cards = _load_cards()
    graph = _build_graph(cards)
    with _cache_lock:
        _cache['cards'] = cards
        _cache['graph'] = graph
        _cache['loaded_at'] = time.time()
        _cache['file_mtimes'] = file_mtimes
        _rebuilding = False
    print(f"[cache] Rebuilt: {len(cards)} cards, {len(graph.get('nodes',[]))} nodes")

def _load_cards():
    cards = []
    for subpath, cat in SUBDIRS.items():
        d = os.path.join(WIKI_ROOT, subpath)
        if not os.path.exists(d):
            continue
        for root, _, files in os.walk(d):
            for f in sorted(files):
                if not f.endswith('.md'):
                    continue
                path = os.path.join(root, f)
                slug = f.replace('.md', '')
                try:
                    with open(path, 'r', encoding='utf-8') as fh:
                        text = fh.read()
                except:
                    continue
                title = extract_title(text, slug)
                tags = extract_tags(text)
                date_m = re.search(r'(\d{4}-\d{2}-\d{2})', f)
                date = date_m.group(1) if date_m else ''
                summary = extract_summary(text)
                cards.append(dict(slug=slug, path=path, title=title, tags=tags,
                                  category=cat, date=date, summary=summary, raw=text))
    return cards

# ── Helpers ─────────────────────────────────────────────────────────────────
def extract_title(text, fallback):
    for line in text.split('\n'):
        line = line.strip()
        if line.startswith('# '):
            return line[2:].strip()
        if line.startswith('## '):
            return line[3:].strip()
    return fallback

def extract_tags(text):
    tags = []
    for line in text.split('\n'):
        if '**标签**' not in line and '标签：' not in line and 'Tags：' not in line:
            continue
        idx = line.find('\uff1a')  # fullwidth colon
        if idx < 0:
            idx = line.find(':')
        if idx < 0:
            continue
        tag_part = line[idx+1:]
        parts = re.split(r'\u00d7', tag_part)  # ×
        for p in parts:
            p = p.strip().strip('*# \t')
            if len(p) > 1:
                tags.append(p)
        break
    return tags

def extract_summary(text, maxlen=180):
    lines = text.split('\n')
    parts, count = [], 0
    skip_words = ('#', '**', '标签', '来源', '作者', '状态', '---', 'Tags',
                  '==', '**标签', '**来源', '**作者', '**状态')
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if any(line.startswith(w) for w in skip_words):
            continue
        parts.append(line)
        count += 1
        if count >= 3:
            break
    s = ' '.join(parts)
    return s[:maxlen] + ('...' if len(s) > maxlen else '')

def render_card(card, all_cards):
    title_map = {c['title']: c for c in all_cards}
    html = markdown.markdown(card['raw'], extras=['tables', 'fenced_code'])
    for title, c in title_map.items():
        if title != card['title']:
            html = html.replace(
                '>' + title + '<',
                '><a href="/card/' + c['slug'] + '" class="wiki-link">' + title + '</a><'
            )
    return html

def _build_graph(cards):
    nodes, edges = [], []
    edge_set = set()
    tag_index = defaultdict(list)
    topic_index = defaultdict(list)

    layer_map = {
        '01_Inbox': 0,
        '概念卡': 1, '方法论': 1, '案例库': 1, '项目复盘': 1,
        '03_Output': 2,
    }

    for c in cards:
        for t in c['tags']:
            tag_index[t].append(c)
        h2s = re.findall(r'^##\s+(.+)$', c['raw'], re.MULTILINE)
        for h2 in h2s:
            skip = {'背景','核心洞察','核心事件','核心数据','核心观点',
                    '延伸思考','小结','总结','附录','补充','概述'}
            if h2.strip() not in skip and len(h2.strip()) > 2:
                topic_index[h2.strip()].append(c)

    for c in cards:
        nodes.append({
            'id': c['slug'],
            'title': c['title'],
            'category': c['category'],
            'layer': layer_map.get(c['category'], 1),
            'tags': c['tags'],
            'date': c['date'],
            'summary': c['summary'][:80],
            'degree': 0
        })

    def add_edge(slug1, slug2, label):
        key = tuple(sorted([slug1, slug2]))
        if key not in edge_set and slug1 != slug2:
            edge_set.add(key)
            edges.append({'source': slug1, 'target': slug2, 'label': label})
            for n in nodes:
                if n['id'] in key:
                    n['degree'] += 1

    for c in cards:
        for tag in c['tags']:
            for other in tag_index[tag]:
                add_edge(c['slug'], other['slug'], f'标签:{tag}')

    for topic, cs in topic_index.items():
        if len(cs) < 2:
            continue
        for i, ci in enumerate(cs):
            for j, cj in enumerate(cs):
                if i >= j:
                    continue
                if ci['category'] == cj['category']:
                    add_edge(ci['slug'], cj['slug'], f'同题:{topic[:12]}')

    all_cards_map = {c['slug']: c for c in cards}
    for c in cards:
        if layer_map.get(c['category']) == 2:
            for other in cards:
                if layer_map.get(other['category']) == 1:
                    if other['title'] in c['raw'] and other['slug'] != c['slug']:
                        add_edge(c['slug'], other['slug'], '引用')

    for n in nodes:
        if n['degree'] == 0:
            same_cat = [x for x in nodes if x['category'] == n['category'] and x['id'] != n['id']]
            if same_cat:
                best = max(same_cat, key=lambda x: x['degree'])
                add_edge(n['id'], best['id'], '同范畴')
            else:
                others = [x for x in nodes if x['degree'] > 0]
                if others:
                    best = max(others, key=lambda x: x['degree'])
                    add_edge(n['id'], best['id'], '跨类关联')

    return {'nodes': nodes, 'edges': edges}

def build_graph():
    global _cache
    cards = get_cards()
    with _cache_lock:
        if _cache['graph']:
            return _cache['graph']
    return _build_graph(cards)

# ── Routes ───────────────────────────────────────────────────────────────────
@app.route('/')
def home():
    cards = get_cards()
    cats = defaultdict(list)
    for c in cards:
        cats[c['category']].append(c)
    recent = sorted(cards, key=lambda x: x['date'], reverse=True)[:12]
    cat_stats = {k: len(v) for k, v in cats.items()}
    return render_template('home.html', recent=recent, cat_stats=cat_stats, total=len(cards))

@app.route('/card/<slug>')
def card_view(slug):
    cards = get_cards()
    card = None
    for c in cards:
        if c['slug'] == slug:
            card = c
            break
    if not card:
        abort(404)
    related = []
    for other in cards:
        if other['slug'] == slug:
            continue
        shared = set(card['tags']) & set(other['tags'])
        if shared:
            related.append((other, list(shared)[:3]))
    related = sorted(related, key=lambda x: len(x[1]), reverse=True)[:8]
    html = render_card(card, cards)
    return render_template('card.html', card=card, content=html, related=related)

@app.route('/graph')
def graph_page():
    return render_template('graph.html')

@app.route('/api/graph')
def api_graph():
    return build_graph()

@app.route('/category/<cat>')
def category(cat):
    cards = get_cards()
    filtered = sorted([c for c in cards if c['category'] == cat],
                     key=lambda x: x['date'], reverse=True)
    return render_template('category.html', cat=cat, cards=filtered)

@app.route('/all')
def all_cards():
    cards = get_cards()
    filtered = sorted(cards, key=lambda x: x['date'], reverse=True)
    return render_template('category.html', cat='全部卡片', cards=filtered)

@app.route('/search')
def search():
    q = request.args.get('q', '').strip()
    cards = get_cards()
    if q:
        qlow = q.lower()
        results = [c for c in cards
                   if qlow in c['title'].lower()
                   or qlow in ' '.join(c['tags']).lower()
                   or qlow in c['raw'].lower()]
    else:
        results = []
    return render_template('search.html', query=q, results=results)

@app.route('/tags')
def tags_page():
    cards = get_cards()
    freq = defaultdict(int)
    for c in cards:
        for t in c['tags']:
            freq[t] += 1
    tags = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return render_template('tags.html', tags=tags)

if __name__ == '__main__':
    print("[Jerry Wiki] Starting... pre-warming cache")
    t0 = time.time()

    # Pre-warm on startup
    file_mtimes = _scan_mtimes()
    cards = _load_cards()
    graph = _build_graph(cards)
    with _cache_lock:
        _cache['cards'] = cards
        _cache['graph'] = graph
        _cache['loaded_at'] = time.time()
        _cache['file_mtimes'] = file_mtimes

    print(f"[Jerry Wiki] Pre-warmed {len(cards)} cards in {time.time()-t0:.1f}s")

    # Ngrok token support (legacy — uses external ngrok now)
    ngrok_tok_file = os.path.join(os.path.dirname(__file__), 'ngrok_token.txt')
    if os.path.exists(ngrok_tok_file):
        with open(ngrok_tok_file) as f:
            token = f.read().strip()
        if token:
            print("Ngrok token found (not used — external ngrok process running)")

    app.run(host='0.0.0.0', port=5001, debug=False)
