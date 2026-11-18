"""Labor EAN-V4: rechnet Aufgabe 1 und 2 und fasst beide Ergebnisse in einer
Markdown-Datei fuer die Abgabe zusammen."""

import datetime
import os
import re

import aufgabe1
import aufgabe2

AUSGABE = "Abgabe_EAN-V4.md"
REPO = "https://github.com/CodeJF06/Pandapower_ElAuN_HSFL"

KOPF = f"""# Labor EAN-V4: Einführung in die Netzberechnung

Labor Elektrische Anlagen und Netze 1, WS 2026/27

| | |
| :--- | :--- |
| Name | Julian Fehre |
| Datum | {datetime.date.today():%d.%m.%Y} |
| Code | [{REPO.removeprefix("https://")}]({REPO}) |

Alle Ergebnisse wurden mit pandapower berechnet und von den Python-Skripten
automatisch erzeugt:

| Datei | Inhalt |
| :--- | :--- |
| `aufgabe1_grundgeruest.py` | Netzmodell Aufgabe 1, einfache Fassung |
| `aufgabe1.py` | Aufgabe 1 mit Netzplan und Markdown-Export |
| `aufgabe2_grundgeruest.py` | Teilaufgaben 2.1–2.6, einfache Fassung |
| `aufgabe2.py` | Aufgabe 2 mit Varianten, Spannungsprofilen und Markdown-Export |
| `abgabe.py` | rechnet beide Aufgaben und erzeugt diese Datei |

## Inhalt

- [Aufgabe 1: Netzmodell für ein Niederspannungsnetz](#aufgabe-1-netzmodell-für-ein-niederspannungsnetz)
- [Aufgabe 2: Erweiterung des Netzmodells](#aufgabe-2-erweiterung-des-netzmodells)
"""


def einbinden(md_datei):
    """Liest eine Ergebnisdatei, stuft Ueberschriften eine Ebene herab und
    passt Bildpfade an den Ort der Abgabe-Datei an."""
    with open(md_datei, encoding="utf-8") as f:
        text = f.read()
    text = re.sub(r"^(#+) ", r"#\1 ", text, flags=re.MULTILINE)
    ordner = os.path.relpath(os.path.dirname(md_datei) or ".",
                             os.path.dirname(AUSGABE) or ".")
    return re.sub(r"!\[([^\]]*)\]\(([^)/]+)\)",
                  lambda m: f"![{m[1]}]({os.path.join(ordner, m[2]).replace(os.sep, '/')})",
                  text)


if __name__ == "__main__":
    aufgabe1.main()
    aufgabe2.main()
    teile = [KOPF, einbinden(aufgabe1.AUSGABE), einbinden(aufgabe2.AUSGABE)]
    with open(AUSGABE, "w", encoding="utf-8") as f:
        f.write("\n---\n\n".join(t.strip() + "\n" for t in teile))
    print(f"\nAbgabe geschrieben: {AUSGABE}")
