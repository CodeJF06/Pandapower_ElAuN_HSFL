"""Labor EAN-V4: rechnet Aufgabe 1 und 2 und erstellt die Abgabe im Ordner abgabe/
(Bericht als .md, Bericht mit eingebetteten Bildern und zwei ZIP-Dateien)."""

import datetime
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HIER))

import aufgabe1  # noqa: E402
import aufgabe2  # noqa: E402
from abgabe_werkzeug import erstelle_abgabe  # noqa: E402

NAME = "Abgabe_EAN-V4"
REPO = "https://github.com/CodeJF06/Pandapower_ElAuN_HSFL"
DATUM = datetime.date(2026, 11, 18)

KOPF = f"""# Labor EAN-V4: Einführung in die Netzberechnung

Labor Elektrische Anlagen und Netze 1, WS 2026/27

| | |
| :--- | :--- |
| Name | Julian Fehre |
| Datum | {DATUM:%d.%m.%Y} |
| Code | [{REPO.removeprefix("https://")}]({REPO}/tree/main/EAN-V4) |

Alle Ergebnisse wurden mit pandapower berechnet und von den Python-Skripten
automatisch erzeugt:

| Datei | Inhalt |
| :--- | :--- |
| `EAN-V4/aufgabe1_grundgeruest.py` | Netzmodell Aufgabe 1, einfache Fassung |
| `EAN-V4/aufgabe1.py` | Aufgabe 1: Netzdaten, Aufruf von `netzberechnung.py` |
| `EAN-V4/aufgabe2_grundgeruest.py` | Teilaufgaben 2.1–2.6, einfache Fassung |
| `EAN-V4/aufgabe2.py` | Aufgabe 2: Netzdaten, Varianten und Beobachtungen |
| `EAN-V4/abgabe.py` | rechnet beide Aufgaben und erzeugt diese Datei |
| `EAN-V4/ergebnisse/` | Ergebnisse je Aufgabe und alle Bilder |
| `netzberechnung.py` | gemeinsamer Code: Lastfluss, Tabellen, Netzplan, Spannungsprofile |

## Inhalt

- [Aufgabe 1: Netzmodell für ein Niederspannungsnetz](#aufgabe-1-netzmodell-für-ein-niederspannungsnetz)
- [Aufgabe 2: Erweiterung des Netzmodells](#aufgabe-2-erweiterung-des-netzmodells)
"""


def main():
    os.chdir(HIER)
    aufgabe1.main()
    aufgabe2.main()
    erstelle_abgabe(HIER, NAME, KOPF, [aufgabe1.AUSGABE, aufgabe2.AUSGABE], DATUM)


if __name__ == "__main__":
    main()
