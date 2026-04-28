"""EVSE Map Viewer — Streamlit アプリ本体.

北米の EVSE (Electric Vehicle Supply Equipment) を地図上に表示し、
フィルタリングおよびピンクリックで詳細情報を表示する。
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pydeck as pdk
import streamlit as st

from config import (
    FUEL_TYPE_LABELS,
    METADATA_PATH,
    PARQUET_PATH,
    STATUS_LABELS,
)

# =====================================================================
# ページ設定
# =====================================================================
st.set_page_config(
    page_title="EVSE Map Viewer",
    page_icon="⚡",
    layout="wide",
)

# =====================================================================
# データ読み込み
# =====================================================================

@st.cache_data(show_spinner="Loading EVSE data …")
def load_data() -> pd.DataFrame:
    """Parquet ファイルから EVSE データを読み込む."""
    return pd.read_parquet(PARQUET_PATH)


def load_metadata() -> dict:
    """メタデータ JSON を読み込む."""
    if METADATA_PATH.exists():
        return json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    return {}


def check_data_exists() -> bool:
    """データファイルの存在を確認する."""
    return Path(PARQUET_PATH).exists()


# =====================================================================
# フィルタ
# =====================================================================

def _get_all_connector_types(df: pd.DataFrame) -> list[str]:
    """データ内の全コネクタタイプを収集してソートして返す."""
    types: set[str] = set()
    for val in df["ev_connector_types"].dropna():
        for t in str(val).split(","):
            t = t.strip()
            if t:
                types.add(t)
    return sorted(types)


def _filter_by_connectors(df: pd.DataFrame, selected: list[str]) -> pd.DataFrame:
    """指定コネクタタイプを 1 つ以上持つステーションに絞り込む (OR 条件)."""
    selected_set = set(selected)

    def has_any(val: object) -> bool:
        if not isinstance(val, str) or not val:
            return False
        return bool({t.strip() for t in val.split(",")} & selected_set)

    return df[df["ev_connector_types"].apply(has_any)]


def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    """サイドバーのフィルタを適用して絞り込んだ DataFrame を返す."""
    st.sidebar.header("Filters")

    # --- Fuel Type (デフォルト: Electric) ----------------------------
    if "fuel_type_code" not in df.columns:
        # 旧スキーマの Parquet (fuel_type_code 列なし) の場合は案内を表示
        st.sidebar.warning(
            "Fuel Type フィルタを使うには `python update_data.py` を再実行して"
            "データを更新してください。"
        )
    else:
        fuel_types_in_data = sorted(df["fuel_type_code"].dropna().unique().tolist())
        selected_fuel_types = st.sidebar.multiselect(
            "Fuel Type",
            options=fuel_types_in_data,
            default=[ft for ft in ["ELEC"] if ft in fuel_types_in_data],
            format_func=lambda x: FUEL_TYPE_LABELS.get(x, x),
        )
        if selected_fuel_types:
            df = df[df["fuel_type_code"].isin(selected_fuel_types)]

    # --- 国 -----------------------------------------------------------
    countries = sorted(df["country"].dropna().unique().tolist())
    selected_countries = st.sidebar.multiselect(
        "Country", countries, default=countries,
    )
    if selected_countries:
        df = df[df["country"].isin(selected_countries)]

    # --- 州 (国に連動) ------------------------------------------------
    states = sorted(df["state"].dropna().unique().tolist())
    selected_states = st.sidebar.multiselect("State / Province", states)
    if selected_states:
        df = df[df["state"].isin(selected_states)]

    # --- ステータス ---------------------------------------------------
    status_options = {
        code: f"{code} — {label}"
        for code, label in STATUS_LABELS.items()
        if code in df["status_code"].dropna().unique()
    }
    selected_statuses = st.sidebar.multiselect(
        "Status",
        options=list(status_options.keys()),
        default=[c for c in ["E"] if c in status_options],
        format_func=lambda x: status_options.get(x, x),
    )
    if selected_statuses:
        df = df[df["status_code"].isin(selected_statuses)]

    # --- EV ネットワーク ----------------------------------------------
    networks = sorted(df["ev_network"].dropna().unique().tolist())
    selected_networks = st.sidebar.multiselect("EV Network", networks)
    if selected_networks:
        df = df[df["ev_network"].isin(selected_networks)]

    # --- Charger Types (Level 1 / Level 2 / DC Fast) -----------------
    st.sidebar.subheader("Charger Types")
    _charger_col_map: dict[str, str] = {
        "Level 1": "has_level1",
        "Level 2": "has_level2",
        "DC Fast":  "has_dc_fast",
    }
    selected_chargers = st.sidebar.multiselect(
        "Charger Type", list(_charger_col_map.keys())
    )
    if selected_chargers:
        mask = pd.Series(False, index=df.index)
        for label in selected_chargers:
            mask = mask | df[_charger_col_map[label]]
        df = df[mask]

    # --- Connector Types (OR 条件) ------------------------------------
    st.sidebar.subheader("Connector Types")
    all_connectors = _get_all_connector_types(df)
    selected_connectors = st.sidebar.multiselect("Connector Type", all_connectors)
    if selected_connectors:
        df = _filter_by_connectors(df, selected_connectors)

    # --- Power Output スライダー (max_power_kw 列が存在する場合のみ) --
    if "max_power_kw" in df.columns:
        valid_power = df["max_power_kw"].dropna()
        st.sidebar.subheader("Power Output (kW)")
        if valid_power.empty:
            # 出力データが未取得の場合は固定レンジ 0–350 kW でスライダーを表示
            global_max = 350.0
            st.sidebar.caption("⚠️ 出力データ未取得のためフィルタは無効です")
        else:
            global_max = float(valid_power.max())
        power_range: tuple[float, float] = st.sidebar.slider(
            "Power Output (kW)",
            min_value=0.0,
            max_value=global_max,
            value=(0.0, global_max),
            step=1.0,
            format="%.0f kW",
        )
        low, high = power_range
        # デフォルト(全範囲)以外に絞った場合のみフィルタを適用。
        # max_power_kw が NaN のステーションは常に表示する。
        if not (low == 0.0 and high == global_max):
            df = df[
                (df["max_power_kw"] >= low) & (df["max_power_kw"] <= high)
            ]

    # --- キーワード検索 ------------------------------------------------
    st.sidebar.subheader("Keyword Search")
    kw_name = st.sidebar.text_input("Station Name")
    if kw_name:
        df = df[df["station_name"].str.contains(kw_name, case=False, na=False)]

    kw_city = st.sidebar.text_input("City")
    if kw_city:
        df = df[df["city"].str.contains(kw_city, case=False, na=False)]

    # --- アクセス -----------------------------------------------------
    if st.sidebar.checkbox("Public Access Only"):
        df = df[df["access_code"] == "public"]

    return df.reset_index(drop=True)


# =====================================================================
# 地図表示
# =====================================================================

def build_deck(df: pd.DataFrame) -> pdk.Deck:
    """PyDeck のデッキオブジェクトを構築する."""
    layer = pdk.Layer(
        "ScatterplotLayer",
        id="evse-layer",
        data=df,
        get_position=["longitude", "latitude"],
        get_radius=800,
        radius_min_pixels=2,
        radius_max_pixels=12,
        get_fill_color=[0, 128, 255, 180],
        pickable=True,
        auto_highlight=True,
    )

    view_state = pdk.ViewState(
        latitude=39.8,
        longitude=-98.5,
        zoom=3.5,
        pitch=0,
    )

    tooltip = {
        "html": (
            "<b>{station_name}</b><br/>"
            "{city}, {state} ({country})<br/>"
            "Network: {ev_network}<br/>"
            "Status: {status_code}"
        ),
        "style": {
            "backgroundColor": "#1a1a2e",
            "color": "white",
            "fontSize": "12px",
            "padding": "8px",
        },
    }

    return pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip=tooltip,
    )


# =====================================================================
# データについて
# =====================================================================

@st.dialog("データについて", width="large")
def show_data_info() -> None:
    """データソースに関する注意事項をモーダルで表示する."""
    st.markdown(
        """
