# -*- coding: utf-8 -*-
"""
Created on Thu Nov 19 2026

@author: julian fehre

Labor EAN-V5, Aufgabe 3: Spannungsabfall im Mittelspannungsnetz
Strahlennetz und Ringnetz im Vergleich.
Vorher aufgabe1_grundgeruest.py ausfuehren (speichert das Netz).
"""

import os

import pandas as pd
import pandapower as pp

# 1. load net from Aufgabe 1 and run power flow as radial net (switches open)
datei = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mittelspannungsnetz.json")
net = pp.from_json(datei)
net.switch["closed"] = False
pp.runpp(net)

spannung_strahl = net.res_bus.vm_pu.copy()
verluste_strahl = net.res_line.pl_mw.sum() + net.res_trafo.pl_mw.sum()

print("Strahlennetz - Knotenspannungen:")
print(net.res_bus.join(net.bus.name)[["name", "vm_pu"]].round(4).to_string(index=False))
print(f"Verluste Strahlennetz: {verluste_strahl * 1000:.1f} kW")


# 2. close switches -> ring net
net.switch["closed"] = True
pp.runpp(net)

spannung_ring = net.res_bus.vm_pu.copy()
verluste_ring = net.res_line.pl_mw.sum() + net.res_trafo.pl_mw.sum()


# 3. compare 20 kV busbar and last nodes of the feeders
namen = ["Sammelschiene 20 kV", "S1 K4", "S2 K4", "S3 K4", "S4 K4"]
idx = [net.bus.index[net.bus.name == n][0] for n in namen]
vergleich = pd.DataFrame({
    "Knoten": namen,
    "U Strahl [p.u.]": spannung_strahl[idx].values,
    "U Ring [p.u.]": spannung_ring[idx].values,
})
vergleich["Differenz [p.u.]"] = vergleich["U Ring [p.u.]"] - vergleich["U Strahl [p.u.]"]
print("\nVergleich Strahlennetz / Ringnetz:")
print(vergleich.round(4).to_string(index=False))

print(f"\nVerluste Strahlennetz: {verluste_strahl * 1000:.1f} kW")
print(f"Verluste Ringnetz:     {verluste_ring * 1000:.1f} kW")
print(f"Differenz:             {(verluste_ring - verluste_strahl) * 1000:.1f} kW")
