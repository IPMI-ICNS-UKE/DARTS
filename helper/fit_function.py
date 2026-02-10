import numpy as np
from scipy.optimize import curve_fit
import pandas as pd

# Datei laden (Pfad anpassen)
df = pd.read_excel("/Users/felixwissel/Documents/UKE/Kopie von human NK cell local Ca2+ calibration.xlsx")
df_clean = df[["ratio", "Ca2+ NM"]].dropna()

ratio = df_clean["ratio"].values
ca = df_clean["Ca2+ NM"].values
ca = ca + 25.47868517 # Ca Werte hochschieben, um bei 0 zu starten
# Modellfunktion
def double_exp(r, a, b, c, d):
    return a * np.exp(b * r) + c * np.exp(d * r)

# Startwerte sind wichtig!
p0 = [10, 1.5, -10, -1.0]

#params, _ = curve_fit(double_exp, ratio, ca, p0=p0, maxfev=100000)

weights = 1 / (ca + 50)   # dämpft hohe Ca-Werte

params, _ = curve_fit(double_exp, ratio, ca, p0=p0, sigma=weights, absolute_sigma=False, maxfev=100000)

a, b, c, d = params
print(a, b, c, d)
