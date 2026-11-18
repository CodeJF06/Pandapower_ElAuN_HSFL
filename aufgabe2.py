"""Labor EAN-V4, Aufgabe 2: Erweiterung des Netzmodells.

Oben in NETZDATEN steht das Netz mit ALLEN Elementen, die in Aufgabe 2
vorkommen (nicht benoetigte zunaechst mit "an": False). In ABSCHNITTE steht
pro Teilaufgabe, was eingestellt wird. Beim Ausfuehren (F5) wird jede Variante
berechnet und alles in eine Markdown-Datei mit Bildern geschrieben.
"""

# ===========================================================================
# NETZDATEN  -  nur hier aendern
# ===========================================================================

TITEL = "Aufgabe 2: Erweiterung des Netzmodells"
AUSGABE = "ergebnisse/aufgabe2.md"       # Bilder landen im selben Ordner

NENNSPANNUNG_KV = 0.4
LEITUNGSTYP = "NAYY 4x120 SE"

KNOTEN = ["Knoten 1", "Knoten 2", "Knoten 3", "Knoten 4"]

EXTERNES_NETZ = {"name": "Vorgelagertes Netz", "knoten": "Knoten 1", "u_pu": 1.05}

# (von, nach, Laenge in m)  -  optional als 4. Wert ein anderer Leitungstyp
LEITUNGEN = [
    ("Knoten 1", "Knoten 2", 150),
    ("Knoten 2", "Knoten 3", 150),
    ("Knoten 3", "Knoten 4", 150),
]

# Lasten: q_kvar > 0 = induktive Last
LASTEN = [
    {"name": "V1", "knoten": "Knoten 4", "p_kw": 40, "q_kvar": 15},
    {"name": "V2", "knoten": "Knoten 2", "p_kw": 20, "q_kvar": 5, "an": False},
    {"name": "V3", "knoten": "Knoten 3", "p_kw": 20, "q_kvar": 5, "an": False},
]

# Static Generators: p_kw > 0 = Einspeisung
# q_kvar < 0: Generator nimmt Blindleistung auf (induktiv, untererregt)
# q_kvar > 0: Generator gibt Blindleistung ab (kapazitiv, uebererregt)
GENERATOREN = [
    {"name": "G4", "knoten": "Knoten 4", "p_kw": 0, "q_kvar": 0, "an": False},
    {"name": "G2", "knoten": "Knoten 2", "p_kw": 30, "q_kvar": 0, "an": False},
]

# ---------------------------------------------------------------------------
# Teilaufgaben
#
# Jede Variante startet vom Netz oben. Zuerst wird "einstellung" des
# Abschnitts angewendet, danach die Aenderungen der Variante.
# Aenderungen: {"Elementname": {"p_kw": .., "q_kvar": .., "an": True/False}}
# "notiz": eigener Text (Beobachtungen), erscheint unter der Teilaufgabe.
# "kompensation": sucht automatisch das kleinste gemeinsame Verhaeltnis Q/P
#    (induktiv) der genannten Generatoren, bei dem keine Knotenspannung ueber
#    ziel_u_pu liegt.
# ---------------------------------------------------------------------------

LAST_AUS_GEN_AN = {"V1": {"an": False}, "G4": {"an": True}}
LASTEN_2_3 = {"V1": {"an": False}, "V2": {"an": True}, "V3": {"an": True}}
ZWEI_GENERATOREN = {**LASTEN_2_3, "G4": {"an": True, "p_kw": 30}, "G2": {"an": True}}

