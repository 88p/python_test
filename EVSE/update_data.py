"""EVSE データ更新スクリプト.

AFDC API から北米の EVSE データを取得し、Parquet 形式でローカルに保存する。
Windows タスクスケジューラ等で週次実行する想定。
"""

from __future__ import annotations

import io
import json
import logging
import sys
from datetime import datetime, timezone

import pandas as pd
import requests

from config import (
    AFDC_API_KEY,
    AFDC_API_PARAMS,
    AFDC_API_URL,
    AFDC_EV_UNITS_URL,
    DATA_DIR,
    EV_POWER_KW_COLUMNS,
    KEEP_COLUMNS,
    METADATA_PATH,
    PARQUET_PATH,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# API レスポンスのタイムアウト (秒)
REQUEST_TIMEOUT = 300


# =====================================================================
# データ取得
# =====================================================================
def fetch_stations() -> list[dict]:
    """AFDC API から EVSE ステーション一覧を取得して返す."""
    logger.info("AFDC API にリクエストを送信しています …")
    logger.info("  URL: %s", AFDC_API_URL)
    logger.info("  パラメータ: %s", {k: v for k, v in AFDC_API_PARAMS.items() if k != "api_key"})

    resp = requests.get(
        AFDC_API_URL,
        params=AFDC_API_PARAMS,
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()

    data = resp.json()
    stations: list[dict] = data.get("fuel_stations", [])
    total = data.get("total_results", len(stations))
    logger.info("取得完了: total_results=%s, 実レコード数=%s", total, len(stations))
    return stations


# =====================================================================
# ev-charging-units 取得
# =====================================================================

def fetch_ev_charging_units() -> pd.DataFrame:
    """ev-charging-units エンドポイントから CSV を取得し DataFrame で返す."""
    params = {
        "api_key": AFDC_API_KEY,
        "country": "all",
        "status": "all",
        "limit": "all",
    }
    logger.info("ev-charging-units エンドポイントにリクエスト中 …")
    resp = requests.get(AFDC_EV_UNITS_URL, params=params, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    df = pd.read_csv(io.StringIO(resp.text))
    logger.info("ev-charging-units 取得完了: %s 行", len(df))
    return df


def compute_power_by_station(units_df: pd.DataFrame) -> pd.Series:
    """充電ユニット DataFrame からステーションごとの最大出力 (kW) を返す.

    戻り値は station id (整数) をインデックスに持つ Series。
    """
    if "ID" not in units_df.columns:
        logger.warning("ev-charging-units CSV に 'ID' 列が見つかりません")
        return pd.Series(dtype="float64")

    power_cols = [c for c in EV_POWER_KW_COLUMNS if c in units_df.columns]
    if not power_cols:
        logger.warning("ev-charging-units CSV に出力電力列が見つかりません")
        return pd.Series(dtype="float64")

    work = units_df[["ID"] + power_cols].copy()
    for col in power_cols:
        work[col] = pd.to_numeric(work[col], errors="coerce")
    work["_row_max"] = work[power_cols].max(axis=1)
    work = work.sort_values("_row_max", ascending=False)
    result = work.drop_duplicates(subset=["ID"], keep="first").set_index("ID")["_row_max"]
    logger.info("出力電力データ: %s ステーション分 (最大 %.0f kW)",
                len(result), result.max() if not result.empty else 0)
    return result


# =====================================================================
# データ整形
# =====================================================================
def transform(
    stations: list[dict],
    power_by_station: pd.Series | None = None,
) -> pd.DataFrame:
    """取得した生データを整形し、必要カラムのみの DataFrame を返す."""
    df = pd.DataFrame(stations)

    # --- ev_connector_types: list → カンマ区切り文字列 ----------------
    if "ev_connector_types" in df.columns:
        df["ev_connector_types"] = df["ev_connector_types"].apply(
            lambda v: ", ".join(v) if isinstance(v, list) else ""
        )

    # --- 必要カラムだけ抽出 (存在しないカラムは NaN で埋める) ----------
    for col in KEEP_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA
    df = df[KEEP_COLUMNS].copy()

    # --- max_power_kw: ev-charging-units データを id で結合 ----------
    if power_by_station is not None and not power_by_station.empty:
        df["max_power_kw"] = df["id"].map(power_by_station)
    else:
        df["max_power_kw"] = pd.NA

    # --- 緯度経度を数値変換 & 欠損行を除外 ---------------------------
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    before = len(df)
    df = df.dropna(subset=["latitude", "longitude"]).reset_index(drop=True)
    dropped = before - len(df)
    if dropped:
        logger.info("緯度経度欠損により %s 件除外", dropped)

    # --- 充電種別フラグ -----------------------------------------------
    df["ev_level1_evse_num"] = pd.to_numeric(df["ev_level1_evse_num"], errors="coerce").fillna(0).astype(int)
    df["ev_level2_evse_num"] = pd.to_numeric(df["ev_level2_evse_num"], errors="coerce").fillna(0).astype(int)
    df["ev_dc_fast_num"] = pd.to_numeric(df["ev_dc_fast_num"], errors="coerce").fillna(0).astype(int)

    df["has_level1"] = df["ev_level1_evse_num"] > 0
    df["has_level2"] = df["ev_level2_evse_num"] > 0
    df["has_dc_fast"] = df["ev_dc_fast_num"] > 0

    logger.info("整形後のレコード数: %s", len(df))
    return df


# =====================================================================
# 保存
# =====================================================================
def save(df: pd.DataFrame) -> None:
    """DataFrame を Parquet で保存し、メタデータ JSON を書き出す."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    df.to_parquet(PARQUET_PATH, index=False, engine="pyarrow")
    logger.info("Parquet 保存完了: %s", PARQUET_PATH)

    meta = {
        "last_updated_utc": datetime.now(timezone.utc).isoformat(),
        "record_count": len(df),
    }
    METADATA_PATH.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("メタデータ保存完了: %s", METADATA_PATH)


# =====================================================================
# メイン
# =====================================================================
def main() -> None:
    """データ更新の一連の処理を実行する."""
    try:
        stations = fetch_stations()
    except requests.RequestException as exc:
        logger.error("stations API リクエストに失敗しました: %s", exc)
        sys.exit(1)

    # ev-charging-units は取得失敗してもスキップして続行する
    power_by_station: pd.Series | None = None
    try:
        units_df = fetch_ev_charging_units()
        power_by_station = compute_power_by_station(units_df)
    except Exception as exc:
        logger.warning(
            "ev-charging-units の取得に失敗しました (スキップ): %s", exc
        )

    try:
        df = transform(stations, power_by_station=power_by_station)
        save(df)
        logger.info("===== 更新完了 =====")
    except (KeyError, ValueError) as exc:
        logger.error("データ変換中にエラーが発生しました: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
