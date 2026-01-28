import json
import pandas as pd
import random
from pathlib import Path
from typing import Union
import math

def main():
    df = make_df_from_schema("labels.json")
    for i in range(3):
        ChargeTime = random.randint(30,60)
        ChargeCnt = random.randint(1,4)
        df = make_df_1record(df,ChargeTime=ChargeTime,ChargeCnt=ChargeCnt,ACDCFLG=random.choice([0,1]))
        df = make_df_record_CAN(df,ChargeTime,ChargeCnt)
    
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
def make_df_1record(df: pd.DataFrame,ChargeTime: int,ChargeCnt: int,ACDCFLG: int) -> pd.DataFrame:
    if df is None:
        return df
    
    # 今日の日付文字列を取得
    today_str = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    row = {}
    for col in df.columns:
        
        # 車両番号
        if col in ("VehicleNo"):
            row[col] = random.randint(1, 1)
            #row[col] = 1
            continue
        
        # 日付
        if col in ("Date"):
            row[col] = today_str
            continue
        
        # EVSEのMACアドレス
        if col in ("EVSE_MACADDRESS_1", "EVSE_MACADDRESS_2", "EVSE_MACADDRESS_3", "EVSE_MACADDRESS_4"):
            # ランダムなMACアドレスを生成してStringDtypeで格納
            for i in range(ChargeCnt):
                if col == f"EVSE_MACADDRESS_{i+1}":
                    mac = ":".join(f"{random.randint(0,255):02X}" for _ in range(6))
                    i = pd.Series(mac, dtype="string").iat[0]
                    row[col] = i
                    break
            continue
        
        # 総充電コネクタ接続検知回数
        if col in ("AllConnectionDetection_1", "AllConnectionDetection_2", "AllConnectionDetection_3", "AllConnectionDetection_4"):
            vehicle_no = row.get("VehicleNo")
            if col == "AllConnectionDetection_1":
                prev = 0
                if vehicle_no is not None and not df.empty and "VehicleNo" in df.columns and "AllConnectionDetection_1" in df.columns:
                    grp = df.loc[df["VehicleNo"] == vehicle_no, "AllConnectionDetection_1"]
                    if not grp.empty:
                        nums = pd.to_numeric(grp, errors="coerce")
                        if nums.notna().any():
                            prev = int(nums.max())
                # ChargeCnt に応じて AllConnectionDetection_1..4 を設定
                vals = [0, 0, 0, 0]  # index 0 -> _1, 1 -> _2, 2 -> _3, 3 -> _4
                if ChargeCnt == 4:
                    vals = [prev + 4, prev + 3, prev + 2, prev + 1]
                elif ChargeCnt == 3:
                    vals = [prev + 3, prev + 2, prev + 1, 0]
                elif ChargeCnt == 2:
                    vals = [prev + 2, prev + 1, 0, 0]
                elif ChargeCnt == 1:
                    vals = [prev + 1, 0, 0, 0]

                for idx, v in enumerate(vals, start=1):
                    colname = f"AllConnectionDetection_{idx}"
                    if colname in df.columns:
                        row[colname] = v
                continue
            
#            for i in range(ChargeCnt):
                if col == f"AllConnectionDetection_{i+1}":
                    vehicle_no = row.get("VehicleNo")
                    prev = 0
                    if vehicle_no is not None and not df.empty and "VehicleNo" in df.columns and col in df.columns:
                        grp = df[df["VehicleNo"] == vehicle_no][col]
                        if not grp.empty:
                            nums = pd.to_numeric(grp, errors="coerce")
                            if nums.notna().any():
                                prev = int(nums.max())
                    row[col] = prev + 1
                    continue
