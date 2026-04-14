import pandas as pd
from pathlib import Path
import re


def join_dpe_and_conso(dpe_file, conso_file, score_threshold=0.6):
    try:
        dpe = pd.read_csv(dpe_file)
        enedis = pd.read_csv(conso_file)
    except Exception as e:
        print(f"Error reading files: {e}")
        return None

    dpe = dpe[dpe["score_ban"] > score_threshold]
    enedis = enedis[enedis["ban_score"] > score_threshold]

    if len(dpe) == 0 or len(enedis) == 0:
        return None

    # Join on BAN ID
    df_join = enedis.merge(
        dpe,
        left_on="ban_id",
        right_on="identifiant_ban",
        how="left",
        suffixes=("_enedis", "_dpe"),
    )

    # Keep only rows with DPE etiquette
    df_join = df_join[df_join["etiquette_dpe"].notnull()]

    return df_join


def main():
    data_path = Path(".data")

    # Find all DPE files (dpe_*.csv)
    dpe_files = sorted(data_path.glob("dpe_*.csv"))
    print(f"Found {len(dpe_files)} DPE files")

    if not dpe_files:
        print("No DPE files found in .data/")
        return

    all_results = []

    for dpe_file in dpe_files:
        # Extract department code from filename (e.g., dpe_75.csv -> 75)
        match = re.search(r"dpe_(\d+)", dpe_file.name)
        if not match:
            print(f"Skipping {dpe_file.name} - could not extract department code")
            continue

        dept_code = match.group(1)
        conso_file = data_path / f"conso_{dept_code}_with_ban.csv"

        if not conso_file.exists():
            print(f"Skipping department {dept_code} - {conso_file.name} not found")
            continue

        print(f"\nProcessing department {dept_code}...")

        df_joined = join_dpe_and_conso(dpe_file, conso_file)

        if df_joined is not None and len(df_joined) > 0:
            print(f"   {len(df_joined)} matched records")
            all_results.append(df_joined)
        else:
            print(f"   No matching records")

    if not all_results:
        print("\nNo results to concatenate")
        return

    # Concatenate all results
    df_final = pd.concat(all_results, ignore_index=True)

    # Save to final.csv
    output_file = data_path / "final.csv"
    df_final.to_csv(output_file, index=False)

    print(f"\n{'='*50}")
    print(f"Output saved to {output_file}")
    print(f"Total rows: {len(df_final)}")
    print(f"Total columns: {len(df_final.columns)}")


if __name__ == "__main__":
    main()
