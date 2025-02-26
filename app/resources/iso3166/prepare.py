from pathlib import Path

import pandas as pd

# The file UNSD.csv can be obtained from https://unstats.un.org/unsd/methodology/m49/overview
# It contains the M49 country codes used by the UN for statistical purposes. The file
# contains the ISO 3166 alpha2/alpha3 codes as well.
fp = Path(__file__).with_name("UNSD.csv")
df = pd.read_csv(fp, sep=";")

dfx = df.rename(columns={"ISO-alpha3 Code": "alpha3", "Country or Area": "name"})
fpout = Path(__file__).with_name("iso-3166-1-alpha3.json")
dfx[["alpha3", "name"]].to_json(fpout, orient="records")
