"""Labor EAN-V5, Aufgabe 3: Spannungsabfall im Mittelspannungsnetz.

Vergleicht das Netz als Strahlennetz (Trennstellen offen) und als Ringnetz
(Trennstellen geschlossen); beim Ausfuehren (F5) entsteht ergebnisse/aufgabe3.md.
"""

# ===========================================================================
# EINGABEN  -  nur hier aendern
# ===========================================================================

TITEL = "Aufgabe 3: Spannungsabfall im Mittelspannungsnetz"
AUSGABE = "ergebnisse/aufgabe3.md"

NOTIZEN = {
    "3.3": (
        "**Antwort:** Im Ringnetz sind die beiden Strangenden eines Rings direkt "
        "verbunden und haben deshalb dieselbe Spannung: Im Kabelring gleichen sich "
        "S1 K4 und S2 K4 auf 0,9110 p.u. an, im Freileitungsring S3 K4 und S4 K4 auf "
        "0,8969 p.u. Der Strang mit der vorher niedrigeren Endspannung wird dabei "
        "angehoben, der andere abgesenkt. Die Sammelschiene ändert sich praktisch "
        "nicht (+0,0002 p.u.). Die Verluste sinken um 25 kW auf 1105 kW "
        "(−2,2 %).\n\n"
        "Grund: Im Ring wird jeder Knoten über zwei parallele Wege versorgt. Die "
        "Leistung teilt sich nach den Impedanzen auf, die Ströme werden "
        "gleichmäßiger verteilt, und weil die Verluste quadratisch mit dem Strom "
        "steigen, sinken sie insgesamt. Die Änderungen sind hier klein, weil die "
        "Spannungen an den Strangenden schon vorher ähnlich waren und dort mit "
        "G1 und G3 eingespeist wird.\n\n"
        "In beiden Ringen fließen rund 0,6 MW über die geschlossene Trennstelle vom "
        "äußeren in den inneren Strang, weil ein Teil der Einspeisung von G1 bzw. G3 "
        "jetzt die Lasten in S2 bzw. S4 versorgt. Die inneren Stränge werden dadurch "
        "entlastet, die äußeren müssen am Anfang mehr Leistung übertragen: Der "
        "erste Kabelabschnitt von S1 ist mit 120,7 % statt 117,5 % sogar noch stärker "
        "überlastet. Der Ringschluss allein löst die Überlastung also nicht."
    ),
}

# ===========================================================================
# Ab hier muss nichts mehr geaendert werden
# ===========================================================================

import os  # noqa: E402

import pandapower as pp  # noqa: E402

import netz  # noqa: E402
from netz import md_tabelle, zahl  # noqa: E402


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    ordner = os.path.dirname(AUSGABE)
    os.makedirs(ordner, exist_ok=True)

    strahl, ring = netz.erstelle_netz(ring=False), netz.erstelle_netz(ring=True)
    pp.runpp(strahl)
    pp.runpp(ring)

    # 3.3 Vergleich: Sammelschiene und Strangenden, danach alle Knoten
    def zeile(name):
        b = netz.bus(strahl, name)
        u_s, u_r = strahl.res_bus.vm_pu[b], ring.res_bus.vm_pu[b]
        return [name, f"{u_s:.4f}", f"{u_r:.4f}", zahl(u_r - u_s, 4),
                zahl((u_r - u_s) * 20000, 0)]

    kopf = ["Knoten", "U Strahl [p.u.]", "U Ring [p.u.]", "ΔU [p.u.]", "ΔU [V]"]
    enden = [netz.SAMMELSCHIENE] + [f"{s} K{len(l)}" for s, (_, l) in netz.STRAENGE.items()]
    alle = [n for n in strahl.bus.name if strahl.bus.vn_kv[netz.bus(strahl, n)] == 20]

    v_s, v_r = netz.verluste(strahl), netz.verluste(ring)
    verluste_md = md_tabelle(
        ["", "P_V Strahl [kW]", "P_V Ring [kW]", "ΔP_V [kW]", "Q_V Strahl [kvar]",
         "Q_V Ring [kvar]"],
        [[n if "gesamt" not in n else f"**{n}**", zahl(v_s[n][0], 1), zahl(v_r[n][0], 1),
          zahl(v_r[n][0] - v_s[n][0], 1), zahl(v_s[n][1], 1), zahl(v_r[n][1], 1)]
         for n in v_s])

    w_s, w_r = netz.strang_werte(strahl), netz.strang_werte(ring)
    straenge_md = md_tabelle(
        ["Strang", "max. Auslastung Strahl [%]", "max. Auslastung Ring [%]",
         "U min Strahl [p.u.]", "U min Ring [p.u.]"],
        [[s, f"{w_s[s]['auslastung']:.1f}", f"{w_r[s]['auslastung']:.1f}",
          f"{w_s[s]['u_min']:.4f}", f"{w_r[s]['u_min']:.4f}"] for s in netz.STRAENGE])

    profil = "aufgabe3_profil.png"
    netz.plot_spannungsprofil([("Strahl", strahl), ("Ring", ring)],
                              os.path.join(ordner, profil),
                              "Spannungsprofil: Strahlennetz (durchgezogen) und Ringnetz (gestrichelt)")

    netz.schreibe_md(AUSGABE, [
        f"# {TITEL}",
        "Netz wie in Aufgabe 1. Strahlennetz: Trennstellen offen; Ringnetz: "
        "Trennstellen geschlossen.",
        "## 3.1 Strahlennetz",
        "Knotenspannungen (ΔU bezogen auf 20 kV):\n\n" + netz.md_knotenspannungen(strahl),
        f"Verlustleistung gesamt: **{v_s['Netz gesamt'][0]:.1f} kW** "
        f"(Leitungen {v_s['Leitungen gesamt'][0]:.1f} kW, "
        f"Transformator {v_s['Transformator'][0]:.1f} kW).",
        "## 3.2 Ringnetz",
        "Knotenspannungen (ΔU bezogen auf 20 kV):\n\n" + netz.md_knotenspannungen(ring),
        f"Verlustleistung gesamt: **{v_r['Netz gesamt'][0]:.1f} kW** "
        f"(Leitungen {v_r['Leitungen gesamt'][0]:.1f} kW, "
        f"Transformator {v_r['Transformator'][0]:.1f} kW).",
        "## 3.3 Vergleich",
        "### Sammelschiene und Strangenden\n\n" + md_tabelle(kopf, [zeile(n) for n in enden]),
        "### Verluste\n\n" + verluste_md,
        "### Stränge\n\n" + straenge_md,
        f"![Spannungsprofil Strahl- und Ringnetz]({profil})",
        "### Alle Knoten\n\n" + md_tabelle(kopf, [zeile(n) for n in alle]),
        NOTIZEN.get("3.3"),
    ])


if __name__ == "__main__":
    main()
