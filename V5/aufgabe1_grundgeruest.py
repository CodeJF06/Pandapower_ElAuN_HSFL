# -*- coding: utf-8 -*-
"""
Created on Thu Nov 19 2026

@author: julian fehre

Labor EAN-V5, Aufgabe 1: Mittelspannungsnetz in Ringtopologie
(Betrieb als Strahlennetz, Trennschalter am Ende der Straenge offen)
"""

import math
import os

import pandas as pd
import pandapower as pp

# create empty net
net = pp.create_empty_network(name="Mittelspannungsringnetz")

# create buses, external grid and transformer
# (geodata = Lage wie in Abbildung 1, fuer die Grafik in Aufgabe 2)
b110 = pp.create_bus(net, vn_kv=110, name="Netz 110 kV", geodata=(1.5, 2))
b20 = pp.create_bus(net, vn_kv=20, name="Sammelschiene 20 kV", geodata=(1.5, 0))
pp.create_ext_grid(net, bus=b110, vm_pu=1.0, name="Externes Netz")
pp.create_transformer(net, hv_bus=b110, lv_bus=b20, std_type="40 MVA 110/20 kV", name="Trafo 40 MVA")

# create feeders: Strang -> (Leitungstyp, Laengen in km)
# linker Ring = Erdkabel (S1, S2), rechter Ring = Freileitung (S3, S4)
kabel = "NA2XS2Y 1x150 RM/25 12/20 kV"
freileitung = "149-AL1/24-ST1A 20.0"
straenge = {
    "S1": (kabel, [3, 2, 4, 6]),
    "S2": (kabel, [4, 1, 2, 4]),
    "S3": (freileitung, [3, 2, 4, 6]),
    "S4": (freileitung, [4, 1, 2, 4]),
}
knoten = {}
for x, (strang, (typ, laengen)) in enumerate(straenge.items()):
    vorher = b20
    for i, laenge in enumerate(laengen, start=1):
        name = f"{strang} K{i}"
        knoten[name] = pp.create_bus(net, vn_kv=20, name=name, geodata=(x, -i))
        pp.create_line(net, from_bus=vorher, to_bus=knoten[name], length_km=laenge, std_type=typ,
                       name=f"{strang} L{i}", geodata=[(x, 1 - i), (x, -i)])
        vorher = knoten[name]

# create open switches at the end of the feeders (Strahlennetz)
pp.create_switch(net, bus=knoten["S1 K4"], element=knoten["S2 K4"], et="b", closed=False, name="Trennstelle Kabelring")
pp.create_switch(net, bus=knoten["S3 K4"], element=knoten["S4 K4"], et="b", closed=False, name="Trennstelle Freileitungsring")

# create loads (Name, Knoten, P in MW, cos phi induktiv) and generators (cos phi = 1)
lasten = [
    ("V1", "S1 K1", 5.2, 0.95), ("V2", "S1 K2", 6.5, 0.97), ("V3", "S1 K3", 4.8, 0.95),
    ("V4", "S2 K2", 3.6, 0.90), ("V5", "S2 K3", 2.8, 0.95),
    ("V6", "S3 K1", 5.2, 0.95), ("V7", "S3 K2", 6.5, 0.97), ("V8", "S3 K3", 4.8, 0.95),
    ("V9", "S4 K2", 3.6, 0.90), ("V10", "S4 K3", 2.8, 0.95),
]
for name, k, p, cos_phi in lasten:
    pp.create_load(net, bus=knoten[k], p_mw=p, q_mvar=p * math.tan(math.acos(cos_phi)), name=name)

for name, k, p in [("G1", "S1 K4", 6.0), ("G2", "S2 K1", 5.0), ("G3", "S3 K4", 6.0), ("G4", "S4 K1", 5.0)]:
    pp.create_sgen(net, bus=knoten[k], p_mw=p, q_mvar=0.0, name=name)


# 1. check net (diagnostic first, it overwrites the results), power flow, maximum voltage drop
pp.diagnostic(net, warnings_only=True)
pp.runpp(net)
print("Lastfluss konvergiert:", net.converged)

mv = net.bus.vn_kv == 20
abfall = ((1 - net.res_bus.vm_pu[mv]) * 100).set_axis(net.bus.name[mv])
print("\nSpannungsabfall 20 kV [%]:")
print(abfall.round(2).to_string())
print(f"Maximum: {abfall.max():.2f} % an {abfall.idxmax()}")

# 2. power exchanged with the external grid (P, Q > 0 = Bezug aus 110 kV)
print("\nExternes Netz:")
print(net.res_ext_grid)
print("Kontrolle P: Lasten - Erzeugung + Verluste =",
      round(net.res_load.p_mw.sum() - net.res_sgen.p_mw.sum()
            + net.res_line.pl_mw.sum() + net.res_trafo.pl_mw.sum(), 3), "MW")

# 3. compare the four feeders
strang_leitung = net.line.name.str[:2]
strang_knoten = net.bus.name.str[:2]
print("\nVergleich der Straenge:")
print(pd.DataFrame({
    "max. Auslastung [%]": net.res_line.loading_percent.groupby(strang_leitung).max(),
    "U min [p.u.]": net.res_bus.vm_pu.groupby(strang_knoten).min()[list(straenge)],
    "U Ende [p.u.]": [net.res_bus.vm_pu[knoten[f"{s} K4"]] for s in straenge],
}).round(4))

# 4. losses of lines (per feeder) and transformer, reactive power (Q > 0 = Aufnahme)
verluste = net.res_line[["pl_mw", "ql_mvar"]].groupby(strang_leitung).sum()
verluste.loc["Trafo"] = net.res_trafo[["pl_mw", "ql_mvar"]].sum()
verluste.loc["Summe"] = verluste.sum()
print("\nVerluste:")
print(verluste.round(4))

# save net for Aufgabe 2 and 3
datei = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mittelspannungsnetz.json")
pp.to_json(net, datei)
print("\nNetz gespeichert:", datei)
