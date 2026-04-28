"""
ui_dialogs.py

機材の貸し出しダイアログと返却ダイアログの UI コンポーネント。

各ダイアログは @st.dialog デコレータでラップされており、
app.py のボタン押下時に呼び出されます。
データ操作はすべて data_manager モジュールに委譲します。
"""

from datetime import date, timedelta

import streamlit as st

import data_manager

# ============================================================
# 貸し出しダイアログ
# ============================================================


@st.dialog("📤 機材の貸し出し", width="large")
def rental_dialog() -> None:
    """
    機材の貸し出し情報を入力するダイアログ。

    入力項目:
      - 名前・部署
      - 貸し出し日・返却予定日（Streamlit 標準 date_input）
      - 貸し出す機材（複数選択可、貸出中の機材は除外）

    貸し出し確定時に data_manager.add_rental() を呼び出してログに記録し、
    st.rerun() でメイン画面を更新する。
    """
    available = data_manager.get_available_equipment()

    if available.empty:
        st.warning("現在貸し出し可能な機材がありません。")
        return

    # ── 入力フォーム ──────────────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        person_name = st.text_input(
            "名前 ＊",
            placeholder="例: 山田 太郎",
            key="rental_person_name",
        )
        rental_date = st.date_input(
            "貸し出し日 ＊",
            value=date.today(),
            key="rental_date",
        )

    with col_right:
        department = st.text_input(
            "部署 ＊",
            placeholder="例: 営業部",
            key="rental_department",
        )
        scheduled_return_date = st.date_input(
            "返却予定日 ＊",
            value=date.today() + timedelta(days=7),
            key="rental_return_date",
        )

    # ── 機材選択 ──────────────────────────────────────────
    # 選択肢を "機材ID | 機材名 [カテゴリ]" 形式で表示
    options = [
        f"{row['equipment_id']} | {row['equipment_name']} [{row['category']}]"
        for _, row in available.iterrows()
    ]
    selected_options = st.multiselect(
        "貸し出す機材 ＊（複数選択可）",
        options=options,
        placeholder="機材を選択してください",
        key="rental_equipment_select",
    )

    if selected_options:
        st.caption(f"選択中: {len(selected_options)} 件")

    st.divider()

    # ── 送信ボタン ────────────────────────────────────────
    if st.button("貸し出す", type="primary", use_container_width=True):
        errors = _validate_rental(
            person_name, department, rental_date, scheduled_return_date, selected_options
        )

        if errors:
            for msg in errors:
                st.error(msg)
            return

        equipment_ids = [opt.split(" | ")[0] for opt in selected_options]
        data_manager.add_rental(
            person_name=person_name.strip(),
            department=department.strip(),
            rental_date=rental_date,
            scheduled_return_date=scheduled_return_date,
            equipment_ids=equipment_ids,
        )
        st.toast(
            f"✅ {len(equipment_ids)} 件の機材を貸し出しました。",
            icon="✅",
        )
        st.rerun()


def _validate_rental(
    person_name: str,
    department: str,
    rental_date: date,
    scheduled_return_date: date,
    selected_options: list,
) -> list:
    """
    貸し出しフォームの入力値を検証し、エラーメッセージのリストを返す。

    Returns
    -------
    list[str]
        エラーがなければ空リスト
    """
    errors = []
    if not person_name.strip():
        errors.append("名前を入力してください。")
    if not department.strip():
        errors.append("部署を入力してください。")
    if not selected_options:
        errors.append("機材を 1 つ以上選択してください。")
    if scheduled_return_date < rental_date:
        errors.append("返却予定日は貸し出し日以降に設定してください。")
    return errors


# ============================================================
# 返却ダイアログ
# ============================================================


@st.dialog("📥 機材の返却", width="large")
def return_dialog() -> None:
    """
    返却する機材を選択するダイアログ。

    現在の貸出中レコードを一覧表示し、チェックボックスで複数選択可能。
    返却確定時に data_manager.process_return() を呼び出してログを更新し、
    st.rerun() でメイン画面を更新する。
    """
    active = data_manager.get_active_rentals()

    if active.empty:
        st.info("現在貸し出し中の機材はありません。")
        return

    st.write("返却する機材の行を選択してください（複数選択可）。")

    # ── 貸出中一覧（行選択インタラクティブ表示）────────────
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

    selection = st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="multi-row",
        key="return_df_selection",
    )

    selected_rows: list = selection.selection.rows
    selected_count = len(selected_rows)

    # ── 返却日 ────────────────────────────────────────────
    return_date = st.date_input(
        "返却日 ＊",
        value=date.today(),
        key="return_date",
    )

    st.divider()

    # ── 送信ボタン ────────────────────────────────────────
    btn_label = (
        f"返却する（{selected_count} 件）" if selected_count > 0 else "返却する"
    )
    if st.button(
        btn_label,
        type="primary",
        use_container_width=True,
        disabled=(selected_count == 0),
    ):
        record_ids = active.iloc[selected_rows]["record_id"].tolist()
        data_manager.process_return(record_ids, return_date)
        st.toast(
            f"✅ {selected_count} 件を返却済にしました。",
            icon="✅",
        )
        st.rerun()
