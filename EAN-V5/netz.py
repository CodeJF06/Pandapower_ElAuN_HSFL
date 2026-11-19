"""Labor EAN-V5: Mittelspannungsringnetz (Abbildung 1, Tabelle 1).

Oben in NETZDATEN steht das Netz, darunter der Code, den aufgabe1.py bis
aufgabe3.py gemeinsam nutzen (Netz aufbauen, Auswertungen, Diagramme).
"""

# ===========================================================================
# NETZDATEN  -  nur hier aendern
# ===========================================================================

EXTERNES_NETZ_U_PU = 1.0
TRAFO_TYP = "40 MVA 110/20 kV"

KABEL = "NA2XS2Y 1x150 RM/25 12/20 kV"
FREILEITUNG = "149-AL1/24-ST1A 20.0"

# Strang: (Leitungstyp, Laengen der Abschnitte in km, vom 20-kV-Knoten aus)
STRAENGE = {
    "S1": (KABEL, [3, 2, 4, 6]),
    "S2": (KABEL, [4, 1, 2, 4]),
    "S3": (FREILEITUNG, [3, 2, 4, 6]),
    "S4": (FREILEITUNG, [4, 1, 2, 4]),
}

# Trennstellen am Ende der Straenge: (Name, Knoten, Knoten)
TRENNSTELLEN = [
    ("Trennstelle Kabelring", "S1 K4", "S2 K4"),
    ("Trennstelle Freileitungsring", "S3 K4", "S4 K4"),
]

# Lasten: (Name, Knoten, P in MW, cos phi induktiv)
LASTEN = [
    ("V1", "S1 K1", 5.2, 0.95), ("V2", "S1 K2", 6.5, 0.97), ("V3", "S1 K3", 4.8, 0.95),
    ("V4", "S2 K2", 3.6, 0.90), ("V5", "S2 K3", 2.8, 0.95),
    ("V6", "S3 K1", 5.2, 0.95), ("V7", "S3 K2", 6.5, 0.97), ("V8", "S3 K3", 4.8, 0.95),
    ("V9", "S4 K2", 3.6, 0.90), ("V10", "S4 K3", 2.8, 0.95),
]

# Generatoren (Static Generator, cos phi = 1): (Name, Knoten, P in MW)
GENERATOREN = [("G1", "S1 K4", 6.0), ("G2", "S2 K1", 5.0), ("G3", "S3 K4", 6.0), ("G4", "S4 K1", 5.0)]

# ===========================================================================
# Ab hier muss nichts mehr geaendert werden
# ===========================================================================

import math  # noqa: E402
import os  # noqa: E402
import sys  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402
import pandapower as pp  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from netzberechnung import FARBEN, md_tabelle, zahl  # noqa: E402

SAMMELSCHIENE = "Sammelschiene 20 kV"


def erstelle_netz(ring=False):
    """Baut das Netz auf. ring=True schliesst die Trennstellen (Ringnetz)."""
    net = pp.create_empty_network(name="Mittelspannungsringnetz")
    b110 = pp.create_bus(net, vn_kv=110, name="Netz 110 kV", geodata=(1.5, 2))
    b20 = pp.create_bus(net, vn_kv=20, name=SAMMELSCHIENE, geodata=(1.5, 0))
    pp.create_ext_grid(net, bus=b110, vm_pu=EXTERNES_NETZ_U_PU, name="Externes Netz")
    pp.create_transformer(net, hv_bus=b110, lv_bus=b20, std_type=TRAFO_TYP, name="Trafo")

    knoten = {}
    for x, (strang, (typ, laengen)) in enumerate(STRAENGE.items()):
        vorher = b20
        for i, laenge in enumerate(laengen, start=1):
            name = f"{strang} K{i}"
            knoten[name] = pp.create_bus(net, vn_kv=20, name=name, geodata=(x, -i))
            pp.create_line(net, from_bus=vorher, to_bus=knoten[name], length_km=laenge,
                           std_type=typ, name=f"{strang} L{i}", geodata=[(x, 1 - i), (x, -i)])
            vorher = knoten[name]

    for name, a, b in TRENNSTELLEN:
        pp.create_switch(net, bus=knoten[a], element=knoten[b], et="b", closed=ring, name=name)
    for name, k, p, cos_phi in LASTEN:
        pp.create_load(net, bus=knoten[k], p_mw=p, q_mvar=p * math.tan(math.acos(cos_phi)),
                       name=name)
    for name, k, p in GENERATOREN:
        pp.create_sgen(net, bus=knoten[k], p_mw=p, q_mvar=0.0, name=name)
    return net


