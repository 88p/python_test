"""
data_manager.py

機材貸し出し管理システム — データ操作ロジック

このモジュールはすべての CSV 読み書きと集計処理を担当します。
UI 層はこのモジュールにのみ依存し、CSV 操作を直接行いません。
"""

import csv
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

# ============================================================
# 定数
# ============================================================

BASE_DIR = Path(__file__).parent

# ファイルパス
EQUIPMENT_CSV = BASE_DIR / "equipment_list.csv"
RENTAL_LOG_CSV = BASE_DIR / "rental_log.csv"

# 機材リスト カラム名
EQUIPMENT_COLS = ["equipment_id", "equipment_name", "category", "notes"]

# 貸し出しログ カラム名
LOG_COLS = [
    "record_id",            # レコード固有 UUID
    "rental_id",            # 同一操作グループ UUID（複数機材の一括貸し出しを紐付け）
    "equipment_id",
    "equipment_name",
    "person_name",
    "department",
    "purpose",              # 借用目的
    "rental_date",
    "scheduled_return_date",
    "actual_return_date",   # 未返却は空文字
    "rental_timestamp",     # 操作日時
    "return_timestamp",     # 返却操作日時（未返却は空文字）
    "status",               # STATUS_RENTING / STATUS_RETURNED
]

STATUS_RENTING = "貸出中"
STATUS_RETURNED = "返却済"

# カレンダー表示用 カテゴリ別カラーパレット（不足分はループして再利用）
_CATEGORY_COLOR_PALETTE = [
    "#2196F3",  # Blue
    "#4CAF50",  # Green
    "#FF9800",  # Orange
    "#9C27B0",  # Purple
    "#F44336",  # Red
    "#00BCD4",  # Cyan
    "#795548",  # Brown
    "#607D8B",  # Blue Grey
]

# 返却済イベントの色
_COLOR_RETURNED = "#adb5bd"


# ============================================================
# 初期化ヘルパー
# ============================================================


