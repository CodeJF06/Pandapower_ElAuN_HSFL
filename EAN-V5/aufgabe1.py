"""Labor EAN-V5, Aufgabe 1: Mittelspannungsnetz in Ringtopologie (Strahlennetz).

Netzdaten stehen in netz.py. Oben hier stehen Titel, Ausgabe und die Antworten
zu den Fragen; beim Ausfuehren (F5) entsteht ergebnisse/aufgabe1.md.
"""

# ===========================================================================
# EINGABEN  -  nur hier aendern
# ===========================================================================

TITEL = "Aufgabe 1: Mittelspannungsnetz in Ringtopologie"
AUSGABE = "ergebnisse/aufgabe1.md"

NOTIZEN = {
    "1.1": (
        "**Antwort:** Der Lastfluss konvergiert, die Diagnosefunktion meldet keine "
        "Auffälligkeiten. Der größte Spannungsabfall tritt mit **12,66 %** am Knoten "
        "**S3 K3** auf (bezogen auf 20 kV). Davon fallen bereits 7,67 % über dem "
        "Transformator ab (Sammelschiene 0,9233 p.u.), im Strang selbst noch rund "
        "5,0 %. Mehrere Knoten liegen unter 0,9 p.u. und damit außerhalb des "
        "üblichen Bands von ±10 %; ohne Spannungsregelung ist das Netz so nicht "
        "zulässig betreibbar."
    ),
    "1.2": (
        "**Antwort:** Die ausgetauschte Leistung ist das Ergebnis des externen "
        "Netzes (Slack) und steht in `net.res_ext_grid` (alternativ auf der "
        "Oberspannungsseite des Trafos in `net.res_trafo`). Zur Kontrolle lässt sie "
        "sich aus der Leistungsbilanz bestimmen: Summe der Lasten minus Summe der "
        "Erzeugung plus alle Verluste. Für die Blindleistung gilt dasselbe mit der "
        "Blindleistungsaufnahme von Leitungen und Trafo."
    ),
    "1.3": (
        "**Antwort:** Die äußeren Stränge S1 und S3 versorgen deutlich mehr Last "
        "(Saldo 10,5 MW gegenüber 1,4 MW) über eine größere Länge (15 km gegenüber "
        "11 km). Sie sind daher wesentlich höher ausgelastet und haben den größeren "
        "Spannungsabfall. Am Ende von S1 und S3 steigt die Spannung wieder an, weil "
        "G1 bzw. G3 dort einspeisen; in S2 und S4 liegt das Minimum am Strangende.\n\n"
        "Bei gleicher Belastung unterscheiden sich Kabel und Freileitung: Die Ströme "
        "sind ähnlich (S1 375 A, S3 386 A), das Kabel ist mit I_max = 319 A aber zu "
        "**117 % überlastet**, die Freileitung mit I_max = 470 A nur zu 82 % "
        "ausgelastet. Dafür ist der Spannungsabfall auf der Freileitung größer "
        "(U min 0,873 statt 0,892 p.u.), weil ihr Längsblindwiderstand X' fast "
        "dreimal so groß ist und die induktive Blindleistung der Lasten dort stärker "
        "wirkt; das Kabel liefert zusätzlich kapazitive Blindleistung."
    ),
    "1.4": (
        "**Antwort:** Die Verluste betragen 1027 kW auf den Leitungen und 103 kW im "
        "Transformator, zusammen **1130 kW** (rund 4,5 % der bezogenen Leistung). Sie "
        "entstehen fast vollständig in den hoch belasteten Strängen S1 und S3 "
        "(je rund 450 kW). Die Blindleistungsaufnahme des Netzes beträgt "
        "**4587 kvar**, davon 4101 kvar im Transformator. Die Kabel geben wegen ihrer "
        "Kapazität Blindleistung ab (negatives Q), die Freileitungen nehmen "
        "Blindleistung auf."
    ),
}

# ===========================================================================
# Ab hier muss nichts mehr geaendert werden
# ===========================================================================

import math  # noqa: E402
import os  # noqa: E402

import pandapower as pp  # noqa: E402