def bus(net, name):
    return net.bus.index[net.bus.name == name][0]


def strang_von(namen):
    """'S1 K2' -> 'S1' (fuer Knoten und Leitungen)."""
    return namen.str.split(" ").str[0]


def entfernung_km(strang, i):
    """Leitungslaenge vom 20-kV-Knoten bis Knoten i des Strangs."""
    return sum(STRAENGE[strang][1][:i])


# ---------------------------------------------------------------------------
# Tabellen
# ---------------------------------------------------------------------------

def md_netzdaten(net):
    """Trafo, Leitungstypen, Straenge, Lasten und Generatoren als Markdown."""
    t = net.trafo.iloc[0]
    trafo = md_tabelle(
        ["Typ", "S_r [MVA]", "U_OS / U_US [kV]", "u_k [%]", "u_kr [%]", "P_Fe [kW]",
         "Stufen", "Stufe [%]"],
        [[TRAFO_TYP, f"{t.sn_mva:.0f}", f"{t.vn_hv_kv:.0f} / {t.vn_lv_kv:.0f}",
          f"{t.vk_percent:.2f}", f"{t.vkr_percent:.2f}", f"{t.pfe_kw:.0f}",
          f"{t.tap_min:.0f} … {t.tap_max:.0f}", f"{t.tap_step_percent:.2f}"]])
    typen = net.line.drop_duplicates("std_type")
    leitungen = md_tabelle(
        ["Leitungstyp", "Art", "R' [Ω/km]", "X' [Ω/km]", "C' [nF/km]", "X/R", "I_max [A]"],
        [[l.std_type, "Kabel" if l.type == "cs" else "Freileitung", f"{l.r_ohm_per_km:.3f}",
          f"{l.x_ohm_per_km:.3f}", f"{l.c_nf_per_km:.0f}",
          f"{l.x_ohm_per_km / l.r_ohm_per_km:.2f}", f"{l.max_i_ka * 1000:.0f}"]
         for l in typen.itertuples()])
    straenge = md_tabelle(
        ["Strang", "Leitungstyp", "Abschnitte [km]", "Länge [km]"],
        [[s, typ, " / ".join(str(x) for x in laengen), f"{sum(laengen)}"]
         for s, (typ, laengen) in STRAENGE.items()])
    elemente = md_tabelle(
        ["Element", "Knoten", "P [MW]", "cos φ", "Q [Mvar]"],
        [[n, k, f"{p:.1f}", f"{c:.2f} ind.", f"{p * math.tan(math.acos(c)):.2f}"]
         for n, k, p, c in LASTEN]
        + [[n, k, f"{p:.1f}", "1.00", "0.00"] for n, k, p in GENERATOREN])
    return (f"### Transformator\n\n{trafo}\n\n### Leitungen\n\n{leitungen}\n\n"
            f"### Stränge\n\n{straenge}\n\n### Lasten und Generatoren\n\n{elemente}")


def md_knotenspannungen(net):
    """Spannungen aller 20-kV-Knoten mit Spannungsabfall bezogen auf 20 kV."""
    zeilen = []
    for b, r in net.res_bus.iterrows():
        if net.bus.at[b, "vn_kv"] == 20:
            zeilen.append([net.bus.at[b, "name"], f"{r.vm_pu:.4f}", f"{r.vm_pu * 20:.2f}",
                           f"{(1 - r.vm_pu) * 100:.2f}"])
    return md_tabelle(["Knoten", "U [p.u.]", "U [kV]", "ΔU [%]"], zeilen)


def strang_werte(net):
    """Kennwerte je Strang als dict {Strang: {...}}."""
    s_line, s_bus = strang_von(net.line.name), strang_von(net.bus.name)
    s_load, s_sgen = strang_von(net.bus.name[net.load.bus].reset_index(drop=True)), \
        strang_von(net.bus.name[net.sgen.bus].reset_index(drop=True))
    werte = {}
    for s in STRAENGE:
        zeilen = net.res_line[s_line == s]
        werte[s] = {
            "last": net.res_load.p_mw[s_load.values == s].sum(),
            "erzeugung": net.res_sgen.p_mw[s_sgen.values == s].sum(),
            "auslastung": zeilen.loading_percent.max(),
            "strom": zeilen.i_ka.max() * 1000,
            "u_min": net.res_bus.vm_pu[s_bus == s].min(),
            "u_ende": net.res_bus.vm_pu[bus(net, f"{s} K{len(STRAENGE[s][1])}")],
            "pl": zeilen.pl_mw.sum() * 1000,
            "ql": zeilen.ql_mvar.sum() * 1000,
        }
    return werte


