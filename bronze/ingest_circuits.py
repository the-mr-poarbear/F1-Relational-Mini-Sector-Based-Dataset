
import json
import os
from pathlib import Path
import polars as pl

BASE_DIR = Path("sources/f1_timer/circuit_shapes")

def ingest_all_circuits():
    os.makedirs("bronze/circuits", exist_ok=True)
    circuits_shapes = []
    mini_sectors_indexes = []
    for circuit in BASE_DIR.glob("*.json"):
        print(circuit.name)
        with open(circuit , 'r' , encoding='utf-8') as f:
            circuit_data = json.load(f)
            # print(circuit_data.keys())
            df_circuit_shape = pl.DataFrame({
                "x": pl.Series(circuit_data["x"], dtype=pl.Float64),
                "y": pl.Series(circuit_data["y"], dtype=pl.Float64),
            }).with_columns(
                pl.lit(circuit_data["circuitName"]).alias("circuit_name"),
                pl.lit(circuit_data["circuitKey"]).alias("circuit_key")
            )
            circuits_shapes.append(df_circuit_shape)

            mini_sector_indexes = circuit_data.get("miniSectorsIndexes")

            if mini_sector_indexes:
                df_mini_sectors_indexes = pl.DataFrame({
                    "mini_sector_index": pl.Series(
                        mini_sector_indexes,
                        dtype=pl.Int64
                    ),
                }).with_columns(
                    pl.lit(circuit_data["circuitName"]).alias("circuit_name"),
                    pl.lit(circuit_data["circuitKey"]).alias("circuit_key")
                )

                mini_sectors_indexes.append(df_mini_sectors_indexes)
    
    if circuits_shapes :
        df = pl.concat(circuits_shapes)

        file_name = f"circuits.parquet"
        out_path = Path("bronze/circuits") / file_name
        
        df.write_parquet(out_path)
        print(f"      Saved ({df.height} rows, {len(circuits_shapes)} circuits) -> {file_name}")
    
    if mini_sectors_indexes :
        df = pl.concat(mini_sectors_indexes)

        file_name = f"mini_sectors_indexes.parquet"
        out_path = Path("bronze/circuits") / file_name
        
        df.write_parquet(out_path)
        print(f"      Saved ({df.height} rows, {len(circuits_shapes)} circuits) -> {file_name}")

    

if __name__ == "__main__":
    ingest_all_circuits()
