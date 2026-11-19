"""Gemeinsamer Code fuer das Labor EAN-V4.

Baut aus den Netzdaten einer Aufgaben-Datei (aufgabe1.py, aufgabe2.py, ...) ein
pandapower-Netz, berechnet alle Varianten und schreibt die Ergebnisse als
Markdown-Datei mit Netzplan und Spannungsprofilen.

Die Aufgaben-Dateien rufen nur erstelle_bericht(...) auf. Hier muss fuer eine
neue Aufgabe normalerweise nichts geaendert werden.
"""

import math
import os

import matplotlib.pyplot as plt
import pandapower as pp


# ---------------------------------------------------------------------------
# Netz aufbauen, aendern, berechnen
# ---------------------------------------------------------------------------

def baue_netz(d):
    """Erstellt das pandapower-Netz aus den Netzdaten d (siehe erstelle_bericht)."""
    net = pp.create_empty_network(name=d["titel"])

    bus = {name: pp.create_bus(net, vn_kv=d["nennspannung_kv"], name=name)
           for name in d["knoten"]}

    def knoten(name):
        if name not in bus:
            raise ValueError(f"Knoten '{name}' steht nicht in KNOTEN {d['knoten']}")
        return bus[name]

    ext = d["externes_netz"]
    pp.create_ext_grid(net, bus=knoten(ext["knoten"]), vm_pu=ext["u_pu"], name=ext["name"])

    for von, nach, laenge_m, *typ in d["leitungen"]:
        pp.create_line(net, from_bus=knoten(von), to_bus=knoten(nach),
                       length_km=laenge_m / 1000, name=f"{von} – {nach}",
                       std_type=typ[0] if typ else d["leitungstyp"])

    # pandapower rechnet in MW / Mvar
    for last in d["lasten"]:
        pp.create_load(net, bus=knoten(last["knoten"]), name=last["name"],
                       p_mw=last["p_kw"] / 1000, q_mvar=last["q_kvar"] / 1000,
                       in_service=last.get("an", True))

    for gen in d["generatoren"]:
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


def netz_fuer(d, abschnitt, variante=None):
    """Netz im Zustand von Abschnitt (+ Variante), noch nicht berechnet."""
    net = baue_netz(d)
    aendere(net, abschnitt.get("einstellung", {}), abschnitt["titel"])
    if variante:
        aendere(net, variante, f"{abschnitt['titel']} / {variante['titel']}")
    return net


def suche_kompensation(d, abschnitt):
    """Kleinstes Q/P (induktiv, fuer alle genannten Generatoren gleich), bei dem
    die hoechste Knotenspannung <= ziel_u_pu ist. Gibt (k, net) oder (None, net)."""
    komp = abschnitt["kompensation"]
    ziel = komp["ziel_u_pu"]

    def netz_mit(k):
        net = netz_fuer(d, abschnitt)
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
        if text == "–":                      # Platzhalter fuer "kein Wert"
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


def de(wert, stellen):
    """Zahl mit Dezimalkomma fuer den Fliesstext."""
    return zahl(wert, stellen).replace(".", ",")


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
    teile = []
    if len(net.load) or len(net.sgen):
        teile.append(f"{h} Lasten und Generatoren (eingestellt)\n\n" + md_einstellungen(net))

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

    teile.append(f"{h} Externes Netz\n\n"
                 "Positive Werte: Bezug aus dem vorgelagerten Netz, negative: Rückspeisung.\n\n"
                 + md_tabelle(
                     ["Externes Netz", "Knoten", "U_soll [p.u.]", "P [kW]", "Q [kvar]"],
                     [[e.name, busname(net, e.bus), f"{e.vm_pu:.2f}",
                       zahl(r.p_mw * 1000), zahl(r.q_mvar * 1000)]
                      for e, r in zip(net.ext_grid.itertuples(),
                                      net.res_ext_grid.itertuples())]))
    return "\n\n".join(teile)


def uebersicht_kopf(d):
    return (["Variante", "Einstellung"] + [f"U {k} [p.u.]" for k in d["knoten"]]
            + ["P ext. Netz [kW]", "Q ext. Netz [kvar]", "max. Auslastung [%]"])


def uebersicht_zeile(titel, einstellung, net, konvergiert):
    """Eine Zeile der Uebersichtstabelle eines Abschnitts."""
    if not konvergiert:
        return [titel, einstellung] + ["–"] * (len(net.bus) + 3)
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
        if len(rest) == len(offen):          # nicht angeschlossene Leitungen
            break
        offen = rest
    for n, b in enumerate(net.bus.index):    # Inselknoten ans Ende haengen
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
    ax.axhline(net.ext_grid.vm_pu.iloc[0], color="0.55", lw=1, ls="--", zorder=0)
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
    print(f"Bild gespeichert:       {datei}")


# ---------------------------------------------------------------------------
# Bericht
# ---------------------------------------------------------------------------

VORZEICHEN = (
    "- Lasten: P, Q > 0 = Bezug (Q > 0 induktiv).\n"
    "- Generatoren: P > 0 = Einspeisung; Q < 0 = Aufnahme von Blindleistung "
    "(induktiv), Q > 0 = Abgabe (kapazitiv).\n"
    "- Externes Netz: P, Q > 0 = Bezug aus dem vorgelagerten Netz, < 0 = Rückspeisung.")


