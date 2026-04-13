import requests
import pandas as pd
from typing import List, Union
from io import StringIO
import time


def download_enedis_data(
    years: Union[int, List[int]],
    dept_codes: Union[str, List[str]],
    delay_between_requests: float = 0.1,
) -> pd.DataFrame:
    years = [years] if isinstance(years, int) else years
    dept_codes = [dept_codes] if isinstance(dept_codes, str) else dept_codes
    years_str = ",".join(str(y) for y in years)

    all_dfs = []

    for dept in dept_codes:
        print(f"Fetching dept={dept}...")

        url = f"https://opendata.enedis.fr/data-fair/api/v1/datasets/consommation-annuelle-residentielle-par-adresse/lines?code_departement_eq={dept}&annee_in={years_str}&format=csv&size=10000"

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


def download_enedis_csv(
    years: Union[int, List[int]],
    dept_codes: Union[str, List[str]],
) -> List[str]:
    dept_list = [dept_codes] if isinstance(dept_codes, str) else dept_codes
    saved_files = []

    for dept in dept_list:
        df = download_enedis_data(years, dept)

        if len(df) > 0:
            output_file = f".data_new/conso_{dept}.csv"
            df.to_csv(output_file, index=False)
            saved_files.append(output_file)
            print(f"Saved: {output_file}")
        else:
            print(f"Skipped dept {dept}")

    print(f"{len(saved_files)}/{len(dept_list)} files saved")
    return saved_files


if __name__ == "__main__":
    files = download_enedis_csv(
        years=[2021, 2022, 2023, 2024],
        dept_codes=["80"],
    )
