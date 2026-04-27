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
                tags = extract_keywords(text, top_n=10)
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

# ── Stopwords ────────────────────────────────────────────────────────────────
_STOPWORDS = set([
    '的', '了', '是', '在', '和', '与', '或', '及', '等', '于', '为', '以', '对', '上', '下',
    '中', '内', '外', '前', '后', '所', '能', '可', '会', '有', '也', '都', '而', '则',
    '一个', '可以', '这个', '那个', '如果', '因为', '所以', '但是', '虽然', '或者',
    '以及', '通过', '进行', '使用', '已经', '目前', '现在', '今天', '昨天', '明天',
    '没有', '什么', '如何', '怎样', '为什么', '哪些', '哪些', '之一',
    '延伸思考', '核心洞察', '核心事件', '核心数据', '核心观点', '创建时间',
    '背景', '事件', '数据', '观点', '思考', '小结', '总结', '附录', '补充', '概述',
    '**', '---', '==', '标签', '来源', '作者', '状态', 'tags',
    '推送日报', '会话复盘', '提炼', '归档', '概念卡', '方法论', '案例库', '项目复盘',
    '年月日', '时分秒', '时间', '日期', '本卡片由', '说明',
    'ai', 'jerry', 'claude', 'anthropic', 'openai', 'google', 'gpu', '英伟达',
    'mlcc', 'vs', 'md', 'cst', '01_inbox', '这是', '这意味着', '而是', '亿美元', '公司', '关注', '发布', '几个月', '个月',
    'deepseek', 'ipo', 'ceo', 'gpt', 'cursor', 'code',
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
    'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
    'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
    'this', 'that', 'these', 'those', 'it', 'its',
])

_RE_SKIP_LINE = re.compile(r'^\s*([#*=\[\]「」『』]|$|---|==|\d{4}[-年]|\d+[月日时])')

def _is_meta_line(line):
    return bool(_RE_SKIP_LINE.match(line.strip()))

def _split_words(text):
    """Split Chinese/English text into words, filter stopwords and single chars."""
    words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z0-9_]+', text)
    result = []
    for w in words:
        if len(w) < 2:
            continue
        if w.lower() in _STOPWORDS:
            continue
        if w.isdigit():
            continue
        result.append(w)
    return result

def _body_text(text):
    """Return only the body text (after meta block: # title, tags, ---, etc)."""
    lines = text.split('\n')
    body_started = False
    body_lines = []
    for line in lines:
        stripped = line.strip()
        # Start of body: first non-skip line after we've passed the meta block
        if not body_started:
            # Skip all meta lines until we hit a real content paragraph
            if _is_meta_line(stripped):
                continue
            # First non-meta line is the title → skip it too
            body_started = True
            continue
        if stripped.startswith('#') or stripped.startswith('**') or stripped in ('---', '=='):
            continue
        body_lines.append(line)
    return '\n'.join(body_lines)

