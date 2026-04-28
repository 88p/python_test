"""
app.py

機材貸し出し管理システム — メインアプリケーション

起動方法:
    streamlit run app.py

画面構成:
    1. ヘッダー + 操作ボタン行（貸し出し / 返却）
    2. 現在の貸出状況テーブル
    3. 貸出カレンダー（FullCalendar CDN）
"""

import streamlit as st

import data_manager
from calendar_component import render_calendar
from ui_dialogs import rental_dialog, return_dialog

# ============================================================
# ページ設定（スクリプト最初に一度だけ呼び出す）
# ============================================================

st.set_page_config(
    page_title="機材貸し出し管理システム",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# カスタム CSS（最小限）
# ============================================================

_CUSTOM_CSS = """
<style>
  /* ボタン間のギャップ調整 */
  div[data-testid="column"] > div > div > div > button {
    margin-top: 0;
  }
</style>
"""


# ============================================================
# メイン画面
# ============================================================


def _render_header() -> None:
    """タイトルと操作ボタン行を表示する。"""
    st.title("📦 機材貸し出し管理システム")

    col_rent, col_return, col_spacer = st.columns([1, 1, 6])

    with col_rent:
        if st.button("📤 貸し出し", type="primary", use_container_width=True):
            rental_dialog()

    with col_return:
        if st.button("📥 返却", type="secondary", use_container_width=True):
            return_dialog()


def _render_active_rentals() -> None:
    """現在の貸出状況テーブルを表示する。"""
    st.subheader("📋 現在の貸出状況")

    active = data_manager.get_active_rentals()

    if active.empty:
        st.info("現在貸し出し中の機材はありません。")
        return

    display_df = active[
        [
            "equipment_id",
            "equipment_name",
            "person_name",
            "department",
            "rental_date",
            "scheduled_return_date",
        ]
    ].rename(
        columns={
            "equipment_id": "機材ID",
            "equipment_name": "機材名",
            "person_name": "氏名",
            "department": "部署",
            "rental_date": "貸出日",
            "scheduled_return_date": "返却予定日",
        }
    )

    st.dataframe(display_df, use_container_width=True, hide_index=True)


def _render_calendar() -> None:
    """貸出カレンダー（FullCalendar）を表示する。"""
    st.subheader("📅 貸出カレンダー")

    events = data_manager.get_calendar_events()

    if not events:
        st.info("表示できる貸し出し情報がありません。")
        # イベントが空でもカレンダー自体は表示する
    render_calendar(events)


def _render_equipment_list() -> None:
    """機材リストを折りたたみ表示する。"""
    with st.expander("🔧 機材リスト（参照用）", expanded=False):
        equipment = data_manager.load_equipment_list()
        if equipment.empty:
            st.warning(
                f"機材リストファイルが見つかりません: `{data_manager.EQUIPMENT_CSV}`"
            )
        else:
            st.dataframe(
                equipment.rename(
                    columns={
                        "equipment_id": "機材ID",
                        "equipment_name": "機材名",
                        "category": "カテゴリ",
                        "notes": "備考",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )


def main() -> None:
    """アプリケーションのエントリーポイント。"""
    st.markdown(_CUSTOM_CSS, unsafe_allow_html=True)

    _render_header()

    st.divider()

    _render_active_rentals()

    st.divider()

    _render_calendar()

    st.divider()

    _render_equipment_list()


# ============================================================
# エントリーポイント
# ============================================================

main()
