# coding=utf-8
"""
HTML 报告渲染模块 - Email Compatible Table Layout
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
    """渲染HTML内容 (邮件兼容重构版)"""

    # --- CSS 样式 ---
    css_style = """
        body {
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: #f4f4f5; /* 强制背景灰 */
            color: #18181b;
        }

        /* 容器样式 */
        .wrapper {
            width: 100%;
            table-layout: fixed;
            background-color: #f4f4f5;
            padding-bottom: 40px;
        }

        .main-container {
            background-color: #ffffff;
            margin: 0 auto;
            max-width: 600px;
            width: 100%;
            border-radius: 12px; /* 圆角在某些App可能不显示，但不影响布局 */
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }

        /* 链接样式 */
        a { text-decoration: none; color: #2563eb; }
        a:hover { text-decoration: underline; }

        /* 按钮样式 */
        .btn {
            display: inline-block;
            background: rgba(255,255,255,0.25);
            border: 1px solid rgba(255,255,255,0.4);
            color: #ffffff !important;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
            margin: 0 4px;
            cursor: pointer;
            text-decoration: none;
        }

        /* 移动端优化 */
        @media only screen and (max-width: 480px) {
            .header-stat-val { font-size: 16px !important; }
            .news-title { font-size: 16px !important; line-height: 1.5 !important; }
            .meta-info { font-size: 12px !important; }
        }
    """

    # --- HTML 头部 ---
    html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>热点新闻分析</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
        <style>{css_style}</style>
    </head>
    <body style="margin:0; padding:0; background-color:#f4f4f5;">
        <table class="wrapper" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#f4f4f5">
            <tr>
                <td align="center" style="padding-top: 20px; padding-bottom: 20px;">

                    <table class="main-container" width="600" cellpadding="0" cellspacing="0" border="0" bgcolor="#ffffff" style="max-width:600px; width:100%; border-radius:12px; overflow:hidden; background-color:#ffffff;">

                        <tr>
                            <td background="https://via.placeholder.com/1x1/4f46e5/4f46e5" bgcolor="#4f46e5" style="background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); padding: 30px 20px;">
                                <table width="100%" border="0" cellspacing="0" cellpadding="0">
                                    <tr>
                                        <td align="right" class="save-buttons">
                                            <span class="btn" onclick="saveAsImage()">保存图片</span>
                                            <span class="btn" onclick="saveAsMultipleImages()">分段保存</span>
                                        </td>
                                    </tr>
                                </table>

                                <table width="100%" border="0" cellspacing="0" cellpadding="0">
                                    <tr>
                                        <td align="center" style="color:#ffffff; font-size:24px; font-weight:bold; padding-bottom: 20px; font-family:sans-serif;">
                                            TrendRadar 热点日报
                                        </td>
                                    </tr>
                                </table>

                                <table width="100%" border="0" cellspacing="0" cellpadding="0" bgcolor="rgba(255,255,255,0.15)" style="background-color:rgba(255,255,255,0.15); border-radius:8px;">
                                    <tr>
                                        <td width="25%" align="center" style="padding: 10px 5px; color:#ffffff;">
                                            <div style="font-size:11px; opacity:0.8; margin-bottom:4px;">类型</div>
                                            <div class="header-stat-val" style="font-size:14px; font-weight:bold;">{'当日汇总' if is_daily_summary else '实时'}</div>
                                        </td>
                                        <td width="25%" align="center" style="padding: 10px 5px; color:#ffffff; border-left:1px solid rgba(255,255,255,0.2);">
                                            <div style="font-size:11px; opacity:0.8; margin-bottom:4px;">总数</div>
                                            <div class="header-stat-val" style="font-size:14px; font-weight:bold;">{total_titles}</div>
                                        </td>
                                        <td width="25%" align="center" style="padding: 10px 5px; color:#ffffff; border-left:1px solid rgba(255,255,255,0.2);">
                                            <div style="font-size:11px; opacity:0.8; margin-bottom:4px;">热点</div>
                                            <div class="header-stat-val" style="font-size:14px; font-weight:bold;">{sum(len(stat["titles"]) for stat in report_data["stats"])}</div>
                                        </td>
                                        <td width="25%" align="center" style="padding: 10px 5px; color:#ffffff; border-left:1px solid rgba(255,255,255,0.2);">
                                            <div style="font-size:11px; opacity:0.8; margin-bottom:4px;">时间</div>
                                            <div class="header-stat-val" style="font-size:14px; font-weight:bold;">{(get_time_func() if get_time_func else datetime.now()).strftime("%H:%M")}</div>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>

                        """

    if report_data["failed_ids"]:
        html += """
                        <tr>
                            <td style="padding: 15px 20px; background-color: #fef2f2; border-bottom: 1px solid #fee2e2;">
                                <div style="color: #dc2626; font-size: 13px; font-weight: bold; margin-bottom: 5px;">⚠️ 数据源连接警告</div>
                                <div style="color: #991b1b; font-size: 12px; font-family: monospace;">
        """
        html += ", ".join([html_escape(x) for x in report_data["failed_ids"]])
        html += """
                                </div>
                            </td>
                        </tr>
        """

    # --- 辅助函数：生成新闻列表 (Table Row) ---
    # ✅ 已删除：序号徽章 + 排名徽章
    # ✅ news-item：不再强制上对齐（自然排版）
    def render_news_rows(items_list, is_incremental=False):
        rows_html = ""
        for _, title_data in enumerate(items_list, 1):
            title = html_escape(title_data["title"])
            url = title_data.get("mobile_url") or title_data.get("url", "")
            source = html_escape(title_data["source_name"])
            count = title_data.get("count", 1)

            # 时间处理
            time_display = title_data.get("time_display", "").replace(" ~ ", "-").replace("[", "").replace("]", "")

            rows_html += f"""
                        <tr>
                            <td style="padding: 12px 20px; border-bottom: 1px solid #f3f4f6;">
                                <table width="100%" border="0" cellspacing="0" cellpadding="0">
                                    <tr>
                                        <td>
                                            <div style="margin-bottom: 6px;">
                                                <a href="{url}" target="_blank" class="news-title" style="display:block; color:#18181b; font-size:15px; font-weight:500; text-decoration:none; line-height:1.4;">{title}</a>
                                            </div>

                                            <div>
                                                {f'<span style="display:inline-block; background:#dcfce7; color:#166534; font-size:10px; padding:2px 6px; border-radius:4px; font-weight:bold; margin-right:4px;">NEW</span>' if (title_data.get("is_new") or is_incremental) else ''}

                                                <span style="display:inline-block; background:#e0e7ff; color:#4338ca; font-size:10px; padding:2px 6px; border-radius:4px; margin-right:4px;">{source}</span>

                                                <span class="meta-info" style="color:#9ca3af; font-size:11px; margin-right:4px;">{time_display}</span>

                                                <span class="meta-info" style="color:#9ca3af; font-size:11px;">{count}次</span>
                                            </div>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
            """
        return rows_html

    # --- 构建内容主体 ---

    # 1. 热点统计
    stats_content = ""
    if report_data["stats"]:
        for i, stat in enumerate(report_data["stats"], 1):
            word = html_escape(stat["word"])
            count = stat["count"]

            # ✅ word-header：上下居中（valign + vertical-align）
            stats_content += f"""
                        <tr>
                            <td bgcolor="#fafafa" style="padding: 12px 20px; border-bottom: 1px solid #f0f0f0; border-top: { '8px solid #f4f4f5' if i > 1 else 'none' };">

                                <table width="100%" border="0" cellspacing="0" cellpadding="0">
                                    <tr>
                                        <td valign="middle" style="vertical-align: middle; line-height: 1.2;">
                                            <span style="font-size:16px; font-weight:bold; color:#111827;">{word}</span>
                                            <span style="background:#f3f4f6; color:#6b7280; font-size:12px; padding:2px 8px; border-radius:12px; margin-left:8px; font-weight:bold;">{count}条</span>
                                        </td>
                                        <td valign="middle" align="right" style="vertical-align: middle; font-size:12px; color:#9ca3af; line-height: 1.2;">
                                            TOP {i}
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        {render_news_rows(stat["titles"])}
            """

    # 2. 新增热点
    new_content = ""
    if report_data["new_titles"]:
        new_content += f"""
                        <tr>
                            <td bgcolor="#ecfdf5" style="padding: 15px 20px; color:#065f46; font-weight:bold; font-size:15px; border-bottom: 1px solid #d1fae5; border-top: 8px solid #f4f4f5;">
                                ⚡ 本次新增 ({report_data['total_new_count']})
                            </td>
                        </tr>
        """
        for source_data in report_data["new_titles"]:
            source_name = html_escape(source_data["source_name"])
            new_content += f"""
                        <tr>
                            <td bgcolor="#f9fafb" style="padding: 8px 20px; color:#6b7280; font-size:12px; font-weight:bold; border-bottom: 1px solid #f3f4f6;">
                                {source_name}
                            </td>
                        </tr>
                        {render_news_rows(source_data["titles"], is_incremental=True)}
            """

    # 组合顺序
    if reverse_content_order:
        html += new_content + stats_content
    else:
        html += stats_content + new_content

    # --- HTML 尾部 ---
    html += f"""
                        <tr>
                            <td align="center" style="padding: 30px 20px; background-color: #fafafa; border-top: 1px solid #e5e7eb;">
                                <div style="font-size:12px; color:#9ca3af; margin-bottom:8px;">Generated by TrendRadar</div>
                                <div>
                                    <a href="https://github.com/sansan0/TrendRadar" target="_blank" style="color:#4f46e5; font-size:12px; font-weight:bold;">GitHub Repo</a>
                                </div>
    """
    if update_info:
        html += f"""
                                <div style="margin-top:10px;">
                                    <span style="background:#fff7ed; color:#c2410c; border:1px solid #ffedd5; padding:4px 10px; border-radius:12px; font-size:11px;">
                                        v{update_info['current_version']} → v{update_info['remote_version']}
                                    </span>
                                </div>
        """

    html += """
                            </td>
                        </tr>
                    </table>
                    </td>
            </tr>
        </table>
        <script>
            async function saveAsImage() {
                const btn = event.target;
                const originalText = btn.textContent;
                btn.textContent = '生成中...';

                // 截图前隐藏按钮
                const btnsContainer = document.querySelector('.save-buttons');
                const originalDisplay = btnsContainer.style.display;
                btnsContainer.style.display = 'none';

                try {
                    window.scrollTo(0,0);
                    await new Promise(r => setTimeout(r, 200));

                    const element = document.querySelector('.main-container');
                    const canvas = await html2canvas(element, {
                        scale: 2,
                        backgroundColor: '#ffffff',
                        useCORS: true
                    });

                    const link = document.createElement('a');
                    link.download = `TrendRadar_${new Date().getTime()}.png`;
                    link.href = canvas.toDataURL('image/png');
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                } catch(e) {
                    alert('截图失败');
                    console.error(e);
                } finally {
                    btnsContainer.style.display = originalDisplay;
                    btn.textContent = originalText;
                }
            }

            async function saveAsMultipleImages() {
                alert('请使用保存图片功能，分段保存逻辑与主逻辑类似');
            }
        </script>
    </body>
    </html>
    """

    return html