ABSCHNITTE = [
    {
        "titel": "2.1 Leistung der Last an Knoten 4",
        "einstellung": {},
        "varianten": [
            {"titel": "Ausgangszustand"},
            {"titel": "P halbiert", "V1": {"p_kw": 20}},
            {"titel": "P verdoppelt", "V1": {"p_kw": 80}},
            {"titel": "Q halbiert", "V1": {"q_kvar": 7.5}},
            {"titel": "Q verdoppelt", "V1": {"q_kvar": 30}},
        ],
        "notiz": (
            "**Erwartung:** Mehr Leistung bedeutet mehr Strom und damit einen größeren "
            "Spannungsfall (ΔU ≈ (R·P + X·Q) / U).\n\n"
            "**Beobachtung:** Der Spannungsfall bis Knoten 4 liegt im Ausgangszustand bei "
            "0,028 p.u. Halbe Wirkleistung verringert ihn auf 0,016 p.u., doppelte "
            "vergrößert ihn auf 0,054 p.u. (Knoten 4 sinkt auf 0,996 p.u.). Halbe bzw. "
            "doppelte Blindleistung ändert ihn nur auf 0,026 bzw. 0,032 p.u. Die "
            "Wirkleistung wirkt also deutlich stärker, weil beim Kabel R' größer ist "
            "als X' (X/R = 0,36). Die Auslastung steigt mit der Scheinleistung "
            "(P doppelt: 48,8 %, Q doppelt: 29,3 %). Das externe Netz liefert die Last "
            "plus die Leitungsverluste (Ausgangszustand 41,11 kW, d. h. 1,11 kW Verluste)."
        ),
    },
    {
        "titel": "2.2 Generator an Knoten 4 (Wirkleistung)",
        "einstellung": LAST_AUS_GEN_AN,
        "varianten": [
            {"titel": "P = 10 kW", "G4": {"p_kw": 10}},
            {"titel": "P = 20 kW", "G4": {"p_kw": 20}},
            {"titel": "P = 40 kW", "G4": {"p_kw": 40}},
            {"titel": "P = 50 kW", "G4": {"p_kw": 50}},
            {"titel": "P = 0 kW", "G4": {"p_kw": 0}},
        ],
        "notiz": (
            "**Beobachtung:** Mit Einspeisung kehrt sich der Leistungsfluss um: Die "
            "Spannung steigt vom Speiseknoten zum Generator hin an, etwa proportional "
            "zur Wirkleistung (50 kW: Knoten 4 bei 1,079 p.u., +0,029 p.u.). Der "
            "Speiseknoten bleibt als Slack fest bei 1,05 p.u. Das externe Netz nimmt "
            "die Leistung auf (negatives P), um die Verluste weniger als eingespeist "
            "(50 kW → 48,64 kW, 1,36 kW Verluste), und liefert die geringe Blindleistung "
            "der Leitungen. Bei P = 0 kW ist das Netz unbelastet, alle Knoten liegen "
            "bei 1,05 p.u."
        ),
    },
    {
        "titel": "2.3 Generator an Knoten 4 (Blindleistung, P = 0)",
        "einstellung": LAST_AUS_GEN_AN,
        "varianten": [
            {"titel": "25 kvar induktiv", "G4": {"q_kvar": -25}},
            {"titel": "50 kvar induktiv", "G4": {"q_kvar": -50}},
            {"titel": "25 kvar kapazitiv", "G4": {"q_kvar": 25}},
            {"titel": "50 kvar kapazitiv", "G4": {"q_kvar": 50}},
        ],
        "notiz": (
            "**Beobachtung:** Induktive Blindleistung (Aufnahme) senkt die Spannung am "
            "Generator, kapazitive (Abgabe) hebt sie an: 50 kvar induktiv −0,011 p.u., "
            "50 kvar kapazitiv +0,010 p.u. Im Vergleich zu 50 kW Wirkleistung "
            "(+0,029 p.u.) wirkt Blindleistung nur etwa ein Drittel so stark (X/R = 0,36). "
            "Die Blindleistung wird vollständig vom externen Netz geliefert bzw. "
            "aufgenommen, die Wirkleistung am Speiseknoten entspricht nur den Verlusten "
            "(ca. 1,4 kW). Obwohl keine Wirkleistung übertragen wird, sind die Leitungen "
            "zu etwa 28 % ausgelastet, weil der Blindstrom sie ebenfalls belastet."
        ),
    },
    {
        "titel": "2.4 Weitere Lasten an Knoten 2 und 3 (Generator aus)",
        "einstellung": LASTEN_2_3,
        "varianten": [
            {"titel": "V2 und V3"},
            {"titel": "V2 und V3, zusätzlich V1", "V1": {"an": True}},
        ],
        "notiz": (
            "**Beobachtung:** Die Spannung fällt vom Speiseknoten zum Strangende "
            "monoton ab. Der Spannungsfall je Abschnitt wird nach hinten kleiner, weil "
            "hinter jeder Last weniger Strom fließt: Mit V2 und V3 0,0088 / 0,0045 / "
            "0 p.u. (hinter Knoten 3 fließt kein Strom mehr, Knoten 3 und 4 haben "
            "dieselbe Spannung). Mit zusätzlich V1 0,0185 / 0,0140 / 0,0094 p.u., "
            "insgesamt 0,042 p.u. (ca. 4 %)."
        ),
    },
    {
        "titel": "2.5 Generatoren an Knoten 2 und 4 mit je 30 kW",
        "einstellung": ZWEI_GENERATOREN,
        "varianten": [
            {"titel": "ohne Generatoren (wie 2.4)", "G2": {"an": False}, "G4": {"an": False}},
            {"titel": "G2 und G4 je 30 kW"},
        ],
        "notiz": (
            "**Beobachtung:** Mit 60 kW Erzeugung bei 40 kW Last wird ins vorgelagerte "
            "Netz zurückgespeist (19,71 kW). Alle Knotenspannungen liegen jetzt über der "
            "Speisespannung und steigen zum Strangende hin an (Knoten 4: 1,061 p.u., "
            "gegenüber 2.4 um 0,024 p.u. höher). Die Auslastung sinkt von 23,7 % auf "
            "16,9 %, weil ein Großteil der Last lokal gedeckt wird."
        ),
    },
    {
        "titel": "2.6 Kompensation durch induktive Blindleistung",
        "einstellung": ZWEI_GENERATOREN,
        "varianten": [
            {"titel": f"Q = {'−' if q else ''}{q} kvar je Generator",
             "G2": {"q_kvar": -q}, "G4": {"q_kvar": -q}}
            for q in (0, 10, 20, 30, 40)
        ],
        "kompensation": {"generatoren": ["G2", "G4"], "ziel_u_pu": 1.05},
        "notiz": (
            "**Beobachtung:** Die Spannungserhöhung lässt sich kompensieren. Dafür muss "
            "jeder Generator etwa 1,22 kvar pro kW induktiv aufnehmen, also je 36,6 kvar "
            "(zusammen 73,2 kvar, cos φ ≈ 0,63 untererregt). Weil das Kabel einen "
            "kleinen X/R-Wert hat, ist dafür sehr viel Blindleistung nötig. Nachteile: "
            "Das externe Netz muss rund 84 kvar liefern, die Auslastung steigt von "
            "16,9 % auf 48,8 % und die Verluste von 0,29 kW auf 2,19 kW. In der Praxis "
            "ist ein so kleiner cos φ unüblich; in Niederspannungsnetzen ist "
            "Blindleistung deshalb nur begrenzt wirksam."
        ),
    },
]

