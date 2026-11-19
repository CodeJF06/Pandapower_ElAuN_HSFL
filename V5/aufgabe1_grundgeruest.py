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

# create buses (geodata = Lage wie in Abbildung 1, fuer die Grafik in Aufgabe 2)
b110 = pp.create_bus(net, vn_kv=110, name="Netz 110 kV", geodata=(1.5, 2))
b20 = pp.create_bus(net, vn_kv=20, name="Sammelschiene 20 kV", geodata=(1.5, 0))

# create external grid and transformer
pp.create_ext_grid(net, bus=b110, vm_pu=1.0, name="Externes Netz")
pp.create_transformer(net, hv_bus=b110, lv_bus=b20, std_type="40 MVA 110/20 kV", name="Trafo 40 MVA")

# create feeders: Strang -> (Leitungstyp, Laengen in km, Spalte im Bild)
# linker Ring = Erdkabel (S1, S2), rechter Ring = Freileitung (S3, S4)
kabel = "NA2XS2Y 1x150 RM/25 12/20 kV"
freileitung = "149-AL1/24-ST1A 20.0"
straenge = {
    "S1": (kabel, [3, 2, 4, 6], 0),
    "S2": (kabel, [4, 1, 2, 4], 1),
    "S3": (freileitung, [3, 2, 4, 6], 2),
    "S4": (freileitung, [4, 1, 2, 4], 3),
}

knoten = {}
for strang, (typ, laengen, x) in straenge.items():
    vorher = b20
    for i, laenge in enumerate(laengen, start=1):
        name = f"{strang} K{i}"
        knoten[name] = pp.create_bus(net, vn_kv=20, name=name, geodata=(x, -i))
        pp.create_line(net, from_bus=vorher, to_bus=knoten[name], length_km=laenge,
                       std_type=typ, name=f"{strang} L{i}", geodata=[(x, 1 - i), (x, -i)])
        vorher = knoten[name]

# create switches at the end of the feeders (open = Strahlennetz)
pp.create_switch(net, bus=knoten["S1 K4"], element=knoten["S2 K4"], et="b", closed=False, name="Trennstelle Kabelring")
pp.create_switch(net, bus=knoten["S3 K4"], element=knoten["S4 K4"], et="b", closed=False, name="Trennstelle Freileitungsring")


# create loads: (Name, Knoten, P in MW, cos phi induktiv)
def q_mvar(p_mw, cos_phi):
    return p_mw * math.tan(math.acos(cos_phi))


lasten = [
    ("V1", "S1 K1", 5.2, 0.95), ("V2", "S1 K2", 6.5, 0.97), ("V3", "S1 K3", 4.8, 0.95),
    ("V4", "S2 K2", 3.6, 0.90), ("V5", "S2 K3", 2.8, 0.95),
    ("V6", "S3 K1", 5.2, 0.95), ("V7", "S3 K2", 6.5, 0.97), ("V8", "S3 K3", 4.8, 0.95),
    ("V9", "S4 K2", 3.6, 0.90), ("V10", "S4 K3", 2.8, 0.95),
]
for name, k, p, cos_phi in lasten:
    pp.create_load(net, bus=knoten[k], p_mw=p, q_mvar=q_mvar(p, cos_phi), name=name)

# create generators (static generators, cos phi = 1)
generatoren = [("G1", "S1 K4", 6.0), ("G2", "S2 K1", 5.0), ("G3", "S3 K4", 6.0), ("G4", "S4 K1", 5.0)]
for name, k, p in generatoren:
    pp.create_sgen(net, bus=knoten[k], p_mw=p, q_mvar=0.0, name=name)


# 1. check net (diagnostic first, it overwrites the results), power flow, maximum voltage drop
pp.diagnostic(net, warnings_only=True)
pp.runpp(net)
print("Lastfluss konvergiert:", net.converged)

res = net.res_bus.join(net.bus[["name", "vn_kv"]])
mv = res[res.vn_kv == 20].copy()
mv["Spannungsabfall [%]"] = (1 - mv.vm_pu) * 100
print("\nKnotenspannungen 20 kV:")
print(mv[["name", "vm_pu", "Spannungsabfall [%]"]].round(4).to_string(index=False))
k_max = mv["Spannungsabfall [%]"].idxmax()
print(f"\nMaximaler Spannungsabfall: {mv.at[k_max, 'Spannungsabfall [%]']:.2f} % an {mv.at[k_max, 'name']}")


# 2. power exchanged with the external grid
print("\nExternes Netz (P, Q > 0 = Bezug aus 110 kV):")
print(net.res_ext_grid)
p_kontrolle = (net.res_load.p_mw.sum() - net.res_sgen.p_mw.sum()
               + net.res_line.pl_mw.sum() + net.res_trafo.pl_mw.sum())
print(f"Kontrolle: Lasten - Erzeugung + Verluste = {p_kontrolle:.3f} MW")


# 3. compare the four feeders
leitungen = net.res_line.join(net.line[["name", "to_bus"]])
leitungen["Strang"] = leitungen.name.str[:2]
strang_knoten = mv[mv.name.str.match(r"S\d ")].copy()
strang_knoten["Strang"] = strang_knoten.name.str[:2]
vergleich = pd.DataFrame({
    "max. Auslastung [%]": leitungen.groupby("Strang").loading_percent.max(),
    "U min [p.u.]": strang_knoten.groupby("Strang").vm_pu.min(),
    "U Ende [p.u.]": [net.res_bus.at[knoten[f"{s} K4"], "vm_pu"] for s in straenge],
})
print("\nVergleich der Straenge:")
print(vergleich.round(4))


# 4. losses of lines (per feeder) and transformer, reactive power
verluste = leitungen.groupby("Strang")[["pl_mw", "ql_mvar"]].sum()
verluste.loc["Trafo"] = [net.res_trafo.pl_mw.sum(), net.res_trafo.ql_mvar.sum()]
verluste.loc["Summe"] = verluste.sum()
print("\nVerluste (P in MW, Q in Mvar; Q > 0 = Aufnahme):")
print(verluste.round(4))


# save net for Aufgabe 2 and 3
datei = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mittelspannungsnetz.json")
pp.to_json(net, datei)
print("\nNetz gespeichert:", datei)
