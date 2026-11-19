"""Labor EAN-V4, Aufgabe 2: Erweiterung des Netzmodells.

Oben in NETZDATEN steht das Netz mit ALLEN Elementen, die in Aufgabe 2
vorkommen (nicht benoetigte zunaechst mit "an": False). In ABSCHNITTE steht
pro Teilaufgabe, was eingestellt wird. Beim Ausfuehren (F5) wird jede Variante
berechnet und alles in eine Markdown-Datei mit Bildern geschrieben.
Der Rechen- und Exportcode steht in netzberechnung.py.
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
            "die eingespeiste Leistung abzüglich der Leitungsverluste auf (negatives P; "
            "50 kW → 48,64 kW, also 1,36 kW Verluste) und liefert die geringe "
            "Blindleistung der Leitungen. Bei P = 0 kW ist das Netz unbelastet, alle Knoten liegen "
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
            "Netz zurückgespeist (19,71 kW). Alle Knoten hinter dem Speiseknoten liegen "
            "jetzt über 1,05 p.u., die Spannung steigt zum Strangende hin an (Knoten 4: 1,061 p.u., "
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

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from netzberechnung import erstelle_bericht  # noqa: E402


def main():
    # Pfade gelten relativ zum Ordner dieser Datei, egal von wo gestartet wird
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    erstelle_bericht(TITEL, AUSGABE, NENNSPANNUNG_KV, LEITUNGSTYP, KNOTEN, EXTERNES_NETZ,
                     LEITUNGEN, LASTEN, GENERATOREN, ABSCHNITTE,
                     bild_je_variante=BILD_JE_VARIANTE, detailtabellen=DETAILTABELLEN)


if __name__ == "__main__":
    main()
