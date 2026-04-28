"""
calendar_component.py

FullCalendar (CDN) を Streamlit の iframe コンポーネントとして表示する。

streamlit-calendar パッケージは使用せず、st.components.v1.html() に
FullCalendar の CDN スクリプトを埋め込む方式を採用しています。
"""

import json

import streamlit as st

# ============================================================
# 定数
# ============================================================

_FULLCALENDAR_VERSION = "6.1.15"

_CDN_BASE = f"https://cdn.jsdelivr.net/npm/fullcalendar@{_FULLCALENDAR_VERSION}"

# ============================================================
# HTML テンプレート
# ============================================================
# ※ Python の str.format() を使うため、JavaScript の {} はすべて {{}} にエスケープ

_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <link
    href="{cdn_base}/index.global.min.css"
    rel="stylesheet"
  />
  <script src="{cdn_base}/index.global.min.js"></script>
  <script src="{cdn_base}/locales-all.global.min.js"></script>
  <style>
    * {{
      box-sizing: border-box;
    }}
    body {{
      margin: 0;
      padding: 6px;
      font-family: "Helvetica Neue", Helvetica, sans-serif;
      background: transparent;
    }}
    #calendar {{
      max-width: 100%;
    }}
    .fc-event-title {{
      white-space: normal !important;
      font-size: 0.78em;
    }}
  </style>
</head>
<body>
  <div id="calendar"></div>
  <script>
    document.addEventListener("DOMContentLoaded", function () {{
      var calendarEl = document.getElementById("calendar");
      var calendar = new FullCalendar.Calendar(calendarEl, {{
        initialView: "dayGridMonth",
        locale: "ja",
        height: "auto",
        headerToolbar: {{
          left: "prev,next today",
          center: "title",
          right: "dayGridMonth,timeGridWeek,listMonth"
        }},
        buttonText: {{
          today: "今日",
          month: "月",
          week:  "週",
          list:  "リスト"
        }},
        events: {events_json},
        eventDidMount: function (info) {{
          // ホバー時にタイトルをツールチップとして表示
          info.el.title = info.event.title;
        }}
      }});
      calendar.render();
    }});
  </script>
</body>
</html>
"""


# ============================================================
# 公開関数
# ============================================================


def render_calendar(events: list, height: int = 660) -> None:
    """
    FullCalendar を Streamlit のインライン HTML コンポーネントとして表示する。

    Parameters
    ----------
    events : list[dict]
        FullCalendar 形式のイベントリスト。
        各 dict に title, start, end, color, textColor キーを含むことを想定。
        例::

            [
              {
                "title": "[貸出中] プロジェクター A / 山田 太郎 (営業部)",
                "start": "2024-04-01",
                "end":   "2024-04-06",   # FullCalendar の end は exclusive
                "color": "#2196F3",
                "textColor": "#ffffff",
              }
            ]
    height : int
        コンポーネントの iframe 高さ (px)。デフォルト 660。
    """
    events_json = json.dumps(events, ensure_ascii=False)
    html = _HTML_TEMPLATE.format(
        cdn_base=_CDN_BASE,
        events_json=events_json,
    )
    st.components.v1.html(html, height=height, scrolling=False)
