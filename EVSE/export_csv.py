"""Parquet → CSV エクスポートスクリプト.

data/evse_latest.parquet を読み込み、同ディレクトリに evse_latest.csv として出力する。
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from config import PARQUET_PATH

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

CSV_PATH = Path(PARQUET_PATH).with_suffix(".csv")


def main() -> None:
    if not Path(PARQUET_PATH).exists():
        logger.error("Parquet ファイルが見つかりません: %s", PARQUET_PATH)
        raise SystemExit(1)

    logger.info("読み込み中: %s", PARQUET_PATH)
    df = pd.read_parquet(PARQUET_PATH)
    logger.info("レコード数: %s 行 / %s 列", len(df), len(df.columns))

    df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
    logger.info("CSV 出力完了: %s", CSV_PATH)


if __name__ == "__main__":
    main()
