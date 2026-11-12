"""Labor EAN-V4, Aufgabe 1: Netzmodell fuer ein Niederspannungsnetz.

Externes Netz -- K1 --150 m-- K2 --150 m-- K3 --150 m-- K4 -- Last V1
Kabel: NAYY 4x120 SE
"""

import pandapower as pp

from md_export import export_ergebnisse, plot_netz


def erstelle_netz():
    """Baut das Netz aus Abbildung 1 auf und gibt es (unberechnet) zurueck."""
    # 1. leeres Netz
    net = pp.create_empty_network(name="Niederspannungsnetz Aufgabe 1")

    # 2. vier Niederspannungsknoten mit 0,4 kV
    k1 = pp.create_bus(net, vn_kv=0.4, name="Knoten 1")
    k2 = pp.create_bus(net, vn_kv=0.4, name="Knoten 2")
    k3 = pp.create_bus(net, vn_kv=0.4, name="Knoten 3")
    k4 = pp.create_bus(net, vn_kv=0.4, name="Knoten 4")

    # 3. vorgelagertes Netz am Knoten 1 mit 1,05 p.u.
    pp.create_ext_grid(net, bus=k1, vm_pu=1.05, name="Vorgelagertes Netz")

    # 4. Last am Knoten 4: P = 40 kW, Q = 15 kvar (pandapower rechnet in MW/Mvar)
    pp.create_load(net, bus=k4, p_mw=0.040, q_mvar=0.015, name="V1")

    # 5. Knoten mit je 150 m NAYY 4x120 SE zu einem Strang verbinden
    for von, nach, name in [(k1, k2, "Leitung 1-2"),
                            (k2, k3, "Leitung 2-3"),
                            (k3, k4, "Leitung 3-4")]:
        pp.create_line(net, from_bus=von, to_bus=nach, length_km=0.150,
                       std_type="NAYY 4x120 SE", name=name)
    return net


if __name__ == "__main__":
    net = erstelle_netz()

    # 6. Lastflussberechnung
    # Bei Fehlermeldungen hilft: pp.diagnostic(net)
    pp.runpp(net)

    print(net.res_bus)
    print(net.res_line[["i_ka", "loading_percent"]])
    print(net.res_ext_grid)

    bild = plot_netz(net, "ergebnisse/aufgabe1_netz.png",
                     titel="Aufgabe 1: Niederspannungsnetz")
    export_ergebnisse(net, "ergebnisse/aufgabe1.md",
                      titel="Aufgabe 1: Netzmodell für ein Niederspannungsnetz",
                      bild=bild)
