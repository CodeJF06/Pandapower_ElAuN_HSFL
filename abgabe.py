"""Labor EAN-V4: rechnet Aufgabe 1 und 2 und erstellt die Abgabe.

Erzeugt:
- Abgabe_EAN-V4.md                    Bilder verlinkt (fuer GitHub)
- abgabe/Abgabe_EAN-V4_mit_Bildern.md Bilder eingebettet, eine einzelne Datei
- abgabe/Abgabe_EAN-V4.zip            alles fuer den Stud.IP-Upload
"""

import base64
import datetime
import os
import re
import zipfile

import aufgabe1
import aufgabe2

AUSGABE = "Abgabe_EAN-V4.md"
ORDNER_ABGABE = "abgabe"
MIT_BILDERN = os.path.join(ORDNER_ABGABE, "Abgabe_EAN-V4_mit_Bildern.md")
ZIP = os.path.join(ORDNER_ABGABE, "Abgabe_EAN-V4.zip")
ZIP_DATEIEN = ["aufgabe1_grundgeruest.py", "aufgabe1.py", "aufgabe2_grundgeruest.py",
               "aufgabe2.py", "abgabe.py", "requirements.txt", AUSGABE]
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
| `ergebnisse/` | Ergebnisse je Aufgabe und alle Bilder |

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


def bilder_einbetten(text, ordner):
    """Ersetzt verlinkte PNG-Bilder durch eingebettete (Base64) Bilder."""
    def ersetze(m):
        with open(os.path.join(ordner, m[2]), "rb") as f:
            daten = base64.b64encode(f.read()).decode("ascii")
        return f"![{m[1]}](data:image/png;base64,{daten})"
    return re.sub(r"!\[([^\]]*)\]\(([^)]+\.png)\)", ersetze, text)


def schreibe(datei, text):
    os.makedirs(os.path.dirname(datei) or ".", exist_ok=True)
    with open(datei, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"Geschrieben: {datei} ({os.path.getsize(datei) / 1024:.0f} kB)")


def packe_zip():
    """Skripte, Abgaben und den Ordner ergebnisse/ in eine ZIP-Datei packen."""
    dateien = list(ZIP_DATEIEN) + [MIT_BILDERN]
    for ordner in {os.path.dirname(aufgabe1.AUSGABE), os.path.dirname(aufgabe2.AUSGABE)}:
        dateien += sorted(os.path.join(ordner, d) for d in os.listdir(ordner))
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for datei in dict.fromkeys(dateien):
            name = os.path.basename(datei) if datei == MIT_BILDERN else os.path.relpath(datei)
            z.write(datei, arcname=name.replace(os.sep, "/"))
    print(f"Geschrieben: {ZIP} ({len(set(dateien))} Dateien, "
          f"{os.path.getsize(ZIP) / 1024:.0f} kB)")


def main():
    aufgabe1.main()
    aufgabe2.main()
    print()
    teile = [KOPF, einbinden(aufgabe1.AUSGABE), einbinden(aufgabe2.AUSGABE)]
    text = "\n---\n\n".join(t.strip() + "\n" for t in teile)
    schreibe(AUSGABE, text)
    schreibe(MIT_BILDERN, bilder_einbetten(text, os.path.dirname(AUSGABE) or "."))
    packe_zip()


if __name__ == "__main__":
    main()
