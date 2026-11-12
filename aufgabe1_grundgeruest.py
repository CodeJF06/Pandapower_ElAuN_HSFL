# -*- coding: utf-8 -*-
"""
Created on Thu Nov 12 15:10:16 2026

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
pp.create_load(net, bus=b4, p_mw=0.04, q_mvar=0.015, name="V1")

# create branch elements
pp.create_line(net, from_bus=b1, to_bus=b2, length_km=0.15, name="Leitung 1-2", std_type="NAYY 4x120 SE")
pp.create_line(net, from_bus=b2, to_bus=b3, length_km=0.15, name="Leitung 2-3", std_type="NAYY 4x120 SE")
pp.create_line(net, from_bus=b3, to_bus=b4, length_km=0.15, name="Leitung 3-4", std_type="NAYY 4x120 SE")

# run power flow
pp.runpp(net)

# print results
print(net.res_bus)
print(net.res_line)
print(net.res_ext_grid)
