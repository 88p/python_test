"""EVSE Map Viewer — 設定・定数定義."""

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# パス
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
PARQUET_PATH = DATA_DIR / "evse_latest.parquet"
METADATA_PATH = DATA_DIR / "metadata.json"

# ---------------------------------------------------------------------------
# AFDC API
# ---------------------------------------------------------------------------
AFDC_API_KEY: str = os.environ.get("AFDC_API_KEY", "DEMO_KEY")
AFDC_API_URL: str = (
    "https://developer.nlr.gov/api/alt-fuel-stations/v1.json"
)
AFDC_EV_UNITS_URL: str = (
    "https://developer.nlr.gov/api/alt-fuel-stations/v1/ev-charging-units.csv"
)
AFDC_API_PARAMS: dict[str, str] = {
    "api_key": AFDC_API_KEY,
    "fuel_type": "all",
    "country": "all",
    "status": "all",
    "limit": "all",
}

# ---------------------------------------------------------------------------
# 保持カラム (Parquet に保存する列)
# ---------------------------------------------------------------------------
KEEP_COLUMNS: list[str] = [
    "id",
    "fuel_type_code",
    "station_name",
    "street_address",
    "city",
    "state",
    "zip",
    "country",
    "latitude",
    "longitude",
    "station_phone",
    "access_code",
    "access_days_time",
    "status_code",
    "groups_with_access_code",
    "ev_level1_evse_num",
    "ev_level2_evse_num",
    "ev_dc_fast_num",
    "ev_connector_types",
    "ev_network",
    "ev_network_web",
    "ev_pricing",
    "restricted_access",
    "date_last_confirmed",
    "updated_at",
    "open_date",
]

# ---------------------------------------------------------------------------
# ev-charging-units CSV の出力電力カラム名
# ---------------------------------------------------------------------------
EV_POWER_KW_COLUMNS: list[str] = [
    "EV J1772 Power Output (kW)",
    "EV CCS Power Output (kW)",
    "EV CHAdeMO Power Output (kW)",
    "EV J3400 Power Output (kW)",
    "EV J3271 Power Output (kW)",
]

# ---------------------------------------------------------------------------
# 燃料タイプのラベル
# ---------------------------------------------------------------------------
FUEL_TYPE_LABELS: dict[str, str] = {
    "ELEC": "⚡ Electric",
    "E85":  "🌽 Ethanol (E85)",
    "CNG":  "🔵 CNG",
    "LPG":  "🟠 Propane (LPG)",
    "BD":   "🟡 Biodiesel",
    "LNG":  "🔷 LNG",
    "HY":   "💧 Hydrogen",
    "RD":   "🟢 Renewable Diesel",
}

# ---------------------------------------------------------------------------
# ステータスコードのラベル
# ---------------------------------------------------------------------------
STATUS_LABELS: dict[str, str] = {
    "E": "Open",
    "P": "Planned",
    "T": "Temporarily Unavailable",
}