#            continue

        # インレット端子温度
        if col in ("Inlet_Terminal_Temp_C1_001", "Inlet_Terminal_Temp_C1_002", "Inlet_Terminal_Temp_C1_003", "Inlet_Terminal_Temp_C1_004","Inlet_Terminal_Temp_C1_005","Inlet_Terminal_Temp_C1_006","Inlet_Terminal_Temp_C1_007","Inlet_Terminal_Temp_C1_008", "Inlet_Terminal_Temp_C1_009", "Inlet_Terminal_Temp_C1_010"):
            # 一度だけ生成して 001～010 に割り当てる
            if not row.get("_inlet_generated"):
                # プロット数 = ChargeTime * 60 / 10
                plots = max(0, int(ChargeTime * 60 / 10))

                # 正規分布の中心はインデックス 6 (Inlet_Terminal_Temp_C1_006)
                mean_idx = 6.0
                sd = 1.5  # 標準偏差（必要なら調整）

                # 1..10 の位置に対する重みを計算して正規分布に従う確率に正規化
                positions = list(range(1, 11))
                weights = [math.exp(-0.5 * ((p - mean_idx) / sd) ** 2) for p in positions]
                total = sum(weights)
                probs = [w / total for w in weights] if total > 0 else [1.0 / 10] * 10

                # plots 回選んで各位置の出現回数をカウント（Multinomial の代替）
                picks = random.choices(positions, weights=probs, k=plots)
                counts = {p: 0 for p in positions}
                for p in picks:
                    counts[p] += 1

                # 各 Inlet_Terminal_Temp_C1_001..010 に対応する値を代入
                for i in positions:
                    colname = f"Inlet_Terminal_Temp_C1_{i:03d}" #このへんをChargeCntに対応すると、C2,C3,C4にも対応できる
                    if colname in df.columns:
                        row[colname] = counts[i]

                # フラグを立てて二重生成を防止（DataFrame には含められないキー）
                row["_inlet_generated"] = True

            # 以降ループで他の Inlet 列が来ても既に設定済みなのでスキップ
            if col in ("Inlet_Terminal_Temp_C1_001", "Inlet_Terminal_Temp_C1_002", "Inlet_Terminal_Temp_C1_003", "Inlet_Terminal_Temp_C1_004","Inlet_Terminal_Temp_C1_005","Inlet_Terminal_Temp_C1_006","Inlet_Terminal_Temp_C1_007","Inlet_Terminal_Temp_C1_008", "Inlet_Terminal_Temp_C1_009", "Inlet_Terminal_Temp_C1_010"):
                continue
        
        # CPLT Duty
        if col in ("CPLT_DUTY_C1_001", "CPLT_DUTY_C1_002", "CPLT_DUTY_C1_003", "CPLT_DUTY_C1_004","CPLT_DUTY_C1_005","CPLT_DUTY_C1_006","CPLT_DUTY_C1_007","CPLT_DUTY_C1_008", "CPLT_DUTY_C1_009", "CPLT_DUTY_C1_010","CPLT_DUTY_C1_011","CPLT_DUTY_C1_012","CPLT_DUTY_C1_013","CPLT_DUTY_C1_014","CPLT_DUTY_C1_015"):
            # 一度だけ生成して 001～010 に割り当てる
            if not row.get("_cplt_generated"):
                # プロット数 = ChargeTime * 60 / 10
                plots = max(0, int(ChargeTime * 60 / 10))

                # 一様分布で各位置に均等に分布させる
                positions = list(range(1, 11))
                counts = {p: 0 for p in positions}

                picks = random.choices(positions, k=plots)
                for p in picks:
                    counts[p] += 1

                # 各 CPLT_DUTY_C1_001..010 に対応する値を代入
                for i in positions:
                    colname = f"CPLT_DUTY_C1_{i:03d}"
                    if colname in df.columns:
                        row[colname] = counts[i]

                # フラグを立てて二重生成を防止（DataFrame には含められないキー）
                row["_cplt_generated"] = True

            # 以降ループで他の CPLT 列が来ても既に設定済みなのでスキップ
            if col in ("CPLT_DUTY_C1_001", "CPLT_DUTY_C1_002", "CPLT_DUTY_C1_003", "CPLT_DUTY_C1_004","CPLT_DUTY_C1_005","CPLT_DUTY_C1_006","CPLT_DUTY_C1_007","CPLT_DUTY_C1_008", "CPLT_DUTY_C1_009", "CPLT_DUTY_C1_010","CPLT_DUTY_C1_011","CPLT_DUTY_C1_012","CPLT_DUTY_C1_013","CPLT_DUTY_C1_014","CPLT_DUTY_C1_015"):
                continue
        
        # PISW 電圧
        if col in ("PISW_Voltage_C1_001", "PISW_Voltage_C1_002", "PISW_Voltage_C1_003", "PISW_Voltage_C1_004","PISW_Voltage_C1_005"):
            # 一度だけ生成して PISW_Voltage_C1_001..005 に割り振る
            if not row.get("_pisw_generated"):
                # プロット数 = ChargeTime * 60 / 10
                plots = max(0, int(ChargeTime * 60 / 10))

                positions = list(range(1, 6))
                counts = {pos: 0 for pos in positions}

                if plots > 0:
                    picks = random.choices(positions, k=plots)
                    for p in picks:
                        counts[p] += 1

                # PISW_Voltage_C1_001..005 にのみ割り当て
                for pos in positions:
                    colname = f"PISW_Voltage_C1_{pos:03d}"
                    if colname in df.columns:
                        row[colname] = counts[pos]

                row["_pisw_generated"] = True
            continue
        
        # 充電最大電力
        if col in ("CHARGER_MAX_POWER_C1", "CHARGER_MAX_POWER_C2", "CHARGER_MAX_POWER_C3", "CHARGER_MAX_POWER_C4"):
            # 例えば 50kW 固定など、適宜調整可能
            for i in range(ChargeCnt):
                if col == f"CHARGER_MAX_POWER_C{i+1}":
                    row[col] = random.randint(50, 150)
                    break
            continue
        
        # 充電器入力電圧[V]
        if col in ("CHARGER_INPUT_VOLTAGE_C1_001", "CHARGER_INPUT_VOLTAGE_C1_002", "CHARGER_INPUT_VOLTAGE_C1_003", "CHARGER_INPUT_VOLTAGE_C1_004","CHARGER_INPUT_VOLTAGE_C1_005","CHARGER_INPUT_VOLTAGE_C1_006","CHARGER_INPUT_VOLTAGE_C1_007","CHARGER_INPUT_VOLTAGE_C1_008", "CHARGER_INPUT_VOLTAGE_C1_009"):
            # 一度だけ生成して 001～009 に割り当てる
            if not row.get("_charger_voltage_generated"):
                # プロット数 = ChargeTime * 60 / 10
                plots = max(0, int(ChargeTime * 60 / 10))

                positions = list(range(1, 10))
                counts = {p: 0 for p in positions}

                picks = random.choices(positions, k=plots)
                for p in picks:
                    counts[p] += 1

                # 各 CHARGER_INPUT_VOLTAGE_C1_001..009 に対応する値を代入
                for i in positions:
                    colname = f"CHARGER_INPUT_VOLTAGE_C1_{i:03d}"
                    if colname in df.columns:
                        row[colname] = counts[i]

                # フラグを立てて二重生成を防止（DataFrame には含められないキー）
                row["_charger_voltage_generated"] = True
            # 以降ループで他の CHARGER_INPUT_VOLTAGE 列が来ても既に設定済みなのでスキップ
            if col in ("CHARGER_INPUT_VOLTAGE_C1_001", "CHARGER_INPUT_VOLTAGE_C1_002", "CHARGER_INPUT_VOLTAGE_C1_003", "CHARGER_INPUT_VOLTAGE_C1_004","CHARGER_INPUT_VOLTAGE_C1_005","CHARGER_INPUT_VOLTAGE_C1_006","CHARGER_INPUT_VOLTAGE_C1_007","CHARGER_INPUT_VOLTAGE_C1_008", "CHARGER_INPUT_VOLTAGE_C1_009"):
                continue

        # 充電器出力電圧[V]
        if col in ("CHARGER_OUTPUT_VOLTAGE_C1_001", "CHARGER_OUTPUT_VOLTAGE_C1_002", "CHARGER_OUTPUT_VOLTAGE_C1_003", "CHARGER_OUTPUT_VOLTAGE_C1_004","CHARGER_OUTPUT_VOLTAGE_C1_005","CHARGER_OUTPUT_VOLTAGE_C1_006","CHARGER_OUTPUT_VOLTAGE_C1_007","CHARGER_OUTPUT_VOLTAGE_C1_008", "CHARGER_OUTPUT_VOLTAGE_C1_009"):
            # 一度だけ生成して 001～009 に割り当てる
            if not row.get("_charger_output_voltage_generated"):
                # プロット数 = ChargeTime * 60 / 10
                plots = max(0, int(ChargeTime * 60 / 10))

                positions = list(range(1, 10))
                counts = {p: 0 for p in positions}

                picks = random.choices(positions, k=plots)
                for p in picks:
                    counts[p] += 1

                # 各 CHARGER_OUTPUT_VOLTAGE_C1_001..009 に対応する値を代入
                for i in positions:
                    colname = f"CHARGER_OUTPUT_VOLTAGE_C1_{i:03d}"
                    if colname in df.columns:
                        row[colname] = counts[i]

                # フラグを立てて二重生成を防止（DataFrame には含められないキー）
                row["_charger_output_voltage_generated"] = True
            # 以降ループで他の CHARGER_OUTPUT_VOLTAGE 列が来ても既に設定済みなのでスキップ
            if col in ("CHARGER_OUTPUT_VOLTAGE_C1_001", "CHARGER_OUTPUT_VOLTAGE_C1_002", "CHARGER_OUTPUT_VOLTAGE_C1_003", "CHARGER_OUTPUT_VOLTAGE_C1_004","CHARGER_OUTPUT_VOLTAGE_C1_005","CHARGER_OUTPUT_VOLTAGE_C1_006","CHARGER_OUTPUT_VOLTAGE_C1_007","CHARGER_OUTPUT_VOLTAGE_C1_008", "CHARGER_OUTPUT_VOLTAGE_C1_009"):
                continue
            
        # 充電器出力[kw]
        if col in ("CHARGER_OUTPUT_POWER_C1_001", "CHARGER_OUTPUT_POWER_C1_002", "CHARGER_OUTPUT_POWER_C1_003", "CHARGER_OUTPUT_POWER_C1_004","CHARGER_OUTPUT_POWER_C1_005","CHARGER_OUTPUT_POWER_C1_006","CHARGER_OUTPUT_POWER_C1_007","CHARGER_OUTPUT_POWER_C1_008", "CHARGER_OUTPUT_POWER_C1_009"):
            # 一度だけ生成して 001～009 に割り当てる
            if not row.get("_charger_output_power_generated"):
                # プロット数 = ChargeTime * 60 / 10
                plots = max(0, int(ChargeTime * 60 / 10))

                positions = list(range(1, 10))
                counts = {p: 0 for p in positions}

                picks = random.choices(positions, k=plots)
                for p in picks:
                    counts[p] += 1

                # 各 CHARGER_OUTPUT_POWER_C1_001..009 に対応する値を代入
                for i in positions:
                    colname = f"CHARGER_OUTPUT_POWER_C1_{i:03d}"
                    if colname in df.columns:
                        row[colname] = counts[i]

                # フラグを立てて二重生成を防止（DataFrame には含められないキー）
                row["_charger_output_power_generated"] = True
            # 以降ループで他の CHARGER_OUTPUT_POWER 列が来ても既に設定済みなのでスキップ
            if col in ("CHARGER_OUTPUT_POWER_C1_001", "CHARGER_OUTPUT_POWER_C1_002", "CHARGER_OUTPUT_POWER_C1_003", "CHARGER_OUTPUT_POWER_C1_004","CHARGER_OUTPUT_POWER_C1_005","CHARGER_OUTPUT_POWER_C1_006","CHARGER_OUTPUT_POWER_C1_007","CHARGER_OUTPUT_POWER_C1_008", "CHARGER_OUTPUT_POWER_C1_009"):
                continue
            
        # 充電中電流（時系列）
        if col == ("IN_CHARGE_CURRENT"):
            row[col] = 65535
            continue

        # 充電中Win（時系列）
        if col == ("IN_CHARGE_WIN"):
            row[col] = 65535
            continue

        # 充電中SOC（時系列）
        if col == ("IN_CHARGE_SOC"):
            row[col] = 65535
            continue

        # DCリレー温度[℃]
        if col in ("DC_RELAY_TEMP_C1_001", "DC_RELAY_TEMP_C1_002", "DC_RELAY_TEMP_C1_003", "DC_RELAY_TEMP_C1_004","DC_RELAY_TEMP_C1_005","DC_RELAY_TEMP_C1_006","DC_RELAY_TEMP_C1_007","DC_RELAY_TEMP_C1_008"):
            # 一度だけ生成して 001～010 に割り当てる
            if not row.get("_dc_relay_generated"):
                # プロット数 = ChargeTime * 60 / 10
                plots = max(0, int(ChargeTime * 60 / 10))

                positions = list(range(1, 11))
                counts = {p: 0 for p in positions}

                picks = random.choices(positions, k=plots)
                for p in picks:
                    counts[p] += 1

                # 各 DC_RELAY_TEMP_C1_001..010 に対応する値を代入
                for i in positions:
                    colname = f"DC_RELAY_TEMP_C1_{i:03d}"
                    if colname in df.columns:
                        row[colname] = counts[i]

                # フラグを立てて二重生成を防止（DataFrame には含められないキー）
                row["_dc_relay_generated"] = True

            # 以降ループで他の DC_RELAY 列が来ても既に設定済みなのでスキップ
            if col in ("DC_RELAY_TEMP_C1_001", "DC_RELAY_TEMP_C1_002", "DC_RELAY_TEMP_C1_003", "DC_RELAY_TEMP_C1_004","DC_RELAY_TEMP_C1_005","DC_RELAY_TEMP_C1_006","DC_RELAY_TEMP_C1_007","DC_RELAY_TEMP_C1_008"):
                continue
            
        # ACリレー温度[℃]
        if col in ("AC_RELAY_TEMP_C1_001", "AC_RELAY_TEMP_C1_002", "AC_RELAY_TEMP_C1_003", "AC_RELAY_TEMP_C1_004","AC_RELAY_TEMP_C1_005","AC_RELAY_TEMP_C1_006","AC_RELAY_TEMP_C1_007","AC_RELAY_TEMP_C1_008"):
            # 一度だけ生成して 001～010 に割り当てる
            if not row.get("_ac_relay_generated"):
                # プロット数 = ChargeTime * 60 / 10
                plots = max(0, int(ChargeTime * 60 / 10))

                positions = list(range(1, 11))
                counts = {p: 0 for p in positions}

                picks = random.choices(positions, k=plots)
                for p in picks:
                    counts[p] += 1

                # 各 AC_RELAY_TEMP_C1_001..010 に対応する値を代入
                for i in positions:
                    colname = f"AC_RELAY_TEMP_C1_{i:03d}"
                    if colname in df.columns:
                        row[colname] = counts[i]

                # フラグを立てて二重生成を防止（DataFrame には含められないキー）
                row["_ac_relay_generated"] = True

            # 以降ループで他の AC_RELAY 列が来ても既に設定済みなのでスキップ
            if col in ("AC_RELAY_TEMP_C1_001", "AC_RELAY_TEMP_C1_002", "AC_RELAY_TEMP_C1_003", "AC_RELAY_TEMP_C1_004","AC_RELAY_TEMP_C1_005","AC_RELAY_TEMP_C1_006","AC_RELAY_TEMP_C1_007","AC_RELAY_TEMP_C1_008"):
                continue

        # 充電中セル最大温度（時系列）
        if col in ("IN_CHARGE_CELL_MAX_TEMP"):
            row[col] = 65535
            continue

        # 充電中セル最小温度（時系列）
        if col in ("IN_CHARGE_CELL_MIN_TEMP"):
            row[col] = 65535
            continue

        # 総AC充電電力量
        if col in ("AC_CHARGE_POWER_AMOUNT"):
            row[col] = 0
            continue

        # 総DC充電電力量
        if col in ("DC_CHARGE_POWER_AMOUNT"):
            row[col] = 0
            continue
        
        # 総充電時間[min]
        if col in ("CHARGE_TIME_AMOUNT"):
            row[col] = 0
            continue
        
        # DC充電回数
        if col in ("DC_CHARGE_COUNTS"):
            row[col] = 0
            continue
        
        # AC充電回数
        if col in ("AC_CHARGE_COUNTS"):
            row[col] = 0
            continue
        
        # 充電停止要因
        if col in ("CHARGE_STOP_COUNT_001", "CHARGE_STOP_COUNT_002", "CHARGE_STOP_COUNT_003", "CHARGE_STOP_COUNT_004"):
            row[col] = 0
            continue
        
        # EVSE_MAlfuction
        if col in ("EVSE_MAlfuction_C1", "EVSE_MAlfuction_C2", "EVSE_MAlfuction_C3", "EVSE_MAlfuction_C4"):
            row[col] = 0
            continue
        
        # EVSE_Shutdown
        if col in ("EVSE_Shutdown_C1", "EVSE_Shutdown_C2", "EVSE_Shutdown_C3", "EVSE_Shutdown_C4"):
            row[col] = 0
            continue
        
        # EVSE_UtilityInterruptEvent
        if col in ("EVSE_UtilityInterruptEvent_C1", "EVSE_UtilityInterruptEvent_C2", "EVSE_UtilityInterruptEvent_C3", "EVSE_UtilityInterruptEvent_C4"):
            row[col] = 0
            continue
        
        #　ERROR系は一旦後回し。
        
        #ACDC充電成功失敗回数
        if col in ("AC_CHARGE_SUCESSED_COUNT","AC_CHARGE_FAILED_COUNT","DC_CHARGE_SUCESSED_COUNT","DC_CHARGE_FAILED_COUNT"):
            if col == "AC_CHARGE_SUCESSED_COUNT":
                if ACDCFLG == 0:
                    prev = 0
                    if not df.empty and col in df.columns:
                        nums = pd.to_numeric(df[col], errors="coerce")
                        if nums.notna().any():
                            prev = int(nums.max())
                    row[col] = prev + 1
                else:
                    row[col] = 0
                continue

            if col == "AC_CHARGE_FAILED_COUNT":
                row[col] = 0
                continue

            if col == "DC_CHARGE_SUCESSED_COUNT":
                if ACDCFLG != 0:
                    prev = 0
                    if not df.empty and col in df.columns:
                        nums = pd.to_numeric(df[col], errors="coerce")
                        if nums.notna().any():
                            prev = int(nums.max())
                    row[col] = prev + 1
                else:
                    row[col] = 0
                continue

            if col == "DC_CHARGE_FAILED_COUNT":
                row[col] = 0
                continue
            continue
    
        # 充電モードフラグ
        if col in ("CHARGE_MODE_NORMAL_FLAG_C1","CHARGE_MODE_TIMER_FLAG_C1"):
            # 両フラグを同時に決定して矛盾を防ぐ
            timer_flag = 0
            if ACDCFLG == 0:
                # 50% の確率でタイマーフラグを立てる
                timer_flag = int(random.random() < 0.5)
            else:
                # ACDCFLG が 1 のときはタイマーフラグは 0
                timer_flag = 0

            # タイマーフラグが 1 のときはノーマルフラグを 0、それ以外は 1
            normal_flag = 0 if timer_flag == 1 else 1

            if "CHARGE_MODE_TIMER_FLAG_C1" in df.columns:
                row["CHARGE_MODE_TIMER_FLAG_C1"] = timer_flag
            if "CHARGE_MODE_NORMAL_FLAG_C1" in df.columns:
                row["CHARGE_MODE_NORMAL_FLAG_C1"] = normal_flag
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


