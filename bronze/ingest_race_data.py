import json
import os
from pathlib import Path
import polars as pl

BASE_DIR = Path("sources/tracinginsights/2026")

def ingest_all_telemetry():
    os.makedirs("bronze/telemetry", exist_ok=True)

    for gp_dir in BASE_DIR.iterdir():
        if not gp_dir.is_dir() or gp_dir.name.startswith('.'):
            continue
            
        print(f"\n🏁 Grand Prix: {gp_dir.name}")
        for session_dir in gp_dir.iterdir():
            if not session_dir.is_dir():
                continue
                
            print(f"   Session: {session_dir.name}")
            session_laps = []
            for driver_dir in session_dir.iterdir():
                if not driver_dir.is_dir() or len(driver_dir.name) != 3:
                    continue

                driver_code = driver_dir.name

                # Collect all laps for this driver
                for tel_file in driver_dir.glob("*_tel.json"):
                    # Extract lap number from "7_tel.json" -> 7
                    try:
                        lap_num = int(tel_file.name.split("_")[0])
                    except ValueError:
                        lap_num = None

                    with open(tel_file, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    tel_dict = data.get("tel", {})
                    # Only keep time, x, and y
                    if "time" in tel_dict and "x" in tel_dict and "y" in tel_dict:
                        lap_df = pl.DataFrame({
                            "time": pl.Series(tel_dict["time"], dtype=pl.Float64),
                            "x": pl.Series(tel_dict["x"], dtype=pl.Float64),
                            "y": pl.Series(tel_dict["y"], dtype=pl.Float64),
                        }).with_columns(
                            pl.lit(driver_code).alias("driver"),
                            pl.lit(lap_num).alias("lap")
                        )
                        session_laps.append(lap_df)

            # If the driver had laps, concat and write to Parquet
            if session_laps:
                df = pl.concat(session_laps).with_columns(
                    pl.lit(gp_dir.name).alias("grand_prix"),
                    pl.lit(session_dir.name).alias("session"),
                )

                file_name = f"{gp_dir.name}_{session_dir.name}.parquet"
                out_path = Path("bronze/telemetry") / file_name
                
                df.write_parquet(out_path)
                print(f"      Saved ({df.height} rows, {len(session_laps)} laps) -> {file_name}")


    

if __name__ == "__main__":
    ingest_all_telemetry()
