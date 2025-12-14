# coding=utf-8
"""
HTML 报告渲染模块（重构版）

目标：
- 保持数据输入/调用方式不变
- 重构布局为更现代的卡片式 UI
- 重点修复移动端：换行挤压、NEW 标识遮挡、按钮叠层、padding-right 魔法数等问题
"""

from datetime import datetime
from typing import Dict, Optional, Callable, List

from trendradar.report.helpers import html_escape


def render_html_content(
    report_data: Dict,
    total_titles: int,
    is_daily_summary: bool = False,
    mode: str = "daily",
    update_info: Optional[Dict] = None,
    *,
    reverse_content_order: bool = False,
    get_time_func: Optional[Callable[[], datetime]] = None,
) -> str:
    """渲染HTML内容

    Args:
        report_data: 报告数据字典，包含 stats, new_titles, failed_ids, total_new_count
        total_titles: 新闻总数
        is_daily_summary: 是否为当日汇总
        mode: 报告模式 ("daily", "current", "incremental")
        update_info: 更新信息（可选）
        reverse_content_order: 是否反转内容顺序（新增热点在前）
        get_time_func: 获取当前时间的函数（可选）

    Returns:
        渲染后的 HTML 字符串
    """

    # ---------------------------
    # Header: 报告类型
    # ---------------------------
    if is_daily_summary:
        if mode == "current":
            report_type = "当前榜单"
        elif mode == "incremental":
            report_type = "增量模式"
        else:
            report_type = "当日汇总"
    else:
        report_type = "实时分析"

    # ---------------------------
    # 统计：热点新闻数量
    # ---------------------------
    hot_news_count = sum(len(stat.get("titles", [])) for stat in report_data.get("stats", []))

    # 时间
    now = get_time_func() if get_time_func else datetime.now()
    time_str = now.strftime("%m-%d %H:%M")

    # ---------------------------
    # Section: 失败平台
    # ---------------------------
    failed_ids_html = ""
    failed_ids = report_data.get("failed_ids") or []
    if failed_ids:
        items = "".join(f'<li class="error-item">{html_escape(x)}</li>' for x in failed_ids)
        failed_ids_html = f"""
            <section class="card card-warn" aria-label="请求失败的平台">
              <div class="card-hd">
                <div class="card-title">⚠️ 请求失败的平台</div>
              </div>
              <ul class="error-list">{items}</ul>
            </section>
        """

    # ---------------------------
    # Section: 热点词 + 新闻列表
    # ---------------------------
    def count_class_name(cnt: int) -> str:
        if cnt >= 10:
            return "hot"
        if cnt >= 5:
            return "warm"
        return "mild"

    stats_blocks: List[str] = []
    stats = report_data.get("stats") or []
    total_groups = len(stats)

    for i, stat in enumerate(stats, 1):
        word = html_escape(stat.get("word", ""))
        cnt = int(stat.get("count", 0))
        ccls = count_class_name(cnt)

        titles = stat.get("titles") or []
        news_rows: List[str] = []

        for j, title_data in enumerate(titles, 1):
            is_new = bool(title_data.get("is_new", False))
            new_badge = '<span class="badge badge-new" aria-label="NEW">NEW</span>' if is_new else ""

            source_name = html_escape(title_data.get("source_name", ""))
            ranks = title_data.get("ranks", []) or []
            rank_threshold = int(title_data.get("rank_threshold", 10))

            rank_html = ""
            if ranks:
                min_rank = min(ranks)
                max_rank = max(ranks)

                if min_rank <= 3:
                    rcls = "top"
                elif min_rank <= rank_threshold:
                    rcls = "high"
                else:
                    rcls = "base"

                rank_text = str(min_rank) if min_rank == max_rank else f"{min_rank}-{max_rank}"
                rank_html = f'<span class="pill pill-rank {rcls}" title="榜单排名">{rank_text}</span>'

            # 时间显示
            time_display = title_data.get("time_display", "") or ""
            time_html = ""
            if time_display:
                simplified = (
                    time_display.replace(" ~ ", "~")
                    .replace("[", "")
                    .replace("]", "")
                )
                time_html = f'<span class="meta">{html_escape(simplified)}</span>'

            # 出现次数
            count_info = int(title_data.get("count", 1) or 1)
            freq_html = f'<span class="pill pill-freq" title="出现次数">{count_info}次</span>' if count_info > 1 else ""

            # 标题 + 链接
            title = html_escape(title_data.get("title", ""))
            link_url = title_data.get("mobile_url") or title_data.get("url", "") or ""
            if link_url:
                escaped_url = html_escape(link_url)
                title_html = f'<a class="title-link" href="{escaped_url}" target="_blank" rel="noreferrer noopener">{title}</a>'
            else:
                title_html = f"<span>{title}</span>"

            # news item: Grid layout (num | body | badge)
            news_rows.append(f"""
              <article class="news-row">
                <div class="news-num" aria-label="序号">{j}</div>
                <div class="news-body">
                  <div class="news-meta">
                    <span class="source">{source_name}</span>
                    {rank_html}
                    {time_html}
                    {freq_html}
                  </div>
                  <div class="news-title">{title_html}</div>
                </div>
                <div class="news-badge">{new_badge}</div>
              </article>
            """)

        stats_blocks.append(f"""
          <section class="card" aria-label="热点词条">
            <div class="card-hd">
              <div class="wordline">
                <div class="word">{word}</div>
                <div class="count count-{ccls}" title="关联新闻数">{cnt} 条</div>
              </div>
              <div class="index">{i}/{total_groups}</div>
            </div>
            <div class="card-bd">
              <div class="news-list">
                {''.join(news_rows) if news_rows else '<div class="empty">暂无新闻</div>'}
              </div>
            </div>
          </section>
        """)

    stats_html = "".join(stats_blocks)

    # ---------------------------
    # Section: 新增热点
    # ---------------------------
    new_titles_html = ""
    new_titles = report_data.get("new_titles") or []
    if new_titles:
        total_new_count = int(report_data.get("total_new_count", 0) or 0)

        parts: List[str] = [f"""
          <section class="card" aria-label="本次新增热点">
            <div class="card-hd">
              <div class="card-title">本次新增热点</div>
              <div class="card-sub">共 {total_new_count} 条</div>
            </div>
            <div class="card-bd">
        """]

        for source_data in new_titles:
            sname = html_escape(source_data.get("source_name", ""))
            titles = source_data.get("titles") or []
            parts.append(f"""
              <div class="source-block">
                <div class="source-hd">
                  <div class="source-name">{sname}</div>
                  <div class="source-count">{len(titles)} 条</div>
                </div>
                <div class="source-list">
            """)

            for idx, title_data in enumerate(titles, 1):
                ranks = title_data.get("ranks", []) or []
                rank_threshold = int(title_data.get("rank_threshold", 10))

                rank_class = "base"
                rank_text = "?"
                if ranks:
                    min_rank = min(ranks)
                    max_rank = max(ranks)
                    if min_rank <= 3:
                        rank_class = "top"
                    elif min_rank <= rank_threshold:
                        rank_class = "high"
                    rank_text = str(min_rank) if min_rank == max_rank else f"{min_rank}-{max_rank}"

                t = html_escape(title_data.get("title", ""))
                link_url = title_data.get("mobile_url") or title_data.get("url", "") or ""
                if link_url:
                    u = html_escape(link_url)
                    t_html = f'<a class="title-link" href="{u}" target="_blank" rel="noreferrer noopener">{t}</a>'
                else:
                    t_html = f"<span>{t}</span>"

                parts.append(f"""
                  <div class="new-row">
                    <div class="new-num">{idx}</div>
                    <div class="pill pill-rank {rank_class}" title="榜单排名">{rank_text}</div>
                    <div class="new-title">{t_html}</div>
                  </div>
                """)

            parts.append("""
                </div>
              </div>
            """)

        parts.append("""
            </div>
          </section>
        """)
        new_titles_html = "".join(parts)

    # ---------------------------
    # Content order
    # ---------------------------
    if reverse_content_order:
        main_html = new_titles_html + stats_html
    else:
        main_html = stats_html + new_titles_html

    # 更新信息
    update_html = ""
    if update_info:
        update_html = f"""
          <div class="update">
            发现新版本 <b>{html_escape(str(update_info.get('remote_version', '')))}</b>，
            当前版本 <b>{html_escape(str(update_info.get('current_version', '')))}</b>
          </div>
        """

    # ---------------------------
    # Final HTML
    # ---------------------------
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
  <title>热点新闻分析</title>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"
          integrity="sha512-BNaRQnYJYiPSqHHDb58B0yaPfCu+Wgds8Gp/gU33kqBtgNS4tSPHuGibyoeqMV/TJlSKda6FXzoEyYGjTe+vXA=="
          crossorigin="anonymous" referrerpolicy="no-referrer"></script>

  <style>
    :root {{
      --bg: #0b1020;
      --paper: #ffffff;
      --muted: rgba(0,0,0,0.55);
      --line: rgba(15, 23, 42, 0.10);

      --indigo: #4f46e5;
      --violet: #7c3aed;

      --hot: #dc2626;
      --warm: #ea580c;
      --ok: #059669;

      --radius: 16px;
      --shadow: 0 10px 30px rgba(0,0,0,0.08);
    }}

    * {{ box-sizing: border-box; }}
    html, body {{ margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
      background: #f6f7fb;
      color: #0f172a;
      line-height: 1.55;
      padding: 16px 12px;
    }}

    .wrap {{
      width: 100%;
      max-width: 720px;
      margin: 0 auto;
    }}

    .hero {{
      background: radial-gradient(1200px 400px at 20% -10%, rgba(255,255,255,0.18), transparent 60%),
                  linear-gradient(135deg, var(--indigo), var(--violet));
      color: #fff;
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      overflow: hidden;
    }}

    .hero-inner {{
      padding: 18px 16px 16px;
    }}

    .hero-top {{
      display: flex;
      gap: 10px;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
    }}

    .hero-title {{
      font-size: clamp(18px, 3.5vw, 22px);
      font-weight: 800;
      letter-spacing: 0.2px;
      margin: 0;
    }}

    .btns {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      justify-content: flex-end;
    }}

    .btn {{
      appearance: none;
      border: 1px solid rgba(255,255,255,0.28);
      background: rgba(255,255,255,0.14);
      color: #fff;
      padding: 9px 12px;
      border-radius: 12px;
      font-size: 13px;
      font-weight: 650;
      cursor: pointer;
      transition: transform 0.12s ease, background 0.12s ease, border-color 0.12s ease;
      backdrop-filter: blur(10px);
      white-space: nowrap;
    }}

    .btn:hover {{
      background: rgba(255,255,255,0.22);
      border-color: rgba(255,255,255,0.38);
      transform: translateY(-1px);
    }}

    .btn:active {{ transform: translateY(0); }}
    .btn:disabled {{ opacity: 0.6; cursor: not-allowed; }}

    .meta-grid {{
      margin-top: 12px;
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
    }}

    .meta-card {{
      background: rgba(255,255,255,0.12);
      border: 1px solid rgba(255,255,255,0.18);
      border-radius: 14px;
      padding: 10px 10px 9px;
      text-align: center;
    }}

    .meta-label {{
      font-size: 12px;
      opacity: 0.85;
    }}

    .meta-value {{
      margin-top: 3px;
      font-size: 15px;
      font-weight: 750;
      letter-spacing: 0.2px;
    }}

    .content {{
      margin-top: 14px;
    }}

    .card {{
      background: var(--paper);
      border-radius: var(--radius);
      box-shadow: 0 6px 18px rgba(0,0,0,0.05);
      border: 1px solid rgba(15, 23, 42, 0.06);
      overflow: hidden;
      margin: 12px 0;
    }}

    .card-hd {{
      padding: 14px 14px 12px;
      display: flex;
      align-items: flex-end;
      justify-content: space-between;
      gap: 12px;
      border-bottom: 1px solid var(--line);
    }}

    .card-title {{
      font-weight: 800;
      font-size: 15px;
    }}

    .card-sub {{
      font-size: 12px;
      color: var(--muted);
      font-weight: 650;
    }}

    .card-bd {{
      padding: 12px 14px 14px;
    }}

    .card-warn {{
      border-color: rgba(220, 38, 38, 0.25);
      background: #fff7f7;
    }}

    .error-list {{
      list-style: none;
      margin: 0;
      padding: 0 14px 14px;
    }}

    .error-item {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
      font-size: 12px;
      color: #991b1b;
      padding: 6px 0;
      border-bottom: 1px dashed rgba(220, 38, 38, 0.18);
    }}
    .error-item:last-child {{ border-bottom: none; }}

    .wordline {{
      display: flex;
      align-items: center;
      gap: 10px;
      min-width: 0;
    }}

    .word {{
      font-size: 16px;
      font-weight: 850;
      letter-spacing: 0.1px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }}

    .count {{
      font-size: 12px;
      font-weight: 800;
      padding: 4px 10px;
      border-radius: 999px;
      background: rgba(15,23,42,0.06);
      color: rgba(15,23,42,0.78);
      white-space: nowrap;
    }}

    .count-hot {{ background: rgba(220,38,38,0.10); color: var(--hot); }}
    .count-warm {{ background: rgba(234,88,12,0.10); color: var(--warm); }}
    .count-mild {{ background: rgba(2,132,199,0.08); color: rgba(2,132,199,0.95); }}

    .index {{
      font-size: 12px;
      color: var(--muted);
      font-weight: 700;
      white-space: nowrap;
    }}

    .news-list {{
      display: flex;
      flex-direction: column;
      gap: 10px;
    }}

    /* 关键：Grid 三列，永远不靠 padding-right 抢空间 */
    .news-row {{
      display: grid;
      grid-template-columns: 34px minmax(0, 1fr) auto;
      gap: 10px;
      padding: 10px 10px;
      border: 1px solid rgba(15, 23, 42, 0.06);
      border-radius: 14px;
      background: #fff;
    }}

    .news-num {{
      width: 34px;
      height: 34px;
      border-radius: 999px;
      display: grid;
      place-items: center;
      font-weight: 850;
      color: rgba(15,23,42,0.55);
      background: rgba(15,23,42,0.06);
      align-self: start;
      margin-top: 2px;
      font-size: 13px;
    }}

    .news-body {{
      min-width: 0;
    }}

    .news-meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
      margin-bottom: 6px;
    }}

    .source {{
      font-size: 12px;
      color: rgba(15,23,42,0.62);
      font-weight: 700;
    }}

    .meta {{
      font-size: 11px;
      color: rgba(15,23,42,0.45);
      font-weight: 650;
    }}

    .pill {{
      font-size: 11px;
      padding: 3px 8px;
      border-radius: 999px;
      font-weight: 850;
      line-height: 1.2;
      white-space: nowrap;
      border: 1px solid rgba(15, 23, 42, 0.10);
      background: rgba(15,23,42,0.04);
      color: rgba(15,23,42,0.70);
    }}

    .pill-rank.top {{ background: rgba(220,38,38,0.12); color: var(--hot); border-color: rgba(220,38,38,0.18); }}
    .pill-rank.high {{ background: rgba(234,88,12,0.12); color: var(--warm); border-color: rgba(234,88,12,0.18); }}
    .pill-rank.base {{ background: rgba(107,114,128,0.10); color: rgba(107,114,128,1); border-color: rgba(107,114,128,0.18); }}
    .pill-freq {{ background: rgba(5,150,105,0.10); color: var(--ok); border-color: rgba(5,150,105,0.18); }}

    .news-title {{
      font-size: 14px;
      font-weight: 650;
      line-height: 1.45;
      word-break: break-word;
      overflow-wrap: anywhere;
    }}

    .title-link {{
      color: #2563eb;
      text-decoration: none;
    }}
    .title-link:hover {{ text-decoration: underline; }}
    .title-link:visited {{ color: #7c3aed; }}

    .news-badge {{
      align-self: start;
      margin-top: 4px;
    }}

    .badge {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-size: 10px;
      font-weight: 900;
      padding: 5px 8px;
      border-radius: 999px;
      letter-spacing: 0.3px;
      white-space: nowrap;
      border: 1px solid rgba(0,0,0,0.08);
    }}

    .badge-new {{
      background: rgba(251,191,36,0.22);
      color: #92400e;
      border-color: rgba(251,191,36,0.32);
    }}

    .source-block {{
      padding: 10px 0 2px;
      border-top: 1px solid rgba(15, 23, 42, 0.08);
    }}
    .source-block:first-child {{ border-top: none; padding-top: 0; }}

    .source-hd {{
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 8px;
    }}
    .source-name {{
      font-size: 13px;
      font-weight: 850;
      color: rgba(15,23,42,0.75);
      min-width: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }}
    .source-count {{
      font-size: 12px;
      color: rgba(15,23,42,0.48);
      font-weight: 750;
      white-space: nowrap;
    }}

    .source-list {{
      display: flex;
      flex-direction: column;
      gap: 8px;
    }}

    .new-row {{
      display: grid;
      grid-template-columns: 28px auto minmax(0, 1fr);
      gap: 10px;
      align-items: start;
      padding: 9px 10px;
      border: 1px solid rgba(15, 23, 42, 0.06);
      border-radius: 14px;
      background: #fff;
    }}

    .new-num {{
      width: 28px;
      height: 28px;
      border-radius: 999px;
      display: grid;
      place-items: center;
      font-weight: 850;
      color: rgba(15,23,42,0.55);
      background: rgba(15,23,42,0.06);
      font-size: 12px;
      margin-top: 1px;
    }}

    .new-title {{
      font-size: 13px;
      font-weight: 650;
      line-height: 1.45;
      word-break: break-word;
      overflow-wrap: anywhere;
    }}

    .empty {{
      font-size: 13px;
      color: rgba(15,23,42,0.55);
      padding: 4px 2px;
    }}

    .footer {{
      margin-top: 14px;
      text-align: center;
      color: rgba(15,23,42,0.55);
      font-size: 12px;
      line-height: 1.7;
      padding: 14px 10px 8px;
    }}

    .footer a {{
      color: #4f46e5;
      text-decoration: none;
      font-weight: 750;
    }}
    .footer a:hover {{ text-decoration: underline; }}

    .update {{
      margin-top: 6px;
      color: #9a3412;
      font-weight: 650;
    }}

    @media (max-width: 520px) {{
      body {{ padding: 12px 10px; }}
      .meta-grid {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}
      .btns {{
        width: 100%;
        justify-content: flex-start;
      }}
      .btn {{
        flex: 1 1 auto;
      }}
      .news-row {{
        grid-template-columns: 32px minmax(0, 1fr) auto;
        padding: 10px 10px;
      }}
    }}
  </style>
</head>

<body>
  <div class="wrap">
    <header class="hero">
      <div class="hero-inner">
        <div class="hero-top">
          <h1 class="hero-title">热点新闻分析</h1>
          <div class="btns">
            <button class="btn" onclick="saveAsImage()">保存为图片</button>
            <button class="btn" onclick="saveAsMultipleImages()">分段保存</button>
          </div>
        </div>

        <div class="meta-grid" role="group" aria-label="报告信息">
          <div class="meta-card">
            <div class="meta-label">报告类型</div>
            <div class="meta-value">{html_escape(report_type)}</div>
          </div>
          <div class="meta-card">
            <div class="meta-label">新闻总数</div>
            <div class="meta-value">{total_titles} 条</div>
          </div>
          <div class="meta-card">
            <div class="meta-label">热点新闻</div>
            <div class="meta-value">{hot_news_count} 条</div>
          </div>
          <div class="meta-card">
            <div class="meta-label">生成时间</div>
            <div class="meta-value">{html_escape(time_str)}</div>
          </div>
        </div>
      </div>
    </header>

    <main class="content">
      {failed_ids_html}
      {main_html}
    </main>

    <footer class="footer">
      由 <b>TrendRadar</b> 生成 ·
      <a href="https://github.com/sansan0/TrendRadar" target="_blank" rel="noreferrer noopener">GitHub 开源项目</a>
      {update_html}
    </footer>
  </div>

  <script>
    async function saveAsImage() {{
      const button = event.target;
      const originalText = button.textContent;

      try {{
        button.textContent = '生成中...';
        button.disabled = true;
        window.scrollTo(0, 0);

        await new Promise(resolve => setTimeout(resolve, 250));

        // 截图前隐藏按钮
        const btns = document.querySelector('.btns');
        if (btns) btns.style.visibility = 'hidden';
        await new Promise(resolve => setTimeout(resolve, 120));

        const target = document.querySelector('.wrap');
        const canvas = await html2canvas(target, {{
          backgroundColor: '#ffffff',
          scale: 1.5,
          useCORS: true,
          allowTaint: false,
          imageTimeout: 10000,
          logging: false,
          scrollX: 0,
          scrollY: 0,
          windowWidth: window.innerWidth,
          windowHeight: window.innerHeight
        }});

        if (btns) btns.style.visibility = 'visible';

        const link = document.createElement('a');
        const now = new Date();
        const filename = `TrendRadar_热点新闻分析_${{now.getFullYear()}}${{String(now.getMonth()+1).padStart(2,'0')}}${{String(now.getDate()).padStart(2,'0')}}_${{String(now.getHours()).padStart(2,'0')}}${{String(now.getMinutes()).padStart(2,'0')}}.png`;
        link.download = filename;
        link.href = canvas.toDataURL('image/png', 1.0);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        button.textContent = '保存成功!';
        setTimeout(() => {{
          button.textContent = originalText;
          button.disabled = false;
        }}, 1800);

      }} catch (error) {{
        const btns = document.querySelector('.btns');
        if (btns) btns.style.visibility = 'visible';
        button.textContent = '保存失败';
        setTimeout(() => {{
          button.textContent = originalText;
          button.disabled = false;
        }}, 1800);
      }}
    }}

    async function saveAsMultipleImages() {{
      const button = event.target;
      const originalText = button.textContent;
      const wrap = document.querySelector('.wrap');
      const scale = 1.5;
      const maxHeight = 5000 / scale;

      try {{
        button.textContent = '分析中...';
        button.disabled = true;

        const btns = document.querySelector('.btns');
        if (btns) btns.style.visibility = 'hidden';

        await new Promise(resolve => setTimeout(resolve, 180));

        const totalHeight = wrap.scrollHeight;
        const segments = [];
        let start = 0;

        // 简化分段：按高度切，避免复杂 DOM 拆分导致移动端差异
        while (start < totalHeight) {{
          const end = Math.min(start + maxHeight, totalHeight);
          segments.push({{ start, end }});
          start = end;
        }}

        button.textContent = `生成中 (0/${{segments.length}})...`;

        const images = [];
        for (let i = 0; i < segments.length; i++) {{
          button.textContent = `生成中 (${{i+1}}/${{segments.length}})...`;

          const seg = segments[i];
          const canvas = await html2canvas(wrap, {{
            backgroundColor: '#ffffff',
            scale: scale,
            useCORS: true,
            allowTaint: false,
            imageTimeout: 10000,
            logging: false,
            width: wrap.clientWidth,
            height: seg.end - seg.start,
            x: 0,
            y: seg.start,
            scrollX: 0,
            scrollY: 0,
            windowWidth: window.innerWidth,
            windowHeight: window.innerHeight
          }});

          images.push(canvas.toDataURL('image/png', 1.0));
          await new Promise(resolve => setTimeout(resolve, 80));
        }}

        if (btns) btns.style.visibility = 'visible';

        const now = new Date();
        const baseFilename = `TrendRadar_热点新闻分析_${{now.getFullYear()}}${{String(now.getMonth()+1).padStart(2,'0')}}${{String(now.getDate()).padStart(2,'0')}}_${{String(now.getHours()).padStart(2,'0')}}${{String(now.getMinutes()).padStart(2,'0')}}`;

        for (let i = 0; i < images.length; i++) {{
          const link = document.createElement('a');
          link.download = `${{baseFilename}}_part${{i+1}}.png`;
          link.href = images[i];
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          await new Promise(resolve => setTimeout(resolve, 120));
        }}

        button.textContent = `已保存 ${{segments.length}} 张图片!`;
        setTimeout(() => {{
          button.textContent = originalText;
          button.disabled = false;
        }}, 1800);

      }} catch (error) {{
        console.error('分段保存失败:', error);
        const btns = document.querySelector('.btns');
        if (btns) btns.style.visibility = 'visible';
        button.textContent = '保存失败';
        setTimeout(() => {{
          button.textContent = originalText;
          button.disabled = false;
        }}, 1800);
      }}
    }}

    document.addEventListener('DOMContentLoaded', function() {{
      window.scrollTo(0, 0);
    }});
  </script>
</body>
</html>
"""
    return html
