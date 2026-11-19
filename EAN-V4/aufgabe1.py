"""Labor EAN-V4, Aufgabe 1: Netzmodell fuer ein Niederspannungsnetz.

Oben im Abschnitt NETZDATEN wird das Netz beschrieben, beim Ausfuehren (F5)
wird es aufgebaut, berechnet und als Markdown-Datei mit Netzplan gespeichert.
Der Rechen- und Exportcode steht in netzberechnung.py.
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

# Teilaufgaben mit Varianten (Aufbau wie in aufgabe2.py).
# Leere Liste = nur das Netz oben wird berechnet und vollstaendig dokumentiert.
ABSCHNITTE = []

BILD_JE_VARIANTE = False     # True: zusaetzlich ein Netzplan pro Variante
DETAILTABELLEN = False       # True: alle Tabellen je Variante im Anhang

# ===========================================================================
# Ab hier muss nichts mehr geaendert werden
# ===========================================================================

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from netzberechnung import erstelle_bericht  # noqa: E402


def main():
    # Pfade gelten relativ zum Ordner dieser Datei, egal von wo gestartet wird
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    erstelle_bericht(TITEL, AUSGABE, NENNSPANNUNG_KV, LEITUNGSTYP, KNOTEN, EXTERNES_NETZ,
                     LEITUNGEN, LASTEN, GENERATOREN, ABSCHNITTE,
                     bild_je_variante=BILD_JE_VARIANTE, detailtabellen=DETAILTABELLEN)


if __name__ == "__main__":
    main()