def md_straenge(net):
    zeilen = []
    for s, w in strang_werte(net).items():
        zeilen.append([s, "Kabel" if STRAENGE[s][0] == KABEL else "Freileitung",
                       f"{sum(STRAENGE[s][1])}", f"{w['last']:.1f}", f"{w['erzeugung']:.1f}",
                       f"{w['last'] - w['erzeugung']:.1f}", f"{w['strom']:.0f}",
                       f"{w['auslastung']:.1f}", f"{w['u_min']:.4f}", f"{w['u_ende']:.4f}"])
    return md_tabelle(["Strang", "Art", "Länge [km]", "P Last [MW]", "P Erzeugung [MW]",
                       "P Saldo [MW]", "I max [A]", "max. Auslastung [%]", "U min [p.u.]",
                       "U Ende [p.u.]"], zeilen)


def md_leitungen(net):
    zeilen = []
    for l, r in zip(net.line.itertuples(), net.res_line.itertuples()):
        zeilen.append([l.name, net.bus.at[l.from_bus, "name"], net.bus.at[l.to_bus, "name"],
                       f"{l.length_km:.0f}", f"{r.i_ka * 1000:.0f}", f"{r.loading_percent:.1f}",
                       zahl(r.pl_mw * 1000, 1), zahl(r.ql_mvar * 1000, 1)])
    return md_tabelle(["Leitung", "von", "nach", "Länge [km]", "I [A]", "Auslastung [%]",
                       "P_V [kW]", "Q_V [kvar]"], zeilen)


def verluste(net):
    """Verluste je Strang, Trafo und gesamt: dict {Name: (P in kW, Q in kvar)}."""
    werte = {s: (w["pl"], w["ql"]) for s, w in strang_werte(net).items()}
    werte["Leitungen gesamt"] = (net.res_line.pl_mw.sum() * 1000, net.res_line.ql_mvar.sum() * 1000)
    werte["Transformator"] = (net.res_trafo.pl_mw.sum() * 1000, net.res_trafo.ql_mvar.sum() * 1000)
    werte["Netz gesamt"] = tuple(a + b for a, b in zip(werte["Leitungen gesamt"],
                                                        werte["Transformator"]))
    return werte


# ---------------------------------------------------------------------------
# Diagramm
# ---------------------------------------------------------------------------

def plot_spannungsprofil(netze, datei, titel):
    """Spannung ueber der Entfernung zum 20-kV-Knoten, eine Farbe je Strang.
    netze: Liste (Bezeichnung, berechnetes Netz); das zweite Netz gestrichelt."""
    fig, ax = plt.subplots(figsize=(9, 4.4))
    stile = ["-", "--"]
    for nr, (bezeichnung, net) in enumerate(netze):
        u0 = net.res_bus.vm_pu[bus(net, SAMMELSCHIENE)]
        for farbe, s in zip(FARBEN, STRAENGE):
            n = len(STRAENGE[s][1])
            x = [entfernung_km(s, i) for i in range(n + 1)]
            u = [u0] + [net.res_bus.vm_pu[bus(net, f"{s} K{i}")] for i in range(1, n + 1)]
            art = "Kabel" if STRAENGE[s][0] == KABEL else "Freileitung"
            name = f"{s} ({art})" + (f", {bezeichnung}" if len(netze) > 1 else "")
            ax.plot(x, u, stile[nr % 2], color=farbe, lw=2, marker="o", ms=5, label=name)
    ax.set_xlabel("Entfernung zur 20-kV-Sammelschiene [km]")
    ax.set_ylabel("Spannung [p.u.]")
    ax.set_title(titel, fontsize=11)
    ax.grid(color="0.9")
    for seite in ("top", "right"):
        ax.spines[seite].set_visible(False)
    ax.legend(loc="center left", bbox_to_anchor=(1.01, 0.5), frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(datei, dpi=200)
    plt.close(fig)
    print(f"Bild gespeichert:       {datei}")


def schreibe_md(datei, teile):
    os.makedirs(os.path.dirname(datei) or ".", exist_ok=True)
    with open(datei, "w", encoding="utf-8") as f:
        f.write("\n\n".join(t.strip() for t in teile if t) + "\n")
    print(f"Ergebnisse geschrieben: {datei}")
