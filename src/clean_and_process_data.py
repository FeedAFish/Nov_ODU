import pandas as pd
from pathlib import Path


def get_dpe_etiquette(kwh_per_m2):
    if pd.isna(kwh_per_m2):
        return None
    if kwh_per_m2 < 50:
        return "A"
    elif kwh_per_m2 < 90:
        return "B"
    elif kwh_per_m2 < 150:
        return "C"
    elif kwh_per_m2 < 230:
        return "D"
    elif kwh_per_m2 < 330:
        return "E"
    elif kwh_per_m2 < 450:
        return "F"
    else:
        return "G"


def process_data(input_file, output_file):
    print(f"Loading data from {input_file}...")
    df = pd.read_csv(input_file)
    print(f"Initial shape: {df.shape}")
    print(f"Initial N/A values: {df.isnull().sum().sum()}")

    # 1. Process surface_habitable
    print("\nProcessing surface_habitable...")
    df["surface_habitable"] = df["surface_habitable_immeuble"].fillna(
        df["surface_habitable_logement"]
    )
    df.drop(
        columns=["surface_habitable_immeuble", "surface_habitable_logement"],
        inplace=True,
    )
    print("   Merged surface columns")

    # 2. Calculate value_etiquette
    print("\nCalculating value_etiquette...")
    df["value_etiquette"] = (
        df["consommation_annuelle_moyenne_par_site_de_ladresse_mwh"]
        * 1000
        / (df["surface_habitable"] / df["nombre_appartement"])
    )
    print("   Calculated energy consumption per m²")

    # 3. Apply DPE etiquette
    print("\nApplying DPE etiquette labels...")
    df["etiquette_calculee"] = df["value_etiquette"].apply(get_dpe_etiquette)
    print("    Generated etiquette A-G labels")

    # 4. Remove rows with surface_habitable null
    print("\nRemoving rows with surface_habitable = null...")
    rows_before = len(df)
    df = df[df["surface_habitable"].notnull()]
    rows_after = len(df)
    print(f"  Removed {rows_before - rows_after} rows")

    # 5. Remove specific columns
    print("\nRemoving unnecessary columns...")
    cols_to_remove = [
        "annee_construction",
        "nombre_niveau_logement",
        "numero_etage_appartement",
    ]
    existing_cols = [col for col in cols_to_remove if col in df.columns]
    if existing_cols:
        df.drop(columns=existing_cols, inplace=True)
        print(f"  Removed: {existing_cols}")

    # 6. Fill N/A values with custom strategy
    print("\nFilling N/A values...")

    # Custom fills for specific columns
    fill_values = {
        "nombre_appartement": 1,
        "nombre_niveau_immeuble": 1,
        "appartement_non_visite": 0,
        "protection_solaire_exterieure": 0,
        "logement_traversant": 0,
        "presence_brasseur_air": 0,
        "inertie_lourde": 0,
        "isolation_toiture": 0,
    }

    for col, value in fill_values.items():
        if col in df.columns and df[col].isnull().sum() > 0:
            df[col] = df[col].fillna(value)
            print(f"  Filled {col} with: {value}")

    # Fill remaining numeric columns with median
    numeric_cols = df.select_dtypes(include=["number"]).columns
    for col in numeric_cols:
        if df[col].isnull().sum() > 0:
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
            print(f"  Filled {col} with median: {median_val}")

    # Fill remaining text columns
    text_cols = df.select_dtypes(include=["object"]).columns
    for col in text_cols:
        if df[col].isnull().sum() > 0:
            fill_value = "G" if "etiquette" in col.lower() else "Unknown"
            df[col] = df[col].fillna(fill_value)
            print(f"  Filled {col} with: '{fill_value}'")

    print("\n" + "=" * 60)
    print(f"Final shape: {df.shape}")
    print(f"Remaining N/A values: {df.isnull().sum().sum()}")

    # 7. Save output
    print(f"\nSaving to {output_file}...")
    df.to_csv(output_file, index=False)
    print("Data processing complete!")

    return df


if __name__ == "__main__":
    # File paths
    input_file = ".data/final.csv"
    output_file = ".data/final_cleaned.csv"

    # Ensure path exists
    Path(input_file).parent.mkdir(parents=True, exist_ok=True)

    # Process data
    df = process_data(input_file, output_file)

    print(f"\nOutput saved to: {output_file}")
