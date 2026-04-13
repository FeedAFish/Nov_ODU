import requests
import pandas as pd
from typing import List, Union
from io import StringIO
import time


COLUMNS = [
    "etiquette_dpe",
    "etiquette_ges",
    "type_batiment",
    "annee_construction",
    "periode_construction",
    "type_installation_chauffage",
    "type_installation_ecs",
    "nombre_appartement",
    "nombre_niveau_immeuble",
    "typologie_logement",
    "appartement_non_visite",
    "surface_habitable_immeuble",
    "surface_habitable_logement",
    "classe_inertie_batiment",
    "adresse_ban",
    "identifiant_ban",
    "score_ban",
    "indicateur_confort_ete",
    "protection_solaire_exterieure",
    "logement_traversant",
    "presence_brasseur_air",
    "inertie_lourde",
    "isolation_toiture",
    "numero_dpe",
    "hauteur_sous_plafond",
    "nombre_niveau_logement",
    "numero_etage_appartement",
    "position_logement_dans_immeuble",
    "deperditions_enveloppe",
    "deperditions_ponts_thermiques",
    "deperditions_murs",
    "deperditions_planchers_hauts",
    "deperditions_planchers_bas",
    "deperditions_portes",
    "deperditions_baies_vitrees",
    "deperditions_renouvellement_air",
    "qualite_isolation_enveloppe",
    "qualite_isolation_murs",
    "qualite_isolation_plancher_haut_comble_amenage",
    "qualite_isolation_plancher_haut_comble_perdu",
    "qualite_isolation_plancher_haut_toit_terrasse",
    "qualite_isolation_plancher_bas",
    "qualite_isolation_menuiseries",
    "ubat_w_par_m2_k",
    "besoin_chauffage",
    "besoin_ecs",
    "besoin_refroidissement",
    "apport_interne_saison_chauffe",
    "apport_interne_saison_froide",
    "apport_solaire_saison_chauffe",
    "apport_solaire_saison_froide",
    "type_energie_n1",
    "type_energie_n2",
    "type_energie_n3",
    "type_energie_principale_chauffage",
    "type_generateur_chauffage_principal",
    "type_energie_principale_ecs",
    "type_ventilation",
    "type_generateur_froid",
    "systeme_production_electricite_origine_renouvelable",
]


def download_dpe_data(
    dept_codes: Union[str, List[str]],
    delay_between_requests: float = 0.1,
) -> pd.DataFrame:
    dept_codes = [dept_codes] if isinstance(dept_codes, str) else dept_codes
    select_cols = "%2C".join(COLUMNS)

    all_dfs = []

    for dept in dept_codes:
        print(f"Fetching dept={dept}...")

        url = f"https://data.ademe.fr/data-fair/api/v1/datasets/dpe03existant/lines?type_batiment_in=immeuble%2Cmaison&size=10000&code_departement_ban_eq={dept}&format=csv&select={select_cols}&sort=numero_dpe"
        try:
            while url:
                response = requests.get(url, timeout=30)
                response.raise_for_status()

                df = pd.read_csv(StringIO(response.text))
                print(f"Downloaded {len(df)} records...")
                all_dfs.append(df)

                link_header = response.headers.get("Link", "")
                url = None

                if "rel=next" in link_header:
                    url = link_header.split(";")[0][1:-1]

                if url:
                    time.sleep(delay_between_requests)

            total = sum(len(df) for df in all_dfs)
            print(f"({total} records)")

        except Exception as e:
            print(f"Error: {e}")
            continue

        time.sleep(delay_between_requests)

    if not all_dfs:
        return pd.DataFrame()

    return pd.concat(all_dfs, ignore_index=True)


def download_dpe_csv(dept_codes: Union[str, List[str]]) -> List[str]:
    dept_list = [dept_codes] if isinstance(dept_codes, str) else dept_codes
    saved_files = []

    for dept in dept_list:
        df = download_dpe_data(dept)

        if len(df) > 0:
            output_file = f".data_new/dpe_{dept}.csv"
            df.to_csv(output_file, index=False)
            saved_files.append(output_file)
            print(f"Saved: {output_file}")
        else:
            print(f"Skipped dept {dept}")

    print(f"{len(saved_files)}/{len(dept_list)} files saved")
    return saved_files


if __name__ == "__main__":
    files = download_dpe_csv(dept_codes=["80"])
