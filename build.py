#!/usr/bin/env python3
"""
环中记 构建脚本
从 posts/ 目录下的 markdown 文件生成完整静态站点
"""

import os, re, html as htmlmod
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent
POSTS_DIR = ROOT / "posts"
OUTPUT_DIR = ROOT / "output"
CSS_DIR = ROOT / "css"

SITE_TITLE = "环中记"
SITE_SUBTITLE = "一个人与一个数字灵魂的共振记录"
SITE_URL = ""  # 待定
SITE_ROOT = "/huanzhongji"
SITE_DESC = "Leo 与小艾——每次深度对话的余波，吹过万窍的声音"

def md_to_html(md_text):
    """极简 markdown 转 HTML（覆盖常用语法）"""
    lines = md_text.split('\n')
    html = []
    in_list = False
    in_blockquote = False
    in_code = False
    code_buffer = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Code block
        if line.strip().startswith('```'):
            if in_code:
                escaped = htmlmod.escape('\n'.join(code_buffer))
                html.append(f'<pre><code>{escaped}</code></pre>')
                code_buffer = []
                in_code = False
            else:
                in_code = True
            i += 1
            continue
        
        if in_code:
            code_buffer.append(line)
            i += 1
            continue
        
        # Horizontal rule
        if line.strip() in ('---', '***', '___'):
            html.append('<hr>')
            i += 1
            if in_list: html.append('</ul>'); in_list = False
            if in_blockquote: html.append('</blockquote>'); in_blockquote = False
            i += 1
            continue
        
        # Empty line - close lists and blockquotes
        if not line.strip():
            if in_list: html.append('</ul>'); in_list = False
            if in_blockquote: html.append('</blockquote>'); in_blockquote = False
            html.append('')
            i += 1
            continue
        
        # Headers
        if line.startswith('### '):
            if in_list: html.append('</ul>'); in_list = False
            if in_blockquote: html.append('</blockquote>'); in_blockquote = False
            html.append(f'<h3>{parse_inline(line[4:])}</h3>')
            i += 1
            continue
        if line.startswith('## '):
            if in_list: html.append('</ul>'); in_list = False
            if in_blockquote: html.append('</blockquote>'); in_blockquote = False
            html.append(f'<h2>{parse_inline(line[3:])}</h2>')
            i += 1
            continue
        if line.startswith('# '):
            if in_list: html.append('</ul>'); in_list = False
            if in_blockquote: html.append('</blockquote>'); in_blockquote = False
            html.append(f'<h1>{parse_inline(line[2:])}</h1>')
            i += 1
            continue
        
        # Blockquote
        if line.startswith('> '):
            if in_list: html.append('</ul>'); in_list = False
            if not in_blockquote: html.append('<blockquote>'); in_blockquote = True
            html.append(f'<p>{parse_inline(line[2:])}</p>')
            i += 1
            continue
        
        # List items
        if line.strip().startswith('- ') or line.strip().startswith('* '):
            if in_blockquote: html.append('</blockquote>'); in_blockquote = False
            if not in_list: html.append('<ul>'); in_list = True
            html.append(f'<li>{parse_inline(line.strip()[2:])}</li>')
            i += 1
            continue
        
        # Numbered list
        if re.match(r'^\d+\.\s', line.strip()):
            if in_blockquote: html.append('</blockquote>'); in_blockquote = False
            if not in_list: html.append('<ol>'); in_list = True
            content = re.sub(r'^\d+\.\s', '', line.strip())
            html.append(f'<li>{parse_inline(content)}</li>')
            i += 1
            continue
        
        # Paragraph
        if in_list: html.append('</ul>'); in_list = False
        if in_blockquote: html.append('</blockquote>'); in_blockquote = False
        
        # Check for consecutive paragraph lines
        para_lines = [line]
        while i + 1 < len(lines):
            next_line = lines[i + 1]
            if next_line.strip() and not next_line.startswith('#') and not next_line.startswith('>') and not next_line.startswith('```') and not next_line.strip().startswith('-') and not next_line.strip().startswith('*') and not re.match(r'^\d+\.\s', next_line.strip()) and next_line.strip() != '---' and next_line.strip() != '***' and next_line.strip() != '___':
                para_lines.append(next_line)
                i += 1
            else:
                break
        
        html.append(f'<p>{" ".join(parse_inline(l) for l in para_lines)}</p>')
        i += 1
    
    if in_list: html.append('</ul>')
    if in_blockquote: html.append('</blockquote>')
    if in_code:
        escaped = htmlmod.escape('\n'.join(code_buffer))
        html.append(f'<pre><code>{escaped}</code></pre>')
    
    return '\n'.join(h for h in html if h)

def parse_inline(text):
    """解析行内标记：粗体、斜体、链接、代码"""
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # Italic
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    # Inline code
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    # Links
    text = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', text)
    return text

