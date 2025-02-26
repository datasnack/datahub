from pathlib import Path

import pandas as pd

# The file iso-639-3.tab can be obtained from https://iso639-3.sil.org/code_tables/download_tables
fp = Path(__file__).with_name("iso-639-3.tab")
df = pd.read_csv(fp, sep="\t")

# for brevity / most common uses of the list, we only select languages that were also
# available in ISO639-1
dfx = df[df["Part1"].notna()]

fpout = Path(__file__).with_name("iso-639-3.json")
dfx[["Id", "Ref_Name"]].to_json(fpout, orient="records")
