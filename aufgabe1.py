"""Labor EAN-V4: Netzberechnung mit pandapower und Export als Markdown.

Oben im Abschnitt NETZDATEN wird das Netz beschrieben, beim Ausfuehren (F5)
wird es aufgebaut, berechnet und als Markdown-Datei mit Netzplan gespeichert.
Fuer ein neues Netz: Datei kopieren (z.B. aufgabe2.py) und nur den Abschnitt
NETZDATEN anpassen.
"""

# ===========================================================================
# NETZDATEN  -  nur hier aendern
# ===========================================================================

TITEL = "Aufgabe 1: Netzmodell für ein Niederspannungsnetz"
AUSGABE = "ergebnisse/aufgabe1.md"       # Netzplan landet daneben als .png

NENNSPANNUNG_KV = 0.4
LEITUNGSTYP = "NAYY 4x120 SE"            # Standardtyp aus pandapower

KNOTEN = ["Knoten 1", "Knoten 2", "Knoten 3", "Knoten 4"]

EXTERNES_NETZ = {"name": "Vorgelagertes Netz", "knoten": "Knoten 1", "u_pu": 1.05}

# (von, nach, Laenge in m)  -  optional als 4. Wert ein anderer Leitungstyp
LEITUNGEN = [
    ("Knoten 1", "Knoten 2", 150),
    ("Knoten 2", "Knoten 3", 150),
    ("Knoten 3", "Knoten 4", 150),
]

# q_kvar > 0: Last nimmt induktive Blindleistung auf
# optional  "an": False  = Element ist vorhanden, aber ausgeschaltet
LASTEN = [
    {"name": "V1", "knoten": "Knoten 4", "p_kw": 40, "q_kvar": 15},
]

# Static Generators. p_kw > 0: Einspeisung.
# q_kvar > 0: gibt Blindleistung ab, q_kvar < 0: nimmt (induktive) Blindleistung auf
GENERATOREN = [
    # {"name": "G4", "knoten": "Knoten 4", "p_kw": 0, "q_kvar": 0},
]

# Varianten: Jede Variante startet vom Netz oben und aendert einzelne Lasten
# oder Generatoren (ueber deren Namen). Erlaubt sind p_kw, q_kvar und an.
# Leere Liste = nur das Netz oben wird berechnet.
VARIANTEN = [
    # {"titel": "P halbiert", "V1": {"p_kw": 20}},
    # {"titel": "Last aus, Generator 10 kW", "V1": {"an": False}, "G4": {"p_kw": 10},
    #  "notiz": "Beobachtung: ..."},
]

BILD_JE_VARIANTE = False                 # True: eigener Netzplan pro Variante

# ===========================================================================
# Ab hier muss nichts mehr geaendert werden
# ===========================================================================

import os

import matplotlib.pyplot as plt
import pandapower as pp


# ---------------------------------------------------------------------------
# Netz aufbauen und berechnen
# ---------------------------------------------------------------------------

def baue_netz():
    """Erstellt das pandapower-Netz aus den NETZDATEN."""
    net = pp.create_empty_network(name=TITEL)

    bus = {}                             # Knotenname -> pandapower-Index
    for name in KNOTEN:
        bus[name] = pp.create_bus(net, vn_kv=NENNSPANNUNG_KV, name=name)

    def knoten(name):
        if name not in bus:
            raise ValueError(f"Knoten '{name}' steht nicht in KNOTEN {KNOTEN}")
        return bus[name]

    pp.create_ext_grid(net, bus=knoten(EXTERNES_NETZ["knoten"]),
                       vm_pu=EXTERNES_NETZ["u_pu"], name=EXTERNES_NETZ["name"])

    for von, nach, laenge_m, *typ in LEITUNGEN:
        pp.create_line(net, from_bus=knoten(von), to_bus=knoten(nach),
                       length_km=laenge_m / 1000, name=f"{von} – {nach}",
                       std_type=typ[0] if typ else LEITUNGSTYP)

    # pandapower rechnet in MW / Mvar
    for last in LASTEN:
        pp.create_load(net, bus=knoten(last["knoten"]), name=last["name"],
                       p_mw=last["p_kw"] / 1000, q_mvar=last["q_kvar"] / 1000,
                       in_service=last.get("an", True))

    for gen in GENERATOREN:
        pp.create_sgen(net, bus=knoten(gen["knoten"]), name=gen["name"],
                       p_mw=gen["p_kw"] / 1000, q_mvar=gen["q_kvar"] / 1000,
                       in_service=gen.get("an", True))

    namen = list(net.load.name) + list(net.sgen.name)
    doppelt = {n for n in namen if namen.count(n) > 1}
    if doppelt:
        raise ValueError(f"Namen von Lasten/Generatoren doppelt vergeben: {doppelt}")
    return net


def wende_variante_an(net, variante):
    """Uebernimmt die Aenderungen einer Variante in das Netz."""
    for name, aenderung in variante.items():
        if name in ("titel", "notiz"):
            continue
        for tabelle in (net.load, net.sgen):
            treffer = tabelle.index[tabelle.name == name]
            if len(treffer):
                break
        else:
            raise ValueError(f"Variante '{variante['titel']}': keine Last und kein "
                             f"Generator mit dem Namen '{name}'")
        for schluessel, wert in aenderung.items():
            if schluessel == "p_kw":
                tabelle.loc[treffer, "p_mw"] = wert / 1000
            elif schluessel == "q_kvar":
                tabelle.loc[treffer, "q_mvar"] = wert / 1000
            elif schluessel == "an":
                tabelle.loc[treffer, "in_service"] = bool(wert)
            else:
                raise ValueError(f"Variante '{variante['titel']}': '{schluessel}' ist "
                                 "nicht erlaubt (nur p_kw, q_kvar, an)")


def berechne(net):
    """Lastflussberechnung. Gibt False zurueck, wenn sie nicht konvergiert."""
    try:
        pp.runpp(net, numba=False)
        return True
    except pp.auxiliary.LoadflowNotConverged:
        return False


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------

def md_tabelle(kopf, zeilen):
    """kopf: Spaltennamen, zeilen: Liste von Zeilen. Zahlen vorher formatieren."""
    def ist_zahl(text):
        if text == "–":                      # Platzhalter fuer "kein Wert"
            return True
        try:
            float(text)
            return True
        except ValueError:
            return False

    zeilen = [[str(z) for z in zeile] for zeile in zeilen]
    rechts = [bool(zeilen) and all(ist_zahl(z[i]) for z in zeilen)
              for i in range(len(kopf))]
    text = ["| " + " | ".join(kopf) + " |",
            "| " + " | ".join("---:" if r else ":---" for r in rechts) + " |"]
    text += ["| " + " | ".join(zeile) + " |" for zeile in zeilen]
    return "\n".join(text)


def busname(net, bus):
    return net.bus.at[bus, "name"]


def md_leitungstypen(net):
    typen = net.line.drop_duplicates("std_type")
    return md_tabelle(
        ["Leitungstyp", "R' [Ω/km]", "X' [Ω/km]", "X/R", "I_max [A]"],
        [[t.std_type, f"{t.r_ohm_per_km:.3f}", f"{t.x_ohm_per_km:.3f}",
          f"{t.x_ohm_per_km / t.r_ohm_per_km:.3f}", f"{t.max_i_ka * 1000:.0f}"]
         for t in typen.itertuples()])


def md_einstellungen(net):
    """Eingestellte Leistungen von Lasten und Generatoren."""
    zeilen = []
    for art, tabelle in (("Last", net.load), ("Generator", net.sgen)):
        for e in tabelle.itertuples():
            zeilen.append([e.name, art, busname(net, e.bus),
                           "ja" if e.in_service else "nein",
                           f"{e.p_mw * 1000:.2f}", f"{e.q_mvar * 1000:.2f}"])
    return md_tabelle(["Element", "Art", "Knoten", "in Betrieb", "P [kW]", "Q [kvar]"],
                      zeilen)


def md_ergebnisse(net, ebene):
    """Ergebnis-Tabellen eines berechneten Netzes."""
    h = "#" * ebene
    teile = []

    if len(net.load) or len(net.sgen):
        teile.append(f"{h} Lasten und Generatoren (eingestellt)\n\n" + md_einstellungen(net))

    teile.append(f"{h} Knotenspannungen\n\n" + md_tabelle(
        ["Knoten", "U [p.u.]", "U [V]", "Winkel [°]"],
        [[busname(net, b), f"{r.vm_pu:.4f}",
          f"{r.vm_pu * net.bus.at[b, 'vn_kv'] * 1000:.1f}", f"{r.va_degree:.3f}"]
         for b, r in net.res_bus.iterrows()]))

    teile.append(f"{h} Leitungen\n\n" + md_tabelle(
        ["von", "nach", "Länge [m]", "I [A]", "Auslastung [%]",
         "P_Verlust [kW]", "Q_Verlust [kvar]"],
        [[busname(net, l.from_bus), busname(net, l.to_bus), f"{l.length_km * 1000:.0f}",
          f"{r.i_ka * 1000:.1f}", f"{r.loading_percent:.1f}",
          f"{r.pl_mw * 1000:.3f}", f"{r.ql_mvar * 1000:.3f}"]
         for l, r in zip(net.line.itertuples(), net.res_line.itertuples())]))

    teile.append(f"{h} Externes Netz\n\n"
                 "Positive Werte: das externe Netz speist ein, negative: Rückspeisung.\n\n"
                 + md_tabelle(
                     ["Externes Netz", "Knoten", "U_soll [p.u.]", "P [kW]", "Q [kvar]"],
                     [[e.name, busname(net, e.bus), f"{e.vm_pu:.2f}",
                       f"{r.p_mw * 1000:.2f}", f"{r.q_mvar * 1000:.2f}"]
                      for e, r in zip(net.ext_grid.itertuples(),
                                      net.res_ext_grid.itertuples())]))
    return "\n\n".join(teile)


def uebersicht_zeile(titel, net, konvergiert):
    """Eine Zeile der Vergleichstabelle ueber alle Varianten."""
    if not konvergiert:
        return [titel] + ["–"] * (len(net.bus) + 3)
    return ([titel] + [f"{u:.4f}" for u in net.res_bus.vm_pu]
            + [f"{net.res_ext_grid.p_mw.sum() * 1000:.2f}",
               f"{net.res_ext_grid.q_mvar.sum() * 1000:.2f}",
               f"{net.res_line.loading_percent.max():.1f}"])


# ---------------------------------------------------------------------------
# Einlinienersatzschaltbild
# ---------------------------------------------------------------------------

def plot_netz(net, datei, titel=None):
    """Zeichnet einen Strang als Einlinienersatzschaltbild mit Ergebnissen."""
    # x-Position jedes Knotens = Leitungsentfernung zum Speiseknoten [km]
    x = {net.ext_grid.bus.iloc[0]: 0.0}
    offen = list(net.line.index)
    while offen:
        rest = []
        for i in offen:
            a, b = net.line.at[i, "from_bus"], net.line.at[i, "to_bus"]
            laenge = net.line.at[i, "length_km"]
            if a in x and b not in x:
                x[b] = x[a] + laenge
            elif b in x and a not in x:
                x[a] = x[b] + laenge
            elif not (a in x and b in x):
                rest.append(i)
        if len(rest) == len(offen):          # nicht angeschlossene Leitungen
            break
        offen = rest
    for n, b in enumerate(net.bus.index):    # Inselknoten ans Ende haengen
        x.setdefault(b, max(x.values()) + 0.1 * (n + 1))

    einheit = max(max(x.values()), 1e-9)
    halb = 0.06 * einheit                    # halbe Breite einer Sammelschiene
    hat_ergebnisse = not net.res_bus.empty

    fig, ax = plt.subplots(figsize=(11, 3.8))

    for i in net.line.index:
        a, b = net.line.at[i, "from_bus"], net.line.at[i, "to_bus"]
        ax.plot([x[a], x[b]], [0, 0], color="black", lw=1.2, zorder=1)
        text = f"{net.line.at[i, 'length_km'] * 1000:.0f} m"
        if hat_ergebnisse:
            text += f"\n{net.res_line.at[i, 'loading_percent']:.1f} %"
        ax.text((x[a] + x[b]) / 2, 0.06, text, ha="center", va="bottom", fontsize=9)

    for b in net.bus.index:
        ax.plot([x[b] - halb, x[b] + halb], [0, 0], color="black", lw=4,
                solid_capstyle="butt", zorder=2)
        text = busname(net, b)
        if hat_ergebnisse:
            u = net.res_bus.at[b, "vm_pu"]
            text += f"\n{u:.4f} p.u.\n{u * net.bus.at[b, 'vn_kv'] * 1000:.1f} V"
        ax.text(x[b], 0.42, text, ha="center", va="bottom", fontsize=9)

    for e in net.ext_grid.itertuples():
        xb = x[e.bus] - halb / 2
        ax.plot([xb, xb], [0, 0.22], color="black", lw=1.2)
        ax.add_patch(plt.Rectangle((xb - halb / 2, 0.22), halb, 0.16,
                                   facecolor="white", edgecolor="black", hatch="xxxx"))
        ax.text(xb - halb * 0.8, 0.30, e.name, ha="right", va="center", fontsize=9)

    # Lasten (Pfeil) und Generatoren (Kreis) nebeneinander unter dem Knoten
    am_knoten = list(net.load.bus) + list(net.sgen.bus)
    belegt = {}

    def platz(bus):
        n = belegt.get(bus, 0)
        belegt[bus] = n + 1
        return x[bus] + (n - (am_knoten.count(bus) - 1) / 2) * 0.085 * einheit

    for art, tabelle in (("last", net.load), ("gen", net.sgen)):
        for e in tabelle.itertuples():
            xb = platz(e.bus)
            farbe = "black" if e.in_service else "0.6"
            if art == "last":
                ax.annotate("", xy=(xb, -0.36), xytext=(xb, 0),
                            arrowprops=dict(arrowstyle="-|>", color=farbe, lw=1.2,
                                            mutation_scale=18))
            else:
                ax.plot([xb, xb], [0, -0.22], color=farbe, lw=1.2)
                ax.plot(xb, -0.29, marker="o", ms=16, mfc="white", mec=farbe, mew=1.2)
                ax.text(xb, -0.29, "G", ha="center", va="center", fontsize=8, color=farbe)
            ax.text(xb, -0.40, f"{e.name}\n{e.p_mw * 1000:g} kW\n{e.q_mvar * 1000:g} kvar"
                    + ("" if e.in_service else "\n(aus)"),
                    ha="center", va="top", fontsize=8, color=farbe)

    ax.text(0.5, 0.02, "Leitungstyp: " + ", ".join(net.line.std_type.unique()),
            transform=ax.transAxes, ha="center", va="bottom", fontsize=9, style="italic")
    ax.set_xlim(-0.22 * einheit, 1.12 * einheit)
    ax.set_ylim(-1.0, 0.95)
    ax.axis("off")
    if titel:
        ax.set_title(titel)
    fig.tight_layout()
    fig.savefig(datei, dpi=200)
    plt.close(fig)
    print(f"Netzplan gespeichert:   {datei}")


# ---------------------------------------------------------------------------
# Ablauf
# ---------------------------------------------------------------------------

def main():
    ordner = os.path.dirname(AUSGABE) or "."
    os.makedirs(ordner, exist_ok=True)
    stamm = os.path.splitext(os.path.basename(AUSGABE))[0]

    def bild(net, nummer, titel):
        """Zeichnet den Netzplan und gibt den Markdown-Verweis darauf zurueck."""
        name = f"{stamm}_netz.png" if nummer == 0 else f"{stamm}_variante{nummer}.png"
        plot_netz(net, os.path.join(ordner, name), titel)
        return f"![{titel}]({name})"

    # --- Ausgangsnetz ---
    net = baue_netz()
    if not berechne(net):
        pp.diagnostic(net)
        raise SystemExit("Lastfluss des Ausgangsnetzes konvergiert nicht - "
                         "Hinweise siehe Diagnose oben.")

    md = [f"# {TITEL}",
          "## Einlinienersatzschaltbild\n\n" + bild(net, 0, TITEL),
          "## Leitungstypen\n\n" + md_leitungstypen(net)]

    if not VARIANTEN:
        md.append(md_ergebnisse(net, ebene=2))
    else:
        uebersicht = [uebersicht_zeile("Ausgangsnetz", net, True)]
        abschnitte = ["## Ausgangsnetz\n\n" + md_ergebnisse(net, ebene=3)]

        for nummer, variante in enumerate(VARIANTEN, start=1):
            titel = variante["titel"]
            net_v = baue_netz()
            wende_variante_an(net_v, variante)
            konvergiert = berechne(net_v)
            uebersicht.append(uebersicht_zeile(titel, net_v, konvergiert))

            teil = [f"## Variante {nummer}: {titel}"]
            if variante.get("notiz"):
                teil.append(variante["notiz"])
            if not konvergiert:
                teil.append("**Lastfluss konvergiert nicht** – keine Ergebnisse.\n\n"
                            + md_einstellungen(net_v))
            else:
                if BILD_JE_VARIANTE:
                    teil.append(bild(net_v, nummer, titel))
                teil.append(md_ergebnisse(net_v, ebene=3))
            abschnitte.append("\n\n".join(teil))

        md.append("## Übersicht aller Varianten\n\n" + md_tabelle(
            ["Variante"] + [f"U {n} [p.u.]" for n in KNOTEN]
            + ["P ext. Netz [kW]", "Q ext. Netz [kvar]", "max. Auslastung [%]"],
            uebersicht))
        md += abschnitte

    with open(AUSGABE, "w", encoding="utf-8") as f:
        f.write("\n\n".join(md) + "\n")
    print(f"Ergebnisse geschrieben: {AUSGABE}")


if __name__ == "__main__":
    main()
