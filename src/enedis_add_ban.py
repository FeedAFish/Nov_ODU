import requests
import time
import pandas as pd
from pathlib import Path
import json


cache_file = ".data/.ban_cache.json"


def load_cache():
    if Path(cache_file).exists():
        with open(cache_file, "r") as f:
            return json.load(f)
    return {}


def save_cache(cache):
    with open(cache_file, "w") as f:
        json.dump(cache, f)


def verify_with_ban(address, cache):
    if address in cache:
        return tuple(cache[address])  # Convert list back to tuple

    url = f"https://api-adresse.data.gouv.fr/search/?q={address}&limit=1"
    try:
        response = requests.get(url, timeout=10).json()
        if response.get("features"):
            result = (
                response["features"][0]["properties"]["id"],
                response["features"][0]["properties"]["name"],
                response["features"][0]["properties"]["score"],
            )
        else:
            result = (None, None, None)
    except Exception as e:
        print(f"Error for {address}: {e}")
        result = (None, None, None)

    cache[address] = result
    time.sleep(0.05)
    return result


def process_enedis_with_ban(csv_path):
    cache = load_cache()
    df = pd.read_csv(csv_path)

    df.drop(
        columns=[
            "Code IRIS",
            "Nom IRIS",
            "Numéro de voie",
            "Indice de répétition",
            "Type de voie",
            "Libellé de voie",
            "Consommation annuelle moyenne de la commune (MWh)",
            "Code EPCI",
            "Tri des adresses",
        ],
        inplace=True,
    )

    df["adresse_full"] = (
        df["Adresse"] + " " + df["Code Commune"].astype(str) + " " + df["Nom Commune"]
    )

    if "ban_id" not in df.columns:
        df[["ban_id", "ban_add", "ban_score"]] = None

    missing_mask = df["ban_id"].isna() | df["ban_id"].isnull()
    missing_count = missing_mask.sum()

    if missing_count > 0:
        unique_addresses = df[missing_mask]["adresse_full"].unique()
        print(
            f"Processing {missing_count} rows ({len(unique_addresses)} unique addresses)..."
        )

        # Build mapping dict (faster than repeated df.loc calls)
        results_map = {}
        cached_count = 0

        for i, address in enumerate(unique_addresses):
            if address in cache:
                cached_count += 1
            ban_id, ban_add, ban_score = verify_with_ban(address, cache)
            results_map[address] = (ban_id, ban_add, ban_score)

            if (i + 1) % 100 == 0 or (i + 1) == len(unique_addresses):
                print(f"  [{i + 1}/{len(unique_addresses)}] (cached: {cached_count})")

        # Vectorized assignment using map
        df.loc[missing_mask, "ban_id"] = df.loc[missing_mask, "adresse_full"].map(
            lambda x: results_map[x][0]
        )
        df.loc[missing_mask, "ban_add"] = df.loc[missing_mask, "adresse_full"].map(
            lambda x: results_map[x][1]
        )
        df.loc[missing_mask, "ban_score"] = df.loc[missing_mask, "adresse_full"].map(
            lambda x: results_map[x][2]
        )

        save_cache(cache)
        print(
            f"{cached_count} from cache, {len(unique_addresses) - cached_count} new queries"
        )
    else:
        print("All rows already have BAN data.")

    return df


if __name__ == "__main__":
    data_dir = Path(".data")
    csv_files = sorted(data_dir.glob("conso_*.csv"))

    if not csv_files:
        print("No conso_*.csv files found in .data/")
    else:
        total_rows = 0
        for csv_file in csv_files:
            print(f"\n{'='*60}")
            print(f"Processing {csv_file.name}...")
            print("=" * 60)

            df = process_enedis_with_ban(str(csv_file))
            total_rows += len(df)

            output_file = str(csv_file).replace(".csv", "_with_ban.csv")
            df.to_csv(output_file, index=False)
            print(f"Saved: {output_file} ({len(df)} rows)")

        print(f"\n{'='*60}")
        print(f"Completed: {len(csv_files)} file(s), {total_rows} total rows")
        print("=" * 60)

        print(f"\n{'='*60}")
        print(f"Processed {len(csv_files)} file(s)")
        print("=" * 60)
