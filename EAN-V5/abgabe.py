"""Labor EAN-V5: rechnet Aufgabe 1 bis 3 und erstellt die Abgabe im Ordner abgabe/
(Bericht als .md, Bericht mit eingebetteten Bildern und zwei ZIP-Dateien)."""

import datetime
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HIER))

import aufgabe1  # noqa: E402
import aufgabe2  # noqa: E402
import aufgabe3  # noqa: E402
from abgabe_werkzeug import erstelle_abgabe  # noqa: E402

NAME = "Abgabe_EAN-V5"
REPO = "https://github.com/CodeJF06/Pandapower_ElAuN_HSFL"
DATUM = datetime.date(2026, 11, 19)

KOPF = f"""# Labor EAN-V5: Spannungsregelung in Mittelspannungsnetzen

Labor Elektrische Anlagen und Netze 1, WS 2026/27

| | |
| :--- | :--- |
| Name | Julian Fehre |
| Datum | {DATUM:%d.%m.%Y} |
| Code | [{REPO.removeprefix("https://")}]({REPO}/tree/main/EAN-V5) |

Alle Ergebnisse wurden mit pandapower berechnet und von den Python-Skripten
automatisch erzeugt:

| Datei | Inhalt |
| :--- | :--- |
| `EAN-V5/aufgabe1_grundgeruest.py` … `aufgabe3_grundgeruest.py` | Aufgaben 1–3, einfache Fassung |
| `EAN-V5/netz.py` | Netzdaten (Abbildung 1, Tabelle 1) und gemeinsamer Code für V5 |
| `EAN-V5/aufgabe1.py` … `aufgabe3.py` | Auswertung je Aufgabe mit Antworten |
| `EAN-V5/abgabe.py` | rechnet alle Aufgaben und erzeugt diese Datei |
| `EAN-V5/ergebnisse/` | Ergebnisse je Aufgabe, Bilder und interaktive Grafiken |

## Inhalt

- [Aufgabe 1: Mittelspannungsnetz in Ringtopologie](#aufgabe-1-mittelspannungsnetz-in-ringtopologie)
- [Aufgabe 2: Graphische Darstellung des Netzes](#aufgabe-2-graphische-darstellung-des-netzes)
- [Aufgabe 3: Spannungsabfall im Mittelspannungsnetz](#aufgabe-3-spannungsabfall-im-mittelspannungsnetz)
"""


def main():
    os.chdir(HIER)
    aufgabe1.main()
    aufgabe2.main()
    aufgabe3.main()
    erstelle_abgabe(HIER, NAME, KOPF, [aufgabe1.AUSGABE, aufgabe2.AUSGABE, aufgabe3.AUSGABE],
                    DATUM)


if __name__ == "__main__":
    main()