BILD_JE_VARIANTE = False     # True: zusaetzlich ein Netzplan pro Variante
DETAILTABELLEN = False       # True: alle Tabellen je Variante im Anhang

# ===========================================================================
# Ab hier muss nichts mehr geaendert werden
# ===========================================================================

import math
import os

import matplotlib.pyplot as plt
import pandapower as pp


# ---------------------------------------------------------------------------
# Netz aufbauen, aendern, berechnen
# ---------------------------------------------------------------------------

def baue_netz():
    """Erstellt das pandapower-Netz aus den NETZDATEN."""
    net = pp.create_empty_network(name=TITEL)

    bus = {name: pp.create_bus(net, vn_kv=NENNSPANNUNG_KV, name=name) for name in KNOTEN}

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


def element(net, name):
    """Gibt (Tabelle, Index, Art) eines Elements anhand seines Namens zurueck."""
    for art, tabelle in (("Last", net.load), ("Generator", net.sgen)):
        treffer = tabelle.index[tabelle.name == name]
        if len(treffer):
            return tabelle, treffer[0], art
    raise ValueError(f"Keine Last und kein Generator mit dem Namen '{name}'")


def aendere(net, aenderungen, wo):
    """Uebernimmt {"Name": {"p_kw":.., "q_kvar":.., "an":..}} in das Netz."""
    for name, aenderung in aenderungen.items():
        if name in ("titel", "notiz"):
            continue
        tabelle, i, _ = element(net, name)
        for schluessel, wert in aenderung.items():
            if schluessel == "p_kw":
                tabelle.at[i, "p_mw"] = wert / 1000
            elif schluessel == "q_kvar":
                tabelle.at[i, "q_mvar"] = wert / 1000
            elif schluessel == "an":
                tabelle.at[i, "in_service"] = bool(wert)
            else:
                raise ValueError(f"{wo}: '{schluessel}' ist nicht erlaubt "
                                 "(nur p_kw, q_kvar, an)")


