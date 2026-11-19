# -*- coding: utf-8 -*-
"""
Created on Wed Nov 18 2026

@author: julian fehre
"""

import pandapower as pp
# create empty net
net = pp.create_empty_network()

# create buses
b1 = pp.create_bus(net, vn_kv=0.4, name="Knoten 1")
b2 = pp.create_bus(net, vn_kv=0.4, name="Knoten 2")
b3 = pp.create_bus(net, vn_kv=0.4, name="Knoten 3")
b4 = pp.create_bus(net, vn_kv=0.4, name="Knoten 4")

# create bus elements
pp.create_ext_grid(net, bus=b1, vm_pu=1.05, name="Vorgelagertes Netz")
v1 = pp.create_load(net, bus=b4, p_mw=0.04, q_mvar=0.015, name="V1")

# create branch elements
pp.create_line(net, from_bus=b1, to_bus=b2, length_km=0.15, name="Leitung 1-2", std_type="NAYY 4x120 SE")
pp.create_line(net, from_bus=b2, to_bus=b3, length_km=0.15, name="Leitung 2-3", std_type="NAYY 4x120 SE")
pp.create_line(net, from_bus=b3, to_bus=b4, length_km=0.15, name="Leitung 3-4", std_type="NAYY 4x120 SE")


# run power flow and print results
def rechnen(titel):
    pp.runpp(net)
    print("\n=====", titel, "=====")
    print(net.res_bus[["vm_pu", "va_degree"]])
    print(net.res_ext_grid)
    print(net.res_line[["i_ka", "loading_percent"]])


rechnen("Ausgangszustand")


# 2.1 change load at bus 4 (P and Q separately)
net.load.at[v1, "p_mw"] = 0.02
rechnen("2.1 P halbiert (20 kW)")
net.load.at[v1, "p_mw"] = 0.08
rechnen("2.1 P verdoppelt (80 kW)")
net.load.at[v1, "p_mw"] = 0.04

net.load.at[v1, "q_mvar"] = 0.0075
rechnen("2.1 Q halbiert (7,5 kvar)")
net.load.at[v1, "q_mvar"] = 0.03
rechnen("2.1 Q verdoppelt (30 kvar)")
net.load.at[v1, "q_mvar"] = 0.015


# 2.2 static generator at bus 4, load off
g4 = pp.create_sgen(net, bus=b4, p_mw=0.0, q_mvar=0.0, name="G4")
net.load.at[v1, "in_service"] = False

for p_kw in [10, 20, 40, 50, 0]:
    net.sgen.at[g4, "p_mw"] = p_kw / 1000
    rechnen(f"2.2 G4: P = {p_kw} kW")
    print("U Speiseknoten:", net.res_bus.at[b1, "vm_pu"], " U Knoten 4:", net.res_bus.at[b4, "vm_pu"])


# 2.3 reactive power of generator (P = 0)
# q_mvar < 0: generator absorbs reactive power (induktiv)
# q_mvar > 0: generator supplies reactive power (kapazitiv)
for q_kvar in [-25, -50, 25, 50]:
    net.sgen.at[g4, "q_mvar"] = q_kvar / 1000
    rechnen(f"2.3 G4: Q = {q_kvar} kvar")
    print("U Speiseknoten:", net.res_bus.at[b1, "vm_pu"], " U Knoten 4:", net.res_bus.at[b4, "vm_pu"])
net.sgen.at[g4, "q_mvar"] = 0.0


# 2.4 additional loads at bus 2 and bus 3, generator off
net.sgen.at[g4, "in_service"] = False
v2 = pp.create_load(net, bus=b2, p_mw=0.02, q_mvar=0.005, name="V2")
v3 = pp.create_load(net, bus=b3, p_mw=0.02, q_mvar=0.005, name="V3")
rechnen("2.4 Lasten an Knoten 2 und 3")


# 2.5 generator at bus 4 on, second generator at bus 2, each 30 kW
net.sgen.at[g4, "in_service"] = True
net.sgen.at[g4, "p_mw"] = 0.03
g2 = pp.create_sgen(net, bus=b2, p_mw=0.03, q_mvar=0.0, name="G2")
rechnen("2.5 G2 und G4 je 30 kW")


# 2.6 compensate voltage rise with inductive reactive power of the generators
for q_kvar in [-10, -20, -30, -40, -50, -60]:
    net.sgen.at[g2, "q_mvar"] = q_kvar / 1000
    net.sgen.at[g4, "q_mvar"] = q_kvar / 1000
    rechnen(f"2.6 G2 und G4: Q = {q_kvar} kvar (Q/P = {abs(q_kvar) / 30:.2f})")
    print("hoechste Spannung:", net.res_bus.vm_pu.max())
