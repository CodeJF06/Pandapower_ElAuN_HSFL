# -*- coding: utf-8 -*-
"""
Created on Thu Nov 19 2026

@author: julian fehre

Labor EAN-V5, Aufgabe 2: Graphische Darstellung des Netzes
Vorher einmal in der iPython-Konsole: pip install pandapower["all"]
und aufgabe1_grundgeruest.py ausfuehren (speichert das Netz).
"""

import os

import pandapower as pp
from pandapower.plotting.plotly import simple_plotly
import plotly.io as pio
pio.templates.default = "plotly_white"

# load net from Aufgabe 1
datei = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mittelspannungsnetz.json")
net = pp.from_json(datei)

# plot net (opens in the browser)
simple_plotly(net)