import netz  # noqa: E402
from netz import md_tabelle, zahl  # noqa: E402


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    ordner = os.path.dirname(AUSGABE)
    os.makedirs(ordner, exist_ok=True)

    net = netz.erstelle_netz(ring=False)
    diagnose = pp.diagnostic(net, warnings_only=True, report_style=None)  # vor runpp!
    pp.runpp(net)

    # 1.1 Spannungen
    mv = net.res_bus[net.bus.vn_kv == 20]
    k_max = mv.vm_pu.idxmin()
    pruefung = (f"Lastfluss konvergiert: **{'ja' if net.converged else 'nein'}**. "
                "Diagnosefunktion: " + ("keine Auffälligkeiten." if not diagnose else
                                        "Hinweise zu " + ", ".join(diagnose) + "."))
    maximum = (f"Maximaler Spannungsabfall: **{(1 - mv.vm_pu[k_max]) * 100:.2f} %** "
               f"am Knoten **{net.bus.name[k_max]}** ({mv.vm_pu[k_max]:.4f} p.u.).")

    # 1.2 Leistungsbilanz (P in MW, Q in Mvar)
    ext = net.res_ext_grid.iloc[0]
    s_ext = math.hypot(ext.p_mw, ext.q_mvar)
    bilanz = [
        ("Lasten", net.res_load.p_mw.sum(), net.res_load.q_mvar.sum()),
        ("− Erzeugung", -net.res_sgen.p_mw.sum(), -net.res_sgen.q_mvar.sum()),
        ("+ Verluste Leitungen", net.res_line.pl_mw.sum(), net.res_line.ql_mvar.sum()),
        ("+ Verluste Transformator", net.res_trafo.pl_mw.sum(), net.res_trafo.ql_mvar.sum()),
    ]
    summe = (sum(b[1] for b in bilanz), sum(b[2] for b in bilanz))
    bilanz_md = md_tabelle(
        ["Anteil", "P [MW]", "Q [Mvar]"],
        [[n, zahl(p, 3), zahl(q, 3)] for n, p, q in bilanz]
        + [["**= Summe**", f"**{zahl(summe[0], 3)}**", f"**{zahl(summe[1], 3)}**"],
           ["Externes Netz (`res_ext_grid`)", zahl(ext.p_mw, 3), zahl(ext.q_mvar, 3)]])
    ext_md = md_tabelle(
        ["P [MW]", "Q [Mvar]", "S [MVA]", "cos φ", "Trafo-Auslastung [%]"],
        [[zahl(ext.p_mw, 2), zahl(ext.q_mvar, 2), f"{s_ext:.2f}", f"{ext.p_mw / s_ext:.3f}",
          f"{net.res_trafo.loading_percent.iloc[0]:.1f}"]])

    # 1.3 Straenge
    profil = "aufgabe1_profil.png"
    netz.plot_spannungsprofil([("Strahlennetz", net)], os.path.join(ordner, profil),
                              "Spannungsprofil der Stränge (Strahlennetz)")

    # 1.4 Verluste
    verluste_md = md_tabelle(
        ["", "P_V [kW]", "Q_V [kvar]"],
        [[n if "gesamt" not in n else f"**{n}**", zahl(p, 1), zahl(q, 1)]
         for n, (p, q) in netz.verluste(net).items()])

    netz.schreibe_md(AUSGABE, [
        f"# {TITEL}",
        "Strahlennetz: Die Trennstellen am Ende der Stränge sind geöffnet. "
        f"Spannung am externen Netz {netz.EXTERNES_NETZ_U_PU} p.u.",
        "## Netzdaten\n\n" + netz.md_netzdaten(net),
        "## 1.1 Lastfluss und Spannungsabfall",
        pruefung,
        "Spannungsabfall bezogen auf die Nennspannung 20 kV:\n\n" + netz.md_knotenspannungen(net),
        maximum,
        NOTIZEN.get("1.1"),
        "## 1.2 Leistungsaustausch mit dem externen Netz",
        ext_md,
        "Kontrolle über die Leistungsbilanz:\n\n" + bilanz_md,
        NOTIZEN.get("1.2"),
        "## 1.3 Vergleich der Stränge",
        netz.md_straenge(net),
        f"![Spannungsprofil der Stränge]({profil})",
        "### Leitungsabschnitte\n\n" + netz.md_leitungen(net),
        NOTIZEN.get("1.3"),
        "## 1.4 Verluste und Blindleistung",
        "Q > 0: Aufnahme von Blindleistung, Q < 0: Abgabe (kapazitiv).\n\n" + verluste_md,
        NOTIZEN.get("1.4"),
    ])


if __name__ == "__main__":
    main()