def _abschnitt(d, abschnitt, nr_a, net_basis, ordner, stamm, anhang):
    """Berechnet alle Varianten eines Abschnitts und gibt dessen Markdown zurueck."""
    print(f"\n--- {abschnitt['titel']} ---")
    teil = [f"## {abschnitt['titel']}"]
    if abschnitt.get("einstellung"):
        teil.append("Gemeinsame Einstellung: " + beschreibe(net_basis, abschnitt["einstellung"]))

    zeilen, kurven = [], []
    for nr_v, variante in enumerate(abschnitt["varianten"], start=1):
        net_v = netz_fuer(d, abschnitt, variante)
        ok = berechne(net_v)
        zeilen.append(uebersicht_zeile(variante["titel"], beschreibe(net_v, variante), net_v, ok))
        if not ok:
            print(f"  {variante['titel']}: Lastfluss konvergiert nicht")
            continue
        kurven.append((variante["titel"], net_v))
        if d["bild_je_variante"]:
            name = f"{stamm}_{nr_a}_{nr_v}.png"
            plot_netz(net_v, os.path.join(ordner, name),
                      f"{abschnitt['titel']}: {variante['titel']}")
            anhang.append(f"![{variante['titel']}]({name})")
        if d["detailtabellen"]:
            anhang.append(f"### {abschnitt['titel']}: {variante['titel']}\n\n"
                          + md_ergebnisse(net_v, ebene=4))

    komp_text = None
    if "kompensation" in abschnitt:
        komp = abschnitt["kompensation"]
        k, net_k = suche_kompensation(d, abschnitt)
        if k is None:
            komp_text = (f"**Kompensation:** Auch mit Q/P = 10 bleibt mindestens eine "
                         f"Knotenspannung über {de(komp['ziel_u_pu'], 2)} p.u.")
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
            namen = komp["generatoren"]
            aufzaehlung = (", ".join(namen[:-1]) + " und " + namen[-1]
                           if len(namen) > 1 else namen[0])
            komp_text = (
                f"**Kompensation:** Damit keine Knotenspannung über "
                f"{de(komp['ziel_u_pu'], 2)} p.u. liegt, müssen {aufzaehlung} "
                f"je **{de(k, 2)} kvar pro kW** induktive Blindleistung aufnehmen "
                f"(|Q|/P = {de(k, 2)}, cos φ = {de(cos_phi, 3)} untererregt), "
                f"zusammen {de(q_summe, 1)} kvar: "
                + ", ".join(f"{n} {de(e['q_kvar'], 1)} kvar" for n, e in einstellung.items())
                + ".")
            print(f"  Kompensation: Q/P = {k:.3f}")

    teil.append(md_tabelle(uebersicht_kopf(d), zeilen))
    if komp_text:
        teil.append(komp_text)
    if kurven:
        name = f"{stamm}_profil_{nr_a}.png"
        plot_spannungsprofil(kurven, os.path.join(ordner, name),
                             f"Spannungsprofil – {abschnitt['titel']}")
        teil.append(f"![Spannungsprofil {abschnitt['titel']}]({name})")
    if abschnitt.get("notiz"):
        teil.append(abschnitt["notiz"])
    return "\n\n".join(teil)


def erstelle_bericht(titel, ausgabe, nennspannung_kv, leitungstyp, knoten, externes_netz,
                     leitungen, lasten, generatoren, abschnitte=(),
                     bild_je_variante=False, detailtabellen=False):
    """Baut das Netz, berechnet es und schreibt den Bericht nach `ausgabe`.

    Ohne abschnitte wird nur das Netz selbst berechnet und vollstaendig
    dokumentiert (wie in Aufgabe 1). Mit abschnitten wird pro Teilaufgabe eine
    Uebersichtstabelle und ein Spannungsprofil ueber alle Varianten erzeugt
    (wie in Aufgabe 2). Bilder landen im selben Ordner wie `ausgabe`.
    """
    d = dict(titel=titel, nennspannung_kv=nennspannung_kv, leitungstyp=leitungstyp,
             knoten=knoten, externes_netz=externes_netz, leitungen=leitungen,
             lasten=lasten, generatoren=generatoren,
             bild_je_variante=bild_je_variante, detailtabellen=detailtabellen)
    ordner = os.path.dirname(ausgabe) or "."
    os.makedirs(ordner, exist_ok=True)
    stamm = os.path.splitext(os.path.basename(ausgabe))[0]
    bild = f"{stamm}_netz.png"

    net = baue_netz(d)
    if not berechne(net):
        pp.diagnostic(net)
        raise SystemExit("Lastfluss des Ausgangsnetzes konvergiert nicht - siehe Diagnose.")

    if not abschnitte:
        plot_netz(net, os.path.join(ordner, bild), titel)
        md = [f"# {titel}",
              f"## Einlinienersatzschaltbild\n\n![{titel}]({bild})",
              "## Leitungstypen\n\n" + md_leitungstypen(net),
              md_ergebnisse(net, ebene=2)]
    else:
        plot_netz(net, os.path.join(ordner, bild), "Ausgangsnetz mit allen Elementen")
        md = [f"# {titel}",
              f"## Netzmodell\n\nAlle in {titel.split(':')[0]} verwendeten Elemente; "
              "ausgeschaltete sind grau "
              "dargestellt. Spannungen und Auslastungen gelten für den Ausgangszustand.\n\n"
              f"![Ausgangsnetz]({bild})",
              "### Leitungstypen\n\n" + md_leitungstypen(net),
              "### Elemente im Ausgangszustand\n\n" + md_einstellungen(net),
              "### Vorzeichen\n\n" + VORZEICHEN]
        anhang = []
        for nr_a, abschnitt in enumerate(abschnitte, start=1):
            md.append(_abschnitt(d, abschnitt, nr_a, net, ordner, stamm, anhang))
        if anhang:
            md.append("## Anhang: Ergebnisse je Variante\n\n" + "\n\n".join(anhang))

    with open(ausgabe, "w", encoding="utf-8") as f:
        f.write("\n\n".join(md) + "\n")
    print(f"\nErgebnisse geschrieben: {ausgabe}")