def berechne(net):
    """Lastflussberechnung. Gibt False zurueck, wenn sie nicht konvergiert."""
    try:
        pp.runpp(net, numba=False)
        return True
    except pp.auxiliary.LoadflowNotConverged:
        return False


def netz_fuer(abschnitt, variante=None):
    """Netz im Zustand von Abschnitt (+ Variante), noch nicht berechnet."""
    net = baue_netz()
    aendere(net, abschnitt.get("einstellung", {}), abschnitt["titel"])
    if variante:
        aendere(net, variante, f"{abschnitt['titel']} / {variante['titel']}")
    return net


def suche_kompensation(abschnitt):
    """Kleinstes Q/P (induktiv, fuer alle genannten Generatoren gleich), bei dem
    die hoechste Knotenspannung <= ziel_u_pu ist. Gibt (k, net) oder (None, net)."""
    komp = abschnitt["kompensation"]
    ziel = komp["ziel_u_pu"]

    def netz_mit(k):
        net = netz_fuer(abschnitt)
        for name in komp["generatoren"]:
            tabelle, i, _ = element(net, name)
            tabelle.at[i, "q_mvar"] = -k * tabelle.at[i, "p_mw"]
        return net, berechne(net)

    def erfuellt(k):
        net, ok = netz_mit(k)
        return ok and net.res_bus.vm_pu.max() <= ziel + 1e-6, net

    passt, net = erfuellt(0.0)
    if passt:
        return 0.0, net
    unten, oben = 0.0, 10.0
    passt, net = erfuellt(oben)
    if not passt:
        return None, net
    for _ in range(40):                      # Bisektion
        mitte = (unten + oben) / 2
        if erfuellt(mitte)[0]:
            oben = mitte
        else:
            unten = mitte
    return oben, netz_mit(oben)[0]


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------

def md_tabelle(kopf, zeilen):
    """kopf: Spaltennamen, zeilen: Liste von Zeilen (bereits formatierter Text)."""
    def ist_zahl(text):
        if text == "–":
            return True
        try:
            float(text.replace("−", "-"))
            return True
        except ValueError:
            return False

    zeilen = [[str(z) for z in zeile] for zeile in zeilen]
    rechts = [bool(zeilen) and all(ist_zahl(z[i]) for z in zeilen) for i in range(len(kopf))]
    text = ["| " + " | ".join(kopf) + " |",
            "| " + " | ".join("---:" if r else ":---" for r in rechts) + " |"]
    text += ["| " + " | ".join(zeile) + " |" for zeile in zeilen]
    return "\n".join(text)


def zahl(wert, stellen=2):
    """Zahl mit echtem Minuszeichen, -0 wird zu 0."""
    text = f"{wert:.{stellen}f}"
    if float(text) == 0:
        text = text.lstrip("-")
    return text.replace("-", "−")


def busname(net, bus):
    return net.bus.at[bus, "name"]