### データソース
本アプリのデータは **U.S. Department of Energy — Alternative Fuels Station Locator (AFDC)** の
オープン API を利用して取得しています。

- **ステーション情報**: [AFDC API v1](https://developer.nrel.gov/docs/transportation/alt-fuel-stations-v1/)
- **充電ユニット出力情報**: AFDC ev-charging-units エンドポイント

### 更新頻度
データは `update_data.py` を実行した時点でスナップショットとして保存されます。
リアルタイムでの反映は行われません。

### 注意事項
- 掲載情報は AFDC から提供されたものであり、実際の設備状況と異なる場合があります。
- Power Output (kW) は充電ユニットデータが取得できた場合のみ表示されます。
- 本アプリは情報提供を目的としており、内容の正確性・完全性を保証するものではありません。
        """
    )


# =====================================================================
# 詳細表示
# =====================================================================

def show_detail(record: pd.Series) -> None:
    """選択された EVSE の詳細情報を表示する."""
    st.subheader(f"📍 {record.get('station_name', 'N/A')}")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Address**")
        addr_parts = [
            record.get("street_address", ""),
            record.get("city", ""),
            record.get("state", ""),
            record.get("zip", ""),
            record.get("country", ""),
        ]
        st.write(", ".join(p for p in addr_parts if p))

        st.markdown("**Phone**")
        st.write(record.get("station_phone") or "N/A")

        st.markdown("**Access**")
        st.write(record.get("access_code") or "N/A")

        st.markdown("**Hours**")
        st.write(record.get("access_days_time") or "N/A")

        st.markdown("**Network**")
        network = record.get("ev_network") or "N/A"
        web = record.get("ev_network_web")
        if web:
            st.markdown(f"[{network}]({web})")
        else:
            st.write(network)

        st.markdown("**Pricing**")
        st.write(record.get("ev_pricing") or "N/A")

    with col2:
        st.markdown("**Charging Ports**")
        st.write(f"Level 1: {record.get('ev_level1_evse_num', 0)}")
        st.write(f"Level 2: {record.get('ev_level2_evse_num', 0)}")
        st.write(f"DC Fast: {record.get('ev_dc_fast_num', 0)}")

        st.markdown("**Max Power Output**")
        max_kw = record.get("max_power_kw")
        st.write(f"{max_kw:.0f} kW" if max_kw is not None and not pd.isna(max_kw) else "N/A")

        st.markdown("**Connector Types**")
        st.write(record.get("ev_connector_types") or "N/A")

        st.markdown("**Date Last Confirmed**")
        st.write(record.get("date_last_confirmed") or "N/A")

        st.markdown("**AFDC Updated At**")
        st.write(record.get("updated_at") or "N/A")

        st.markdown("**Open Date**")
        st.write(record.get("open_date") or "N/A")

        st.markdown("**Status**")
        code = record.get("status_code", "")
        st.write(f"{code} — {STATUS_LABELS.get(code, 'Unknown')}")


# =====================================================================
# メイン
# =====================================================================

def main() -> None:
    """アプリのエントリポイント."""
    st.title("⚡ EVSE Map Viewer")
    st.caption("North America — Electric Vehicle Supply Equipment")

    # --- データ存在チェック -------------------------------------------
    if not check_data_exists():
        st.error(
            "データファイルが見つかりません。  \n"
            "先に `python update_data.py` を実行してデータを取得してください。"
        )
        st.stop()

    # --- メタデータ ---------------------------------------------------
    meta = load_metadata()
    if meta:
        cols = st.columns(2)
        cols[0].metric("Last Updated (UTC)", meta.get("last_updated_utc", "N/A"))
        cols[1].metric("Total Records", f"{meta.get('record_count', 0):,}")

    # --- データ読み込み & フィルタ ------------------------------------
    df = load_data()
    filtered = apply_filters(df)

    st.info(f"Showing **{len(filtered):,}** stations (of {len(df):,} total)")

    # --- 地図 ---------------------------------------------------------
    if filtered.empty:
        st.warning("No stations match the current filters.")
        return

    deck = build_deck(filtered)
    selection = st.pydeck_chart(
        deck,
        on_select="rerun",
        selection_mode="single-object",
    )

    # --- 選択されたオブジェクトの詳細表示 ------------------------------
    if selection and selection.selection and selection.selection.get("objects"):
        objects = selection.selection["objects"]
        # ScatterplotLayer → "evse-layer" キーの中にリストが入る
        picked_list = objects.get("evse-layer", [])
        if picked_list:
            picked = picked_list[0]
            # picked は dict なので Series に変換
            record = pd.Series(picked)
            st.divider()
            show_detail(record)

    # --- データについて -----------------------------------------------
    st.divider()
    if st.button("📋 データについて"):
        show_data_info()


if __name__ == "__main__":
    main()
