import json
import pandas as pd
import random
from pathlib import Path
from typing import Union

def main():
    df = make_df_from_schema("labels.json")
    for i in range(5):
        df = make_df_1record(df)
    
    # CSVエクスポート
    out_path = Path("labels_export.csv")
    if df is None or df.empty:
        print("DataFrame is empty, skipping CSV export.")
    else:
        df.to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"Exported DataFrame to: {out_path.resolve()}")

# schema.json から DataFrame を作成
def make_df_from_schema(json_path: Union[str, Path]) -> pd.DataFrame:
    data = json.loads(Path(json_path).read_text(encoding="utf-8"))
    cols = data["columns"]

    if not cols:
        return pd.DataFrame()

    # 文字列リスト形式にも対応
    if isinstance(cols[0], str):
        return pd.DataFrame(columns=cols)

    names = [c["name"] for c in cols]
    dtypes = {c["name"]: c["dtype"] for c in cols if "dtype" in c}

    df = pd.DataFrame(columns=names)

    # データ型を設定
    for k, v in dtypes.items():
        if v.startswith("datetime"):
            continue
        df[k] = df[k].astype(v)

    return df


# DataFrame に1レコード追加
def make_df_1record(df: pd.DataFrame) -> pd.DataFrame:
    if df is None:
        return df
    
    # 今日の日付文字列を取得
    today_str = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    row = {}
    for col in df.columns:
        # ラベル名ごとに個別処理する（必要に応じてラベル名を追加・編集してください）
        if col in ("VehicleNo"):
            #row[col] = random.randint(1, 10)
            row[col] = 1
            continue
        if col in ("Date"):
            row[col] = today_str
            continue
        if col in ("EVSE_MACADDRESS_1", "EVSE_MACADDRESS_2", "EVSE_MACADDRESS_3", "EVSE_MACADDRESS_4"):
            # ランダムなMACアドレスを生成してStringDtypeで格納
            mac = ":".join(f"{random.randint(0,255):02X}" for _ in range(6))
            i = pd.Series(mac, dtype="string").iat[0]
            row[col] = i
            continue
        if col in ("AllConnectionDetection_1", "AllConnectionDetection_2", "AllConnectionDetection_3", "AllConnectionDetection_4"):
            #前回値を取得してインクリメント
            if df.empty:
                prev = 0
            else:
                last = df[col].iloc[-1]
                num = pd.to_numeric(last, errors="coerce")
                prev = int(num) if pd.notna(num) else 0
            row[col] = prev + 1
            #row[col] = 1
            continue
        if col.endswith("_flag") or col.startswith("is_"):
            row[col] = False
            continue
        if col in ("status", "state"):
            row[col] = "unknown"
            continue

    new_row = pd.DataFrame([row], columns=df.columns)
    for k, dtype in df.dtypes.items():
        try:
            new_row[k] = new_row[k].astype(dtype)
        except Exception:
            pass

    return pd.concat([df, new_row], ignore_index=True)


if __name__ == "__main__":
    main()