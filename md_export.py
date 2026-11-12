"""Hilfsfunktionen fuer das Labor EAN-V4: Netzplan zeichnen und
Lastfluss-Ergebnisse eines pandapower-Netzes als Markdown exportieren.

Verwendung (nach pp.runpp(net)):

    from md_export import plot_netz, export_ergebnisse

    plot_netz(net, "ergebnisse/aufgabe1_netz.png")
    export_ergebnisse(net, "ergebnisse/aufgabe1.md", titel="Aufgabe 1",
                      bild="ergebnisse/aufgabe1_netz.png")

Mit anhaengen=True wird an eine bestehende Datei angehaengt, so lassen sich
mehrere Varianten (Aufgabe 2) in einer Datei sammeln.
"""

import os

import matplotlib.pyplot as plt
import pandas as pd


# ---------------------------------------------------------------------------
# Markdown-Bausteine
# ---------------------------------------------------------------------------

def _zahl(wert, stellen):
    """Zahl mit fester Nachkommastellenzahl, alles andere als Text."""
    if isinstance(wert, bool):
        return "ja" if wert else "nein"
    if isinstance(wert, (int, float)):
        if pd.isna(wert):
            return "–"
        return f"{wert:.{stellen}f}"
    return str(wert)


def tabelle(df, stellen=3):
    """Wandelt ein DataFrame in eine Markdown-Tabelle um.

    stellen: Nachkommastellen, entweder eine Zahl fuer alle Spalten oder ein
             dict {Spaltenname: Stellen} (nicht genannte Spalten: 3).
    """
    zeilen = ["| " + " | ".join(str(s) for s in df.columns) + " |"]
    ausrichtung = []
    for spalte in df.columns:
        ist_zahl = pd.api.types.is_numeric_dtype(df[spalte]) and \
            not pd.api.types.is_bool_dtype(df[spalte])
        ausrichtung.append("---:" if ist_zahl else ":---")
    zeilen.append("| " + " | ".join(ausrichtung) + " |")

    for _, zeile in df.iterrows():
        zellen = []
        for spalte in df.columns:
            n = stellen.get(spalte, 3) if isinstance(stellen, dict) else stellen
            wert = zeile[spalte]
            if hasattr(wert, "item"):      # numpy-Typ -> Python-Typ
                wert = wert.item()
            zellen.append(_zahl(wert, n))
        zeilen.append("| " + " | ".join(zellen) + " |")
    return "\n".join(zeilen)


def _busname(net, bus):
    name = net.bus.at[bus, "name"]
    return str(name) if name not in (None, "") and not pd.isna(name) else f"Bus {bus}"


def _elementname(df, idx, praefix):
    name = df.at[idx, "name"]
    return str(name) if name not in (None, "") and not pd.isna(name) else f"{praefix} {idx}"


# ---------------------------------------------------------------------------
# Ergebnis-Tabellen (alle in kW / kvar / V / A, passend zur Niederspannung)
# ---------------------------------------------------------------------------

def knotenspannungen(net):
    return pd.DataFrame({
        "Knoten": [_busname(net, b) for b in net.bus.index],
        "U [p.u.]": net.res_bus.vm_pu.values,
        "U [V]": net.res_bus.vm_pu.values * net.bus.vn_kv.values * 1e3,
        "Winkel [°]": net.res_bus.va_degree.values,
    })


def leitungen(net):
    return pd.DataFrame({
        "Leitung": [_elementname(net.line, i, "Leitung") for i in net.line.index],
        "von": [_busname(net, b) for b in net.line.from_bus],
        "nach": [_busname(net, b) for b in net.line.to_bus],
        "Typ": net.line.std_type.values,
        "Länge [m]": net.line.length_km.values * 1e3,
        "I [A]": net.res_line.i_ka.values * 1e3,
        "Auslastung [%]": net.res_line.loading_percent.values,
        "P_Verlust [kW]": net.res_line.pl_mw.values * 1e3,
        "Q_Verlust [kvar]": net.res_line.ql_mvar.values * 1e3,
    })


def externes_netz(net):
    """Positive Werte = das externe Netz speist ins Netz ein."""
    return pd.DataFrame({
        "Externes Netz": [_elementname(net.ext_grid, i, "Ext. Netz")
                          for i in net.ext_grid.index],
        "Knoten": [_busname(net, b) for b in net.ext_grid.bus],
        "U_soll [p.u.]": net.ext_grid.vm_pu.values,
        "P [kW]": net.res_ext_grid.p_mw.values * 1e3,
        "Q [kvar]": net.res_ext_grid.q_mvar.values * 1e3,
    })


def _einspeiser_oder_last(net, element, praefix, spaltenname):
    df, res = net[element], net["res_" + element]
    return pd.DataFrame({
        spaltenname: [_elementname(df, i, praefix) for i in df.index],
        "Knoten": [_busname(net, b) for b in df.bus],
        "in Betrieb": df.in_service.values.astype(bool),
        "P [kW]": res.p_mw.values * 1e3,
        "Q [kvar]": res.q_mvar.values * 1e3,
    })


def lasten(net):
    """Positive Werte = Bezug aus dem Netz."""
    return _einspeiser_oder_last(net, "load", "Last", "Last")


def generatoren(net):
    """Static Generators. Positive Werte = Einspeisung ins Netz."""
    return _einspeiser_oder_last(net, "sgen", "Generator", "Generator")


def leitungstypen(net):
    """R', X' und das X/R-Verhaeltnis je verwendetem Leitungstyp."""
    df = net.line[["std_type", "r_ohm_per_km", "x_ohm_per_km", "max_i_ka"]]
    df = df.drop_duplicates().reset_index(drop=True)
    return pd.DataFrame({
        "Leitungstyp": df.std_type.values,
        "R' [Ω/km]": df.r_ohm_per_km.values,
        "X' [Ω/km]": df.x_ohm_per_km.values,
        "X/R": df.x_ohm_per_km.values / df.r_ohm_per_km.values,
        "I_max [A]": df.max_i_ka.values * 1e3,
    })


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def ergebnisse_als_markdown(net, titel, beschreibung="", bild=None, ebene=1,
                            mit_leitungstypen=True, bezugsordner="."):
    """Baut den Markdown-Text fuer ein berechnetes Netz und gibt ihn zurueck.

    ebene: Ueberschriftenebene des Titels (1 = '#', 2 = '##', ...).
    """
    if net.res_bus.empty:
        raise ValueError("Keine Ergebnisse vorhanden - zuerst pp.runpp(net) ausfuehren.")

    h, h2 = "#" * ebene, "#" * (ebene + 1)
    teile = [f"{h} {titel}"]
    if beschreibung:
        teile.append(beschreibung.strip())

    if bild:
        pfad = os.path.relpath(bild, bezugsordner).replace(os.sep, "/")
        teile.append(f"{h2} Einlinienersatzschaltbild\n\n![{titel}]({pfad})")

    teile.append(f"{h2} Knotenspannungen\n\n" + tabelle(
        knotenspannungen(net), {"U [p.u.]": 4, "U [V]": 1, "Winkel [°]": 3}))

    if len(net.line):
        teile.append(f"{h2} Leitungen\n\n" + tabelle(
            leitungen(net), {"Länge [m]": 0, "I [A]": 1, "Auslastung [%]": 1}))

    if len(net.ext_grid):
        teile.append(f"{h2} Externes Netz\n\n"
                     "Positive Werte: das externe Netz speist ein; "
                     "negative Werte: Rückspeisung.\n\n"
                     + tabelle(externes_netz(net), {"U_soll [p.u.]": 2, "P [kW]": 2,
                                                    "Q [kvar]": 2}))

    if len(net.load):
        teile.append(f"{h2} Lasten\n\n" + tabelle(lasten(net), 2))

    if len(net.sgen):
        teile.append(f"{h2} Generatoren\n\n"
                     "Positive Werte: Einspeisung ins Netz.\n\n"
                     + tabelle(generatoren(net), 2))

    if mit_leitungstypen and len(net.line):
        teile.append(f"{h2} Leitungstypen\n\n" + tabelle(
            leitungstypen(net), {"X/R": 3, "I_max [A]": 0}))

    return "\n\n".join(teile) + "\n"


def export_ergebnisse(net, datei, titel, beschreibung="", bild=None,
                      anhaengen=False, ebene=1, mit_leitungstypen=True):
    """Schreibt die Ergebnisse von net in die Markdown-Datei `datei`.

    net:          pandapower-Netz, fuer das pp.runpp(net) bereits gelaufen ist
    datei:        Zieldatei, z.B. "ergebnisse/aufgabe1.md"
    titel:        Ueberschrift des Abschnitts
    beschreibung: optionaler Freitext (z.B. Beobachtungen) unter der Ueberschrift
    bild:         optionaler Pfad zu einem Bild (z.B. von plot_netz)
    anhaengen:    True = an bestehende Datei anhaengen statt ueberschreiben
    ebene:        Ueberschriftenebene (z.B. 2 fuer Varianten innerhalb einer Datei)
    """
    ordner = os.path.dirname(datei) or "."
    os.makedirs(ordner, exist_ok=True)
    text = ergebnisse_als_markdown(net, titel, beschreibung, bild, ebene,
                                   mit_leitungstypen, bezugsordner=ordner)
    anhaengen = anhaengen and os.path.exists(datei)
    with open(datei, "a" if anhaengen else "w", encoding="utf-8") as f:
        if anhaengen:
            f.write("\n---\n\n")
        f.write(text)
    print(f"Ergebnisse geschrieben: {datei}")
    return datei


# ---------------------------------------------------------------------------
# Einlinienersatzschaltbild
# ---------------------------------------------------------------------------

