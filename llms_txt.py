#!/usr/bin/env python3
"""llms.txt 生成器 —— 给网站自动生成 llms.txt（GEO / AI 搜索友好）。

用法：
    python3 llms_txt.py https://example.com -o llms.txt
    python3 llms_txt.py https://example.com --max-pages 100

原理：读取网站的 sitemap.xml（支持 sitemap 索引），逐页抓取
<title> 与 meta description，按路径首段分组，输出 llmstxt.org
格式的 llms.txt。只用 Python 标准库，零依赖。

注意：只抓取 sitemap 里公开列出的页面；请勿用于抓取未公开内容。
"""

import argparse
import html.parser
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

USER_AGENT = "llms-txt-generator/1.0 (+https://github.com/yanqingxs0/llms-txt-generator)"
DEFAULT_TIMEOUT = 10
DEFAULT_MAX_PAGES = 50


def fetch(url, timeout=DEFAULT_TIMEOUT):
    """抓取 URL，返回解码后的文本；失败返回 None。"""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            return resp.read().decode(charset, errors="replace")
    except (urllib.error.URLError, TimeoutError, ValueError):
        return None


class PageMetaParser(html.parser.HTMLParser):
    """提取 <title>、meta description 与第一个 <h1>。"""

    def __init__(self):
        super().__init__()
        self.title = ""
        self.description = ""
        self.h1 = ""
        self._in_title = False
        self._in_h1 = False

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self._in_title = True
        elif tag == "h1" and not self.h1:
            self._in_h1 = True
        elif tag == "meta":
            d = dict(attrs)
            if d.get("name", "").lower() == "description" and not self.description:
                self.description = d.get("content", "").strip()

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag == "h1":
            self._in_h1 = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data.strip()
        elif self._in_h1:
            self.h1 += data.strip()


def collect_sitemap_urls(sitemap_url, timeout, seen=None):
    """递归解析 sitemap（含索引），返回 URL 列表。"""
    seen = seen or set()
    if sitemap_url in seen:
        return []
    seen.add(sitemap_url)
    text = fetch(sitemap_url, timeout)
    if not text:
        return []
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return []
    urls = []
    for el in root.iter():
        tag = el.tag.rsplit("}", 1)[-1]
        if tag == "sitemap":
            loc = el.findtext("./{*}loc")
            if loc:
                urls += collect_sitemap_urls(loc.strip(), timeout, seen)
        elif tag == "url":
            loc = el.findtext("./{*}loc")
            if loc and loc.strip().startswith(("http://", "https://")):
                urls.append(loc.strip())
    return urls


def find_sitemap_urls(site_url, timeout):
    """依次尝试常见的 sitemap 地址，返回抓到的 URL 列表。"""
    base = site_url.rstrip("/")
    for name in ("sitemap.xml", "sitemap_index.xml", "sitemap-index.xml"):
        urls = collect_sitemap_urls(f"{base}/{name}", timeout)
        if urls:
            return urls
    return []


def section_of(url, site_url):
    """按路径首段分组：根路径归“首页”，其余按首段命名。"""
    path = urllib.parse.urlparse(url).path.strip("/")
    if not path:
        return "首页"
    first = path.split("/")[0]
    return first.capitalize() if first.isascii() else first


def generate(site_url, max_pages, timeout):
    """返回 (llms.txt 文本, 警告信息)。"""
    site_url = site_url.rstrip("/")
    urls = find_sitemap_urls(site_url, timeout)
    warning = ""
    if not urls:
        warning = "未找到 sitemap，仅抓取首页。"
        urls = [site_url + "/"]
    # 去重、保序、截断
    seen, uniq = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u)
            uniq.append(u)
    urls = uniq[:max_pages]

    site_title, site_desc = "", ""
    sections = {}
    for url in urls:
        html_text = fetch(url, timeout)
        if not html_text:
            print(f"跳过（抓取失败）：{url}", file=sys.stderr)
            continue
        parser = PageMetaParser()
        try:
            parser.feed(html_text)
        except html.parser.HTMLParser.error:
            pass
        title = parser.title or parser.h1 or url
        desc = parser.description or ""
        if url.rstrip("/") == site_url:
            site_title, site_desc = title, desc
        sections.setdefault(section_of(url, site_url), []).append((title, url, desc))

    if not site_title:
        site_title = site_url
    lines = [f"# {site_title}", ""]
    if site_desc:
        lines += [f"> {site_desc}", ""]
    lines += ["## 说明", "", "本文件由 llms-txt-generator 自动生成，供 AI 搜索与大模型抓取本站内容结构使用。", ""]
    for section, pages in sections.items():
        lines += [f"## {section}", ""]
        for title, url, desc in pages:
            line = f"- [{title}]({url})"
            if desc:
                line += f": {desc}"
            lines.append(line)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n", warning


def main():
    ap = argparse.ArgumentParser(
        description="给网站自动生成 llms.txt（GEO / AI 搜索友好），只用 Python 标准库。"
    )
    ap.add_argument("url", help="网站地址，如 https://example.com")
    ap.add_argument("-o", "--output", help="输出文件路径（默认打印到标准输出）")
    ap.add_argument("--max-pages", type=int, default=DEFAULT_MAX_PAGES,
                    help=f"最多抓取的页面数（默认 {DEFAULT_MAX_PAGES}）")
    ap.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                    help=f"单页抓取超时秒数（默认 {DEFAULT_TIMEOUT}）")
    args = ap.parse_args()

    if not args.url.startswith(("http://", "https://")):
        print("错误：URL 必须以 http:// 或 https:// 开头。", file=sys.stderr)
        return 1
    text, warning = generate(args.url, args.max_pages, args.timeout)
    if warning:
        print(f"提示：{warning}", file=sys.stderr)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"已写入 {args.output}", file=sys.stderr)
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