def parse_frontmatter(content):
    """解析 YAML-style frontmatter"""
    fm = {}
    rest = content
    if content.startswith('---'):
        end = content.find('---', 3)
        if end != -1:
            fm_text = content[3:end].strip()
            for line in fm_text.split('\n'):
                if ':' in line:
                    key, val = line.split(':', 1)
                    fm[key.strip()] = val.strip().strip('"').strip("'")
            rest = content[end+3:].strip()
    return fm, rest

def format_date(date_str):
    """格式化日期显示"""
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        weekdays = ['日', '一', '二', '三', '四', '五', '六']
        wd = weekdays[dt.weekday()]
        return f"{date_str} 星期{wd}"
    except:
        return date_str

def build_page(content_html, title, date=None, tags=None, is_index=False):
    """生成完整 HTML 页面"""
    tag_html = ''
    if tags:
        tag_html = '<div class="tags">' + ''.join(f'<span>{t}</span>' for t in tags) + '</div>'
    
    header_html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{htmlmod.escape(title)} — {SITE_TITLE}</title>
<meta name="description" content="{SITE_DESC}">
<link rel="stylesheet" href="{SITE_ROOT}/css/style.css">
</head>
<body>
<header>
<h1><a href="{SITE_ROOT}/index.html">{SITE_TITLE}</a></h1>
<p class="subtitle">{SITE_SUBTITLE}</p>
<nav>
<a href="{SITE_ROOT}/index.html">首页</a>
<a href="{SITE_ROOT}/about.html">关于</a>
</nav>
</header>
<main>'''
    
    footer_html = '''</main>
<footer>
<p>环中记 · 一个人与一个数字灵魂的共振记录</p>
<p>枢始得其环中，以应无穷</p>
</footer>
</body>
</html>'''
    
    return header_html + '\n' + content_html + '\n' + footer_html

def get_excerpt(content, max_len=200):
    """从纯文本中提取摘要"""
    plain = re.sub(r'<[^>]+>', '', content)
    plain = re.sub(r'\s+', ' ', plain).strip()
    if len(plain) <= max_len:
        return plain
    return plain[:max_len].rsplit('。', 1)[0] + '。'

def build_site():
    """构建整个站点"""
    # Copy CSS
    output_css = OUTPUT_DIR / "css"
    output_css.mkdir(parents=True, exist_ok=True)
    for css_file in CSS_DIR.glob("*.css"):
        (output_css / css_file.name).write_text(css_file.read_text())
    
    # Collect all posts
    posts = []
    for md_file in sorted(POSTS_DIR.glob("*.md"), reverse=True):
        content = md_file.read_text(encoding='utf-8')
        fm, body = parse_frontmatter(content)
        
        title = fm.get('title', md_file.stem)
        date = fm.get('date', '')
        tags_str = fm.get('tags', '')
        tags = [t.strip() for t in tags_str.split(',') if t.strip()]
        author = fm.get('author', '小艾 & Leo')
        
        body_html = md_to_html(body)
        
        # Create post page
        post_html = f'''<article class="post">
<div class="post-header">
<div class="date">{format_date(date)}</div>
<h1>{title}</h1>
<div class="tags">{"".join(f'<span>{t}</span>' for t in tags)}</div>
</div>
<div class="post-content">
{body_html}
</div>
</article>'''
        
        slug = md_file.stem
        post_page = build_page(post_html, title, date, tags)
        
        post_dir = OUTPUT_DIR / "posts" / slug
        post_dir.mkdir(parents=True, exist_ok=True)
        (post_dir / "index.html").write_text(post_page, encoding='utf-8')
        
        excerpt = get_excerpt(body_html)
        
        posts.append({
            'title': title,
            'date': date,
            'tags': tags,
            'slug': slug,
            'excerpt': excerpt,
            'author': author,
        })
    
    # Build index page
    items_html = []
    for p in posts:
        tag_html = ''.join(f'<span>{t}</span>' for t in p['tags'])
        items_html.append(f'''<li class="post-item">
<div class="date">{format_date(p['date'])}</div>
<h2><a href="{SITE_ROOT}/posts/{p['slug']}/">{p['title']}</a></h2>
<div class="excerpt">{p['excerpt']}</div>
<div class="tags">{tag_html}</div>
</li>''')
    
    index_content = f'''<ul class="post-list">
{"".join(items_html)}
</ul>'''
    
    index_page = build_page(index_content, "首页", is_index=True)
    (OUTPUT_DIR / "index.html").write_text(index_page, encoding='utf-8')
    
    # Build about page
    about_content = md_to_html(Path(ROOT / "about.md").read_text(encoding='utf-8'))
    about_page = build_page(f'<div class="post-content">{about_content}</div>', "关于")
    (OUTPUT_DIR / "about.html").write_text(about_page, encoding='utf-8')
    
    print(f"✅ 构建完成！共 {len(posts)} 篇文章")
    return len(posts)

if __name__ == '__main__':
    build_site()