def make_df_record_CAN(df: pd.DataFrame, ChargeTime: int, ChargeCnt: int) -> pd.DataFrame:
    if df is None:
        return df

    # SOC と完全一致する列を検出（大文字小文字は区別）
    soc_cols = []
    for col in df.columns:
        if col == "SOC":
            soc_cols.append(col)
    if not soc_cols:
        return df

    # レコード数: ChargeTime　1分ごとに1レコード
    n_records = max(1, int(ChargeTime * 1))

    # 初期SOC: 80..100
    init_soc = random.randint(80, 100)

    # 減少量のレンジを ChargeTime に応じて線形補間（30 -> 5..15, 60 -> 15..30）
    t = (ChargeTime - 30) / 30.0
    t = max(0.0, min(1.0, t))
    drop_min = 5 + t * 10   # 5 .. 15
    drop_max = 15 + t * 15  # 15 .. 30
    drop_min_i = max(0, int(math.floor(drop_min)))
    drop_max_i = max(drop_min_i, int(math.ceil(drop_max)))
    total_drop = random.randint(drop_min_i, drop_max_i)

    # 最終値は 0 未満にならないようにする
    final_soc = max(0, init_soc - total_drop)

    # 端から端まで減少する系列を作成（単調減少、整数、0..100 にクランプ）
    vals = []
    if n_records == 1:
        vals = [init_soc]
    else:
        for i in range(n_records):
            frac = i / (n_records - 1)
            v = init_soc - total_drop * frac
            vi = int(round(v))
            vi = max(0, min(100, vi))
            vals.append(vi)

    # DataFrame 用の行を作成（SOC 列に値を入れ、他列は欠損値）
    rows = []
    for v in vals:
        row = {c: None for c in df.columns}
        for sc in soc_cols:
            row[sc] = v
        rows.append(row)

    new_df = pd.DataFrame(rows, columns=df.columns)

    # 既存の dtypes に合わせて可能ならキャスト
    for k, dtype in df.dtypes.items():
        try:
            new_df[k] = new_df[k].astype(dtype)
        except Exception:
            pass

    return pd.concat([df, new_df], ignore_index=True)

if __name__ == "__main__":
    main()