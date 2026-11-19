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

# load net from Aufgabe 1
datei = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mittelspannungsnetz.json")
net = pp.from_json(datei)


# run power flow with open (Strahlennetz) or closed switches (Ringnetz)
def rechnen(ring):
    net.switch["closed"] = ring
    pp.runpp(net)
    return net.res_bus.vm_pu.copy(), net.res_line.pl_mw.sum() + net.res_trafo.pl_mw.sum()


# 1. + 2. radial net, then ring net
u_strahl, verluste_strahl = rechnen(ring=False)
u_ring, verluste_ring = rechnen(ring=True)

# 3. compare node voltages and losses
vergleich = pd.DataFrame({"U Strahl [p.u.]": u_strahl, "U Ring [p.u.]": u_ring}).set_axis(net.bus.name)
vergleich["Differenz [p.u.]"] = vergleich["U Ring [p.u.]"] - vergleich["U Strahl [p.u.]"]
print("Knotenspannungen:")
print(vergleich.round(4))

print(f"\nVerluste Strahlennetz: {verluste_strahl * 1000:.1f} kW")
print(f"Verluste Ringnetz:     {verluste_ring * 1000:.1f} kW")
print(f"Differenz:             {(verluste_ring - verluste_strahl) * 1000:.1f} kW")