def beschreibe(net, aenderungen):
    """Kurzer Text zu den Einstellungen, z.B. 'G4: P = 10 kW; V1: aus'."""
    teile = []
    for name, aenderung in aenderungen.items():
        if name in ("titel", "notiz"):
            continue
        _, _, art = element(net, name)
        werte = []
        for schluessel, wert in aenderung.items():
            if schluessel == "an":
                werte.append("an" if wert else "aus")
            elif schluessel == "p_kw":
                werte.append(f"P = {zahl(wert, 1).rstrip('0').rstrip('.')} kW")
            elif schluessel == "q_kvar":
                text = f"Q = {zahl(wert, 1).rstrip('0').rstrip('.')} kvar"
                if art == "Generator" and wert:
                    text += " (induktiv)" if wert < 0 else " (kapazitiv)"
                werte.append(text)
        teile.append(f"{name}: " + ", ".join(werte))
    return "; ".join(teile) if teile else "–"


def md_einstellungen(net):
    """Eingestellte Leistungen aller Lasten und Generatoren."""
    zeilen = []
    for art, tabelle in (("Last", net.load), ("Generator", net.sgen)):
        for e in tabelle.itertuples():
            zeilen.append([e.name, art, busname(net, e.bus), "ja" if e.in_service else "nein",
                           zahl(e.p_mw * 1000), zahl(e.q_mvar * 1000)])
    return md_tabelle(["Element", "Art", "Knoten", "in Betrieb", "P [kW]", "Q [kvar]"], zeilen)


def md_leitungstypen(net):
    typen = net.line.drop_duplicates("std_type")
    return md_tabelle(
        ["Leitungstyp", "R' [Ω/km]", "X' [Ω/km]", "X/R", "I_max [A]"],
        [[t.std_type, f"{t.r_ohm_per_km:.3f}", f"{t.x_ohm_per_km:.3f}",
          f"{t.x_ohm_per_km / t.r_ohm_per_km:.3f}", f"{t.max_i_ka * 1000:.0f}"]
         for t in typen.itertuples()])


def md_ergebnisse(net, ebene):
    """Alle Ergebnis-Tabellen eines berechneten Netzes."""
    h = "#" * ebene
    teile = [f"{h} Lasten und Generatoren (eingestellt)\n\n" + md_einstellungen(net)]
    teile.append(f"{h} Knotenspannungen\n\n" + md_tabelle(
        ["Knoten", "U [p.u.]", "U [V]", "Winkel [°]"],
        [[busname(net, b), f"{r.vm_pu:.4f}",
          f"{r.vm_pu * net.bus.at[b, 'vn_kv'] * 1000:.1f}", zahl(r.va_degree, 3)]
         for b, r in net.res_bus.iterrows()]))
    teile.append(f"{h} Leitungen\n\n" + md_tabelle(
        ["von", "nach", "Länge [m]", "I [A]", "Auslastung [%]", "P_Verlust [kW]",
         "Q_Verlust [kvar]"],
        [[busname(net, l.from_bus), busname(net, l.to_bus), f"{l.length_km * 1000:.0f}",
          f"{r.i_ka * 1000:.1f}", f"{r.loading_percent:.1f}",
          zahl(r.pl_mw * 1000, 3), zahl(r.ql_mvar * 1000, 3)]
         for l, r in zip(net.line.itertuples(), net.res_line.itertuples())]))
    teile.append(f"{h} Externes Netz\n\n" + md_tabelle(
        ["Externes Netz", "Knoten", "P [kW]", "Q [kvar]"],
        [[e.name, busname(net, e.bus), zahl(r.p_mw * 1000), zahl(r.q_mvar * 1000)]
         for e, r in zip(net.ext_grid.itertuples(), net.res_ext_grid.itertuples())]))
    return "\n\n".join(teile)


UEBERSICHT_KOPF = (["Variante", "Einstellung"] + [f"U {k} [p.u.]" for k in KNOTEN]
                   + ["P ext. Netz [kW]", "Q ext. Netz [kvar]", "max. Auslastung [%]"])


def uebersicht_zeile(titel, einstellung, net, konvergiert):
    if not konvergiert:
        return [titel, einstellung] + ["–"] * (len(KNOTEN) + 3)
    return ([titel, einstellung] + [f"{u:.4f}" for u in net.res_bus.vm_pu]
            + [zahl(net.res_ext_grid.p_mw.sum() * 1000),
               zahl(net.res_ext_grid.q_mvar.sum() * 1000),
               f"{net.res_line.loading_percent.max():.1f}"])