def extract_keywords(text, top_n=20):
    """Extract most frequent meaningful words from body text only."""
    body = _body_text(text)
    words = _split_words(body)
    freq = defaultdict(int)
    seen = set()
    for w in words:
        if w not in seen:
            freq[w] += 1
            seen.add(w)
    return [w for w, _ in sorted(freq.items(), key=lambda x: x[1], reverse=True)[:top_n]]

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

    layer_map = {
        '01_Inbox': 0,
        '概念卡': 1, '方法论': 1, '案例库': 1, '项目复盘': 1,
        '03_Output': 2,
    }

    # ── Extract keywords for each card ─────────────────────────────────────
    for c in cards:
        c['_keywords'] = set(extract_keywords(c['raw'], top_n=30))

    # Global keyword index: keyword → list of cards
    kw_index = defaultdict(list)
    for c in cards:
        for kw in c['_keywords']:
            kw_index[kw].append(c)

    # ── Build nodes ─────────────────────────────────────────────────────────
    for c in cards:
        nodes.append({
            'id': c['slug'],
            'title': c['title'],
            'category': c['category'],
            'layer': layer_map.get(c['category'], 1),
            'tags': list(c['_keywords'])[:5],   # reuse field: top-5 keywords as display tags
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

    # ── Link 1: Keyword co-occurrence ─────────────────────────────────────────
    # Only connect if they share ≥3 meaningful keywords AND keywords are not too common
    kw_doc_count = {kw: len(docs) for kw, docs in kw_index.items()}
    min_kw, max_kw = 2, max(2, len(cards) * 0.03)  # keyword must appear in 2~3% of docs (≥2 docs)
    for kw, owners in kw_index.items():
        if len(owners) < min_kw or len(owners) > max_kw:
            continue
        for i, ci in enumerate(owners):
            for j, cj in enumerate(owners):
                if i >= j:
                    continue
                shared = ci['_keywords'] & cj['_keywords']
                if len(shared) >= 3:
                    label = ' · '.join(sorted(shared)[:3])
                    add_edge(ci['slug'], cj['slug'], f'共词:{label[:20]}')

    # ── Link 2: Same creation batch (same YYYY-MM-DD) ───────────────────────────
    # Only connect docs that share the exact day AND the day has ≤15 docs
    date_index = defaultdict(list)
    for c in cards:
        if c['date'] and len(c['date']) == 10:
            date_index[c['date']].append(c)

    for date, owners in date_index.items():
        if len(owners) < 2 or len(owners) > 8:
            continue
        for i, ci in enumerate(owners):
            for j, cj in enumerate(owners):
                if i >= j:
                    continue
                add_edge(ci['slug'], cj['slug'], '同日')

    # ── Link 3: Title mention (A mentions B's title in body) ──────────────
    title_map = {c['title']: c for c in cards}
    for c in cards:
        for title, other in title_map.items():
            if title == c['title'] or title == other['title']:
                continue
            if len(title) < 4:
                continue
            if title in c['raw']:
                add_edge(c['slug'], other['slug'], '引用')

    # ── Ensure no orphans ───────────────────────────────────────────────────
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

    # Clean up temporary keyword sets
    for c in cards:
        del c['_keywords']

    return {'nodes': nodes, 'edges': edges}
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

def build_graph():
    global _cache
    cards = get_cards()
    with _cache_lock:
        if _cache['graph']:
            return _cache['graph']
    return _build_graph(cards)

@app.route('/api/graph')
def api_graph():
    return build_graph()

@app.route('/category/<cat>')
def category(cat):
    page = max(1, int(request.args.get('page', 1)))
    per_page = 12
    cards = get_cards()
    filtered = sorted([c for c in cards if c['category'] == cat],
                     key=lambda x: x['date'], reverse=True)
    total = len(filtered)
    page_cards = filtered[(page-1)*per_page:page*per_page]
    pages = (total + per_page - 1) // per_page
    return render_template('category.html', cat=cat, cards=page_cards,
                          page=page, pages=pages, total=total)

@app.route('/all')
def all_cards():
    page = max(1, int(request.args.get('page', 1)))
    per_page = 12
    cards = get_cards()
    filtered = sorted(cards, key=lambda x: x['date'], reverse=True)
    total = len(filtered)
    page_cards = filtered[(page-1)*per_page:page*per_page]
    pages = (total + per_page - 1) // per_page
    return render_template('category.html', cat='全部卡片', cards=page_cards,
                          page=page, pages=pages, total=total)

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

_TAG_STOPWORDS = set([
    # ── 通用中文 ────────────────────────────────────────────────
    '的', '了', '是', '在', '和', '与', '或', '及', '等', '于', '为', '以', '对', '上', '下',
    '中', '内', '外', '前', '后', '所', '能', '可', '会', '有', '也', '都', '而', '则',
    '一个', '可以', '这个', '那个', '如果', '因为', '所以', '但是', '虽然', '或者',
    '以及', '通过', '进行', '使用', '已经', '目前', '现在', '今天', '昨天', '明天',
    '没有', '什么', '如何', '怎样', '为什么', '哪些', '之一',
    '重要', '一般', '普通', '特殊', '关键',
    '成功', '失败', '完成', '进行中', '待处理', '备注', '备注说明',
    '过去', '未来', '现在', '目前', '今日', '本周', '本月', '今年',
    # ── 模板/Meta ────────────────────────────────────────────────
    '延伸思考', '核心洞察', '核心事件', '核心数据', '核心观点', '创建时间',
    '背景', '事件', '数据', '观点', '思考', '小结', '总结', '附录', '补充', '概述',
    '标签', '来源', '作者', '状态', 'tags',
    '推送日报', '会话复盘', '提炼', '归档', '概念卡', '方法论', '案例库', '项目复盘',
    '年月日', '时分秒', '时间', '日期', '本卡片由', '说明',
    '归档时间', '创建时间', '更新时间', '修改时间',
    # ── Cron 推送输出词 ─────────────────────────────────────────
    '热点推送', '热点日报', '热点播报',
    '财经新闻推送', '财经早报', '财经新闻',
    '半导体热点晨报', '半导体晨报',
    '数据来源', '数据窗口',
    '推送任务成功率', '任务执行总数', '送达渠道', '飞书总体运营群', '飞书用户',
    '含误报', '未删减', '内容均实际送达', '内容实际已推送成功', '本窗口内',
    '按时间顺序排列', '摘要', '送达状态',
    # ── 英文工具/系统词 ──────────────────────────────────────────
    'ai', 'jerry', 'claude', 'anthropic', 'openai', 'google', 'gpu', '英伟达',
    'mlcc', 'vs', 'md', 'cst', '01_inbox',
    'deepseek', 'ipo', 'ceo', 'gpt', 'cursor', 'code',
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
    'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
    'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
    'this', 'that', 'these', 'those', 'it', 'its',
    # ── 技术/格式残留 ────────────────────────────────────────────
    'json', 'ts', 'md', 'html', 'css', 'py', 'js',
    'jobid', 'runs', 'cron', 'schedule',
    'uuid', 'slug', 'tag', 'url',
    'hot', 'new', 'top', 'hotfix',
])

@app.route('/tags')
def tags_page():
    page = max(1, int(request.args.get('page', 1)))
    per_page = 100
    cards = get_cards()
    freq = defaultdict(int)
    for c in cards:
        for t in c['tags']:
            t = t.strip()
            if len(t) < 2 or len(t) > 20 or t.isdigit():
                continue
            if t.lower() in _TAG_STOPWORDS:
                continue
            freq[t] += 1
    # Only keep tags appearing 2+ times (low-freq noise)
    all_tags = sorted([(k, v) for k, v in freq.items() if v >= 2],
                     key=lambda x: x[1], reverse=True)
    total = len(all_tags)
    page_tags = all_tags[(page-1)*per_page:page*per_page]
    pages = (total + per_page - 1) // per_page
    return render_template('tags.html', tags=page_tags, page=page, pages=pages, total=total)

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
