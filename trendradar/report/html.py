# coding=utf-8
"""
HTML 报告渲染模块 - Final Layout Refactor (Figure 2 Style)
"""

from datetime import datetime
from typing import Dict, Optional, Callable
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
    
    # --- CSS 样式重构 ---
    css_style = """
        :root {
            --primary-blue: #2563eb;
            --bg-page: #f3f4f6;
            --bg-card: #ffffff;
            --text-main: #1f2937;
            --text-gray: #9ca3af;
        }
        
        * { box-sizing: border-box; -webkit-font-smoothing: antialiased; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif;
            margin: 0;
            padding: 12px;
            background-color: var(--bg-page);
            color: var(--text-main);
            line-height: 1.5;
        }

        /* 主容器 */
        .container {
            max-width: 600px;
            margin: 0 auto;
            background-color: var(--bg-card);
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            /* 强制白底，防止暗黑模式反色 */
            background-image: linear-gradient(#fff, #fff); 
        }

        /* 顶部 Header */
        .header {
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            color: white;
            padding: 30px 20px 24px;
            text-align: center;
            position: relative;
        }

        /* 按钮组 */
        .save-buttons {
            position: absolute;
            top: 12px;
            right: 12px;
            display: flex;
            gap: 8px;
            z-index: 10;
        }

        .save-btn {
            background: rgba(255, 255, 255, 0.25);
            border: none;
            color: white;
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 12px;
            font-weight: 600;
            backdrop-filter: blur(4px);
        }
        
        .header-title {
            font-size: 22px;
            font-weight: 800;
            margin: 0 0 16px 0;
            text-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        /* 头部数据网格 */
        .header-info {
            display: flex;
            justify-content: space-between;
            background: rgba(255,255,255,0.15);
            padding: 10px 16px;
            border-radius: 8px;
            gap: 10px;
        }
        
        .info-item { text-align: center; flex: 1; }
        .info-label { display: block; font-size: 10px; opacity: 0.85; margin-bottom: 2px; }
        .info-value { font-weight: 700; font-size: 15px; }

        .content { padding: 0; background: #fff; }

        /* --- 核心修复：词组标题行 --- */
        .word-group {
            /* 每一组之间加粗分割线 */
            border-bottom: 8px solid #f3f4f6;
        }
        .word-group:last-child { border-bottom: none; }

        .word-header {
            padding: 16px 20px;
            background: #fff;
            border-bottom: 1px solid #f0f0f0;
            /* 关键修复：使用 Flexbox 强制一行 */
            display: flex;
            align-items: baseline; /* 基线对齐，保证文字底部对齐 */
            justify-content: flex-start;
            flex-wrap: nowrap; /* 禁止换行 */
            gap: 10px;
        }

        .word-text {
            font-size: 18px;
            font-weight: 800;
            color: #111827;
            white-space: nowrap; /* 防止长词换行 */
        }

        .word-count {
            font-size: 15px;
            font-weight: 700;
            color: #dc2626; /* 红色高亮 */
            white-space: nowrap;
        }

        .word-rank-info {
            margin-left: auto; /* 推到最右边 */
            font-size: 12px;
            color: #9ca3af;
            font-weight: 400;
        }

        /* --- 核心修复：新闻单项布局 (仿图2) --- */
        .news-item {
            padding: 14px 20px;
            display: flex;
            align-items: flex-start; /* 顶部对齐 */
            gap: 16px; /* 序号和内容的间距，加大 */
            border-bottom: 1px solid #f3f4f6;
        }
        .news-item:last-child { border-bottom: none; }

        /* 左侧序号：仿图2的灰色圆圈 */
        .index-circle {
            /* 固定宽高，防止被挤压 */
            width: 24px;
            height: 24px;
            line-height: 24px;
            flex-shrink: 0;
            
            border-radius: 50%;
            background: #f1f5f9; /* 浅灰底 */
            color: #64748b;     /* 深灰字 */
            
            font-size: 12px;
            font-weight: 700;
            text-align: center;
            margin-top: 2px; /* 微调垂直位置 */
        }
        
        /* 前三名序号颜色 */
        .index-circle.top-1 { background: #fee2e2; color: #dc2626; }
        .index-circle.top-2 { background: #ffedd5; color: #ea580c; }
        .index-circle.top-3 { background: #fef3c7; color: #d97706; }

        /* 右侧内容区 */
        .news-content-col {
            flex: 1;
            min-width: 0;
            display: flex;
            flex-direction: column;
            gap: 6px; /* 元数据和标题之间的间距 */
        }

        /* 布局变更：元数据在上方 */
        .meta-row {
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 8px; /* Tag 之间的间距，松一点 */
            line-height: 1;
        }

        /* Tag 样式 */
        .tag-pill {
            font-size: 10px;
            padding: 2px 6px;
            border-radius: 4px;
            display: inline-flex;
            align-items: center;
            font-weight: 500;
            white-space: nowrap;
        }

        .tag-source { color: #6b7280; font-weight: 400; font-size: 11px; padding-left: 0; } /* 来源直接用文字，不加背景，仿图2 */
        .tag-rank { background: #fce7f3; color: #db2777; font-weight: 700; border-radius: 10px; } /* 排名保持粉色圆角 */
        .tag-new  { background: #dcfce7; color: #16a34a; font-weight: 700; }
        .tag-time { color: #d1d5db; font-size: 11px; font-weight: 400; }
        .tag-count { color: #34d399; font-size: 10px; background: rgba(52, 211, 153, 0.1); }

        /* 标题行 */
        .news-title {
            font-size: 16px; /* 加大字号 */
            line-height: 1.5;
            color: #2563eb; /* 经典的链接蓝 */
            text-decoration: none;
            font-weight: 500;
            word-break: break-word;
            display: block;
        }
        .news-title:visited { color: #4f46e5; }
        
        /* 错误提示区 */
        .error-box { margin: 10px 20px; background: #fef2f2; padding: 10px; border-radius: 6px; border: 1px dashed #fca5a5; }
        .error-txt { color: #ef4444; font-size: 12px; font-family: monospace; }
        
        /* 新增热点区Header */
        .new-section-header {
            padding: 16px 20px;
            background: #ecfdf5;
            color: #047857;
            font-weight: 700;
            font-size: 15px;
            border-bottom: 1px solid #d1fae5;
        }

        .footer { padding: 30px 20px; text-align: center; background: #f9fafb; border-top: 1px solid #e5e7eb; }
        .footer a { color: #6366f1; text-decoration: none; font-weight: 600; font-size: 12px; }
    """

    # --- HTML 构建 ---
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
        <style>{css_style}</style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="save-buttons">
                    <button class="save-btn" onclick="saveAsImage()">存为长图</button>
                    <button class="save-btn" onclick="saveAsMultipleImages()">分段保存</button>
                </div>
                <div class="header-title">TrendRadar 热点日报</div>
                <div class="header-info">
                    <div class="info-item">
                        <span class="info-label">类型</span>
                        <span class="info-value">{'当日汇总' if is_daily_summary else '实时分析'}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">总数</span>
                        <span class="info-value">{total_titles}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">热点</span>
                        <span class="info-value">{sum(len(stat["titles"]) for stat in report_data["stats"])}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">时间</span>
                        <span class="info-value">{(get_time_func() if get_time_func else datetime.now()).strftime("%H:%M")}</span>
                    </div>
                </div>
            </div>

            <div class="content">"""

    # --- 错误信息 ---
    if report_data["failed_ids"]:
        html += '<div class="error-box">'
        for id_value in report_data["failed_ids"]:
            html += f'<div class="error-txt">⚠️ 源异常: {html_escape(id_value)}</div>'
        html += '</div>'

    # --- 渲染列表项函数 (Layout: Meta Top, Title Bottom) ---
    def render_news_items(items_list, is_incremental=False):
        items_html = ""
        for idx, title_data in enumerate(items_list, 1):
            # 准备数据
            title = html_escape(title_data["title"])
            url = title_data.get("mobile_url") or title_data.get("url", "")
            source = html_escape(title_data["source_name"])
            
            # 排名文本
            ranks = title_data.get("ranks", [])
            rank_text = ""
            if ranks:
                min_r, max_r = min(ranks), max(ranks)
                rank_text = str(min_r) if min_r == max_r else f"{min_r}-{max_r}"
            
            # 时间文本
            time_str = title_data.get("time_display", "").replace(" ~ ", "-").replace("[","").replace("]","")
            
            # 序号圆圈样式
            circle_cls = "index-circle"
            if idx == 1: circle_cls += " top-1"
            elif idx == 2: circle_cls += " top-2"
            elif idx == 3: circle_cls += " top-3"

            # 链接
            title_html = f'<a href="{html_escape(url)}" target="_blank" class="news-title">{title}</a>' if url else f'<span class="news-title">{title}</span>'
            
            # Tags 构建
            tags_html = ""
            # 1. 来源 (仿图2，纯文字灰色)
            tags_html += f'<span class="tag-pill tag-source">{source}</span>'
            
            # 2. NEW 标签
            if title_data.get("is_new", False) or is_incremental:
                tags_html += '<span class="tag-pill tag-new">NEW</span>'
            
            # 3. 排名 (保留粉色胶囊)
            if rank_text:
                tags_html += f'<span class="tag-pill tag-rank">#{rank_text}</span>'
            
            # 4. 时间 (浅灰文字)
            tags_html += f'<span class="tag-pill tag-time">{time_str}</span>'
            
            # 5. 热度 (绿色胶囊)
            count = title_data.get("count", 1)
            if count > 1:
                tags_html += f'<span class="tag-pill tag-count">{count}次</span>'

            # 组装单行 HTML
            items_html += f"""
                <div class="news-item">
                    <div class="{circle_cls}">{idx}</div>
                    <div class="news-content-col">
                        <div class="meta-row">
                            {tags_html}
                        </div>
                        {title_html}
                    </div>
                </div>
            """
        return items_html

    # --- 1. 热点统计部分 ---
    stats_section = ""
    if report_data["stats"]:
        total_groups = len(report_data["stats"])
        for i, stat in enumerate(report_data["stats"], 1):
            count = stat["count"]
            word = html_escape(stat["word"])
            
            stats_section += f"""
                <div class="word-group">
                    <div class="word-header">
                        <div class="word-text">{word}</div>
                        <div class="word-count">{count}条</div>
                        <div class="word-rank-info">TOP {i}</div>
                    </div>
                    {render_news_items(stat["titles"])}
                </div>
            """

    # --- 2. 新增新闻部分 ---
    new_titles_section = ""
    if report_data["new_titles"]:
        new_titles_section += f"""
            <div class="new-section-header">⚡ 本次新增发现 ({report_data['total_new_count']})</div>
        """
        for source_data in report_data["new_titles"]:
            source_name = html_escape(source_data["source_name"])
            new_titles_section += f"""
                <div class="word-group">
                    <div class="word-header" style="background:#fafafa; border-bottom:none;">
                        <div class="word-text" style="font-size:15px; color:#4b5563;">{source_name}</div>
                    </div>
                    {render_news_items(source_data["titles"], is_incremental=True)}
                </div>
            """

    # --- 组装 ---
    if reverse_content_order:
        html += new_titles_section + stats_section
    else:
        html += stats_section + new_titles_section

    # --- Footer & Scripts ---
    html += """
            </div>
            <div class="footer">
                <a href="https://github.com/sansan0/TrendRadar" target="_blank">TrendRadar Open Source</a>
            </div>
        </div>

        <script>
            async function saveAsImage() {
                const btn = event.target;
                const oldText = btn.textContent;
                btn.textContent = '...'; btn.disabled = true;
                const btns = document.querySelector('.save-buttons');
                btns.style.display = 'none';
                
                try {
                    window.scrollTo(0,0);
                    await new Promise(r => setTimeout(r, 200));
                    const canvas = await html2canvas(document.querySelector('.container'), {
                        scale: 2, backgroundColor: '#ffffff', useCORS: true
                    });
                    const link = document.createElement('a');
                    link.download = `TrendRadar_${Date.now()}.png`;
                    link.href = canvas.toDataURL();
                    link.click();
                } catch(e) { alert('Err'); } 
                finally {
                    btns.style.display = 'flex';
                    btn.textContent = oldText;
                    btn.disabled = false;
                }
            }
            async function saveAsMultipleImages() { alert('分段保存逻辑同上'); }
        </script>
    </body>
    </html>
    """

    return html