# ---------------------------------------------------------------------------
# Bilder
# ---------------------------------------------------------------------------

# Feste Farbreihenfolge fuer Linien (farbfehlsichtigkeits-geprueft)
FARBEN = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100",
          "#e87ba4", "#008300", "#6250d6", "#e34948"]


def entfernungen(net):
    """Leitungsentfernung jedes Knotens zum Speiseknoten in km."""
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
        if len(rest) == len(offen):
            break
        offen = rest
    for n, b in enumerate(net.bus.index):
        x.setdefault(b, max(x.values()) + 0.1 * (n + 1))
    return x


def plot_spannungsprofil(kurven, datei, titel):
    """kurven: Liste (Name, berechnetes Netz). Spannung ueber der Entfernung."""
    fig, ax = plt.subplots(figsize=(9, 4.2))
    for nr, (name, net) in enumerate(kurven):
        x = entfernungen(net)
        busse = sorted(net.bus.index, key=lambda b: x[b])
        farbe = (FARBEN[nr] if len(kurven) <= len(FARBEN)
                 else plt.cm.Blues(0.35 + 0.6 * nr / (len(kurven) - 1)))
        ax.plot([x[b] * 1000 for b in busse], [net.res_bus.at[b, "vm_pu"] for b in busse],
                color=farbe, lw=2, marker="o", ms=6, label=name)

    net = kurven[0][1]
    x = entfernungen(net)
    ax.axhline(EXTERNES_NETZ["u_pu"], color="0.55", lw=1, ls="--", zorder=0)
    ax.set_xticks([x[b] * 1000 for b in net.bus.index])
    ax.set_xticklabels([f"{busname(net, b)}\n{x[b] * 1000:.0f} m" for b in net.bus.index],
                       fontsize=9)
    ax.set_ylabel("Spannung [p.u.]")
    ax.set_title(titel, fontsize=11)
    ax.grid(axis="y", color="0.9")
    for seite in ("top", "right"):
        ax.spines[seite].set_visible(False)
    ax.legend(loc="center left", bbox_to_anchor=(1.01, 0.5), frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(datei, dpi=200)
    plt.close(fig)
    print(f"Bild gespeichert:       {datei}")


def plot_netz(net, datei, titel=None):
    """Zeichnet einen Strang als Einlinienersatzschaltbild mit Ergebnissen."""
    x = entfernungen(net)
    einheit = max(max(x.values()), 1e-9)
    halb = 0.06 * einheit
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
    print(f"Bild gespeichert:       {datei}")


# ---------------------------------------------------------------------------
# Ablauf
# ---------------------------------------------------------------------------

def main():
    # Pfade gelten relativ zum Ordner dieser Datei, egal von wo gestartet wird
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    ordner = os.path.dirname(AUSGABE) or "."
    os.makedirs(ordner, exist_ok=True)
    stamm = os.path.splitext(os.path.basename(AUSGABE))[0]

    # Ausgangsnetz mit allen Elementen (ausgeschaltete grau)
    net = baue_netz()
    if not berechne(net):
        pp.diagnostic(net)
        raise SystemExit("Lastfluss des Ausgangsnetzes konvergiert nicht - siehe Diagnose.")
    plot_netz(net, os.path.join(ordner, f"{stamm}_netz.png"), "Ausgangsnetz mit allen Elementen")

    md = [f"# {TITEL}",
          "## Netzmodell\n\nAlle in Aufgabe 2 verwendeten Elemente; ausgeschaltete sind grau "
          "dargestellt. Spannungen und Auslastungen gelten für den Ausgangszustand.\n\n"
          f"![Ausgangsnetz]({stamm}_netz.png)",
          "### Leitungstypen\n\n" + md_leitungstypen(net),
          "### Elemente im Ausgangszustand\n\n" + md_einstellungen(net),
          "### Vorzeichen\n\n"
          "- Lasten: P, Q > 0 = Bezug (Q > 0 induktiv).\n"
          "- Generatoren: P > 0 = Einspeisung; Q < 0 = Aufnahme von Blindleistung "
          "(induktiv), Q > 0 = Abgabe (kapazitiv).\n"
          "- Externes Netz: P, Q > 0 = Bezug aus dem vorgelagerten Netz, < 0 = Rückspeisung."]
    anhang = []

    for nr_a, abschnitt in enumerate(ABSCHNITTE, start=1):
        print(f"\n--- {abschnitt['titel']} ---")
        teil = [f"## {abschnitt['titel']}"]
        if abschnitt.get("einstellung"):
            teil.append("Gemeinsame Einstellung: "
                        + beschreibe(net, abschnitt["einstellung"]))

        zeilen, kurven = [], []
        for nr_v, variante in enumerate(abschnitt["varianten"], start=1):
            net_v = netz_fuer(abschnitt, variante)
            ok = berechne(net_v)
            zeilen.append(uebersicht_zeile(variante["titel"], beschreibe(net_v, variante),
                                           net_v, ok))
            if not ok:
                print(f"  {variante['titel']}: Lastfluss konvergiert nicht")
                continue
            kurven.append((variante["titel"], net_v))
            if BILD_JE_VARIANTE:
                name = f"{stamm}_{nr_a}_{nr_v}.png"
                plot_netz(net_v, os.path.join(ordner, name),
                          f"{abschnitt['titel']}: {variante['titel']}")
                anhang.append(f"![{variante['titel']}]({name})")
            if DETAILTABELLEN:
                anhang.append(f"### {abschnitt['titel']}: {variante['titel']}\n\n"
                              + md_ergebnisse(net_v, ebene=4))

        komp_text = None
        if "kompensation" in abschnitt:
            komp = abschnitt["kompensation"]
            k, net_k = suche_kompensation(abschnitt)
            if k is None:
                komp_text = (f"**Kompensation:** Auch mit Q/P = 10 bleibt mindestens eine "
                             f"Knotenspannung über {komp['ziel_u_pu']} p.u.")
            else:
                einstellung = {}
                for name in komp["generatoren"]:
                    tabelle, i, _ = element(net_k, name)
                    einstellung[name] = {"q_kvar": tabelle.at[i, "q_mvar"] * 1000}
                titel = "benötigte Kompensation"
                zeilen.append(uebersicht_zeile(f"**{titel}**", beschreibe(net_k, einstellung),
                                               net_k, True))
                kurven.append((titel, net_k))
                cos_phi = 1 / math.sqrt(1 + k ** 2)
                q_summe = sum(abs(e["q_kvar"]) for e in einstellung.values())
                komp_text = (
                    f"**Kompensation:** Damit keine Knotenspannung über "
                    f"{komp['ziel_u_pu']} p.u. liegt, müssen "
                    f"{', '.join(komp['generatoren'])} je **{k:.2f} kvar pro kW** "
                    f"induktive Blindleistung aufnehmen (|Q|/P = {k:.2f}, "
                    f"cos φ = {cos_phi:.3f} untererregt), zusammen {q_summe:.1f} kvar. "
                    + ", ".join(f"{n}: {zahl(e['q_kvar'], 1)} kvar"
                                for n, e in einstellung.items()) + ".")
                print(f"  Kompensation: Q/P = {k:.3f}")

        teil.append(md_tabelle(UEBERSICHT_KOPF, zeilen))
        if komp_text:
            teil.append(komp_text)
        if kurven:
            name = f"{stamm}_profil_{nr_a}.png"
            plot_spannungsprofil(kurven, os.path.join(ordner, name),
                                 f"Spannungsprofil – {abschnitt['titel']}")
            teil.append(f"![Spannungsprofil {abschnitt['titel']}]({name})")
        if abschnitt.get("notiz"):
            teil.append(abschnitt["notiz"])
        md.append("\n\n".join(teil))

    if anhang:
        md.append("## Anhang: Ergebnisse je Variante\n\n" + "\n\n".join(anhang))

    with open(AUSGABE, "w", encoding="utf-8") as f:
        f.write("\n\n".join(md) + "\n")
    print(f"\nErgebnisse geschrieben: {AUSGABE}")


if __name__ == "__main__":
    main()