def plot_netz(net, datei=None, titel=None, anzeigen=False):
    """Zeichnet einen Strang als Einlinienersatzschaltbild.

    Die Knoten werden entsprechend ihrer Leitungslaenge ab dem externen Netz
    von links nach rechts angeordnet. Liegen Ergebnisse vor, werden Spannungen
    und Leitungsauslastungen mit eingetragen.
    """
    hat_ergebnisse = not net.res_bus.empty

    # x-Position jedes Knotens = Leitungsentfernung zum Speiseknoten [km]
    start = net.ext_grid.bus.iloc[0] if len(net.ext_grid) else net.bus.index[0]
    x = {start: 0.0}
    offen = list(net.line.index)
    while offen:
        rest = []
        for i in offen:
            a, b, laenge = net.line.at[i, "from_bus"], net.line.at[i, "to_bus"], \
                net.line.at[i, "length_km"]
            if a in x and b not in x:
                x[b] = x[a] + laenge
            elif b in x and a not in x:
                x[a] = x[b] + laenge
            elif not (a in x and b in x):
                rest.append(i)
        if len(rest) == len(offen):     # nicht verbundene Leitungen
            break
        offen = rest
    for n, b in enumerate(net.bus.index):   # Inselknoten ans Ende haengen
        x.setdefault(b, max(x.values()) + 0.1 * (n + 1))

    einheit = max(max(x.values()), 1e-9)
    halb = 0.06 * einheit               # halbe Breite eines Sammelschienen-Strichs

    fig, ax = plt.subplots(figsize=(11, 3.8))

    for i in net.line.index:
        a, b = net.line.at[i, "from_bus"], net.line.at[i, "to_bus"]
        ax.plot([x[a], x[b]], [0, 0], color="black", lw=1.2, zorder=1)
        text = f"{net.line.at[i, 'length_km'] * 1e3:.0f} m"
        if hat_ergebnisse:
            text += f"\n{net.res_line.at[i, 'loading_percent']:.1f} %"
        ax.text((x[a] + x[b]) / 2, 0.06, text, ha="center", va="bottom", fontsize=9)

    for b in net.bus.index:
        ax.plot([x[b] - halb, x[b] + halb], [0, 0], color="black", lw=4,
                solid_capstyle="butt", zorder=2)
        text = _busname(net, b)
        if hat_ergebnisse:
            text += (f"\n{net.res_bus.at[b, 'vm_pu']:.4f} p.u."
                     f"\n{net.res_bus.at[b, 'vm_pu'] * net.bus.at[b, 'vn_kv'] * 1e3:.1f} V")
        ax.text(x[b], 0.42, text, ha="center", va="bottom", fontsize=9)

    for i in net.ext_grid.index:
        xb = x[net.ext_grid.at[i, "bus"]] - halb / 2
        ax.plot([xb, xb], [0, 0.22], color="black", lw=1.2)
        ax.add_patch(plt.Rectangle((xb - halb / 2, 0.22), halb, 0.16, fill=True,
                                   facecolor="white", edgecolor="black", hatch="xxxx"))
        ax.text(xb - halb * 0.8, 0.30, _elementname(net.ext_grid, i, "Netz"),
                ha="right", va="center", fontsize=9)

    # Lasten (Pfeil nach unten) und Generatoren (Kreis) unter den Knoten,
    # mehrere Elemente am selben Knoten nebeneinander
    anzahl = (list(net.load.bus) + list(net.sgen.bus))
    belegt = {}
    abstand = 0.085 * einheit

    def _platz(bus):
        n = belegt.get(bus, 0)
        belegt[bus] = n + 1
        return x[bus] + (n - (anzahl.count(bus) - 1) / 2) * abstand

    for i in net.load.index:
        xb = _platz(net.load.at[i, "bus"])
        an = bool(net.load.at[i, "in_service"])
        farbe = "black" if an else "0.6"
        ax.annotate("", xy=(xb, -0.36), xytext=(xb, 0),
                    arrowprops=dict(arrowstyle="-|>", color=farbe, lw=1.2,
                                    mutation_scale=18))
        ax.text(xb, -0.40, f"{_elementname(net.load, i, 'Last')}\n"
                f"{net.load.at[i, 'p_mw'] * 1e3:g} kW\n"
                f"{net.load.at[i, 'q_mvar'] * 1e3:g} kvar" + ("" if an else "\n(aus)"),
                ha="center", va="top", fontsize=8, color=farbe)

    for i in net.sgen.index:
        xb = _platz(net.sgen.at[i, "bus"])
        an = bool(net.sgen.at[i, "in_service"])
        farbe = "black" if an else "0.6"
        ax.plot([xb, xb], [0, -0.22], color=farbe, lw=1.2)
        ax.plot(xb, -0.29, marker="o", ms=16, mfc="white", mec=farbe, mew=1.2)
        ax.text(xb, -0.29, "G", ha="center", va="center", fontsize=8, color=farbe)
        ax.text(xb, -0.40, f"{_elementname(net.sgen, i, 'Generator')}\n"
                f"{net.sgen.at[i, 'p_mw'] * 1e3:g} kW\n"
                f"{net.sgen.at[i, 'q_mvar'] * 1e3:g} kvar" + ("" if an else "\n(aus)"),
                ha="center", va="top", fontsize=8, color=farbe)

    typen = ", ".join(str(t) for t in net.line.std_type.dropna().unique())
    if typen:
        ax.text(0.5, 0.02, f"Leitungstyp: {typen}", transform=ax.transAxes,
                ha="center", va="bottom", fontsize=9, style="italic")

    ax.set_xlim(-0.22 * einheit, 1.12 * einheit)
    ax.set_ylim(-1.0, 0.95)
    ax.axis("off")
    if titel:
        ax.set_title(titel)
    fig.tight_layout()

    if datei:
        os.makedirs(os.path.dirname(datei) or ".", exist_ok=True)
        fig.savefig(datei, dpi=200)
        print(f"Netzplan gespeichert: {datei}")
    if anzeigen:
        plt.show()
    else:
        plt.close(fig)
    return datei
