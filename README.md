# llms.txt 生成器

给网站自动生成 `llms.txt`，让 AI 搜索与大模型更快抓准你网站的内容结构。GEO（生成式引擎优化）里最基础、性价比最高的一步。

## 它做什么

1. 读取网站的 `sitemap.xml`（支持 sitemap 索引），拿到公开页面列表；
2. 逐页抓取 `<title>` 与 meta description；
3. 按路径分组，输出 [llmstxt.org](https://llmstxt.org/) 格式的 `llms.txt`。

```bash
python3 llms_txt.py https://example.com -o llms.txt
```

## 环境要求

- Python 3.9+
- 零依赖，只用标准库

## 用法

```bash
# 输出到终端
python3 llms_txt.py https://example.com

# 写入文件
python3 llms_txt.py https://example.com -o llms.txt

# 最多抓 100 页，单页超时 15 秒
python3 llms_txt.py https://example.com -o llms.txt --max-pages 100 --timeout 15
```

## 输出示例

`example-llgoder.llms.txt` 是拿本站（llgoder.pages.dev）实测跑出来的结果：

```markdown
# 刘磊聊GEO｜让 AI 找到你

> 刘磊聊GEO：前平安十年小微金融老兵，现南京 GEO 全域获客操盘手……

## 首页

- [刘磊聊GEO｜让 AI 找到你](https://llgoder.pages.dev/): ……

## Articles

- [你的客户都在问 AI，为什么回答里没有你？｜刘磊聊GEO](https://llgoder.pages.dev/articles/customers-ask-ai): ……
```

## 说明与限制

- 只抓取 sitemap 里公开列出的页面；找不到 sitemap 时仅抓首页并给出提示。
- 生成的是结构骨架，正式上线前建议人工检查一遍标题与描述，再放到网站根目录。
- 请勿用于抓取未公开内容。

## 这个工具是怎么做的

这个工具是用 Muse 做出来的：给它讲清楚需求，它写代码、跑测试、修 bug，全程可追溯。如果你也想试试 Muse：

- 注册链接：https://muse.ai/join
- 邀请码：`ELGFUL`

想多了解 Muse 本身：[用 Muse 是什么体验](muse-invite.md)