def _ensure_log_file_exists() -> None:
    """rental_log.csv が存在しない場合、ヘッダー行だけの空ファイルを作成する。"""
    if not RENTAL_LOG_CSV.exists():
        with open(RENTAL_LOG_CSV, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(LOG_COLS)


# ============================================================
# データ読み込み
# ============================================================


def load_equipment_list() -> pd.DataFrame:
    """
    機材リスト CSV を読み込んで DataFrame を返す。

    Returns
    -------
    pd.DataFrame
        カラム: equipment_id, equipment_name, category, notes
    """
    if not EQUIPMENT_CSV.exists():
        return pd.DataFrame(columns=EQUIPMENT_COLS)
    return pd.read_csv(EQUIPMENT_CSV, dtype=str, encoding="utf-8-sig").fillna("")


def load_rental_log() -> pd.DataFrame:
    """
    貸し出しログ CSV を読み込んで DataFrame を返す。
    ファイルが存在しない場合は自動作成する。

    Returns
    -------
    pd.DataFrame
        カラム: LOG_COLS 参照
    """
    _ensure_log_file_exists()
    df = pd.read_csv(RENTAL_LOG_CSV, dtype=str, encoding="utf-8-sig").fillna("")
    # カラムが不足している場合に備えて補完
    for col in LOG_COLS:
        if col not in df.columns:
            df[col] = ""
    return df[LOG_COLS]


# ============================================================
# 集計・フィルタ
# ============================================================


def get_active_rentals() -> pd.DataFrame:
    """
    現在貸出中のレコードを返す。

    Returns
    -------
    pd.DataFrame
        status == STATUS_RENTING のレコード
    """
    df = load_rental_log()
    return df[df["status"] == STATUS_RENTING].reset_index(drop=True)


def get_available_equipment() -> pd.DataFrame:
    """
    現在貸し出し可能な機材（貸出中でない）を返す。

    Returns
    -------
    pd.DataFrame
        貸出中の equipment_id を除いた機材リスト
    """
    equipment = load_equipment_list()
    active = get_active_rentals()
    rented_ids = set(active["equipment_id"].tolist())
    available = equipment[~equipment["equipment_id"].isin(rented_ids)]
    return available.reset_index(drop=True)


# ============================================================
# データ書き込み
# ============================================================


def add_rental(
    person_name: str,
    department: str,
    purpose: str,
    rental_date: date,
    scheduled_return_date: date,
    equipment_ids: list,
) -> None:
    """
    貸し出し情報をログに追記する。

    同一操作で選択した機材は同じ rental_id で紐付けられる。

    Parameters
    ----------
    person_name : str
        借用者氏名
    department : str
        借用者部署
    purpose : str
        借用目的
    rental_date : date
        貸し出し日
    scheduled_return_date : date
        返却予定日
    equipment_ids : list[str]
        貸し出す機材 ID のリスト
    """
    _ensure_log_file_exists()
    equipment_map = _build_equipment_name_map()
    rental_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    rows = []
    for eq_id in equipment_ids:
        rows.append(
            {
                "record_id": str(uuid.uuid4()),
                "rental_id": rental_id,
                "equipment_id": eq_id,
                "equipment_name": equipment_map.get(eq_id, ""),
                "person_name": person_name,
                "department": department,
                "purpose": purpose,
                "rental_date": str(rental_date),
                "scheduled_return_date": str(scheduled_return_date),
                "actual_return_date": "",
                "rental_timestamp": timestamp,
                "return_timestamp": "",
                "status": STATUS_RENTING,
            }
        )

    with open(RENTAL_LOG_CSV, mode="a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=LOG_COLS)
        writer.writerows(rows)


def process_return(record_ids: list, actual_return_date: date) -> None:
    """
    指定された record_id の行を返却済に更新する。

    Parameters
    ----------
    record_ids : list[str]
        返却対象の record_id リスト
    actual_return_date : date
        実際の返却日
    """
    df = load_rental_log()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mask = df["record_id"].isin(record_ids)
    df.loc[mask, "actual_return_date"] = str(actual_return_date)
    df.loc[mask, "return_timestamp"] = timestamp
    df.loc[mask, "status"] = STATUS_RETURNED
    df.to_csv(RENTAL_LOG_CSV, index=False, encoding="utf-8-sig")


# ============================================================
# カレンダー用イベント生成
# ============================================================


def get_calendar_events() -> list:
    """
    FullCalendar 用のイベント dict リストを返す。

    貸出中・返却済を含む全レコードを対象とする。
    FullCalendar の all-day イベントでは end が exclusive なので
    scheduled_return_date に 1 日加算する。

    Returns
    -------
    list[dict]
        FullCalendar の events 配列として渡せる dict リスト
    """
    df = load_rental_log()
    if df.empty:
        return []

    equipment = load_equipment_list()
    category_color_map = _build_category_color_map(equipment)
    eq_category_map = dict(zip(equipment["equipment_id"], equipment["category"]))

    events = []
    for _, row in df.iterrows():
        try:
            # FullCalendar の end は exclusive → 返却予定日の翌日を設定
            fc_end = (
                datetime.strptime(row["scheduled_return_date"], "%Y-%m-%d").date()
                + timedelta(days=1)
            )
        except ValueError:
            continue  # 日付が不正なレコードはスキップ

        category = eq_category_map.get(row["equipment_id"], "")

        if row["status"] == STATUS_RENTING:
            title = (
                f"[貸出中] {row['equipment_name']} "
                f"/ {row['person_name']} ({row['department']})"
            )
            color = category_color_map.get(category, _CATEGORY_COLOR_PALETTE[0])
        else:
            title = (
                f"[返却済] {row['equipment_name']} "
                f"/ {row['person_name']} ({row['department']})"
            )
            color = _COLOR_RETURNED

        events.append(
            {
                "title": title,
                "start": row["rental_date"],
                "end": str(fc_end),
                "color": color,
                "textColor": "#ffffff",
            }
        )

    return events


# ============================================================
# プライベートヘルパー
# ============================================================


def _build_equipment_name_map() -> dict:
    """equipment_id → equipment_name のマップを返す。"""
    equipment = load_equipment_list()
    return dict(zip(equipment["equipment_id"], equipment["equipment_name"]))


def _build_category_color_map(equipment: pd.DataFrame) -> dict:
    """カテゴリ名 → カラーコード のマップを生成する。"""
    categories = equipment["category"].unique().tolist()
    return {
        cat: _CATEGORY_COLOR_PALETTE[i % len(_CATEGORY_COLOR_PALETTE)]
        for i, cat in enumerate(categories)
    }
