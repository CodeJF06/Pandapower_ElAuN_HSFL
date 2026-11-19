"""Gemeinsamer Code fuer die Abgabe eines Versuchs (EAN-V4, EAN-V5, ...).

erstelle_abgabe(...) fasst die Ergebnisdateien eines Versuchs zu einem Bericht
zusammen und erzeugt im Ordner <Versuch>/abgabe/:
- <name>.md                 Bericht, Bilder verlinkt (fuer GitHub)
- <name>_mit_Bildern.md     Bericht als einzelne Datei, Bilder eingebettet
- <name>.tex / <name>.pdf   Bericht als LaTeX und (wenn pdflatex installiert ist) als PDF
- <name>.zip                alles: gemeinsamer Code, Skripte, Ergebnisse, Bericht
- <name>_Bericht.zip        nur der Bericht (.md, .tex, .pdf) und seine Bilder
"""

import base64
import os
import re
import zipfile

from latex_export import kompiliere, md_zu_latex

REPO_ORDNER = os.path.dirname(os.path.abspath(__file__))
GEMEINSAM = ["README.md", "requirements.txt", "netzberechnung.py", "abgabe_werkzeug.py",
             "latex_export.py"]
BILD = re.compile(r"!\[([^\]]*)\]\(([^)]+\.png)\)")
DATEI_LINK = re.compile(r"(!?\[[^\]]*\])\(([^):]+\.(?:png|html))\)")   # Bilder und lokale Grafiken


def einbinden(md_datei, ziel):
    """Liest eine Ergebnisdatei, stuft Ueberschriften eine Ebene herab und passt
    Pfade von Bildern und lokalen Grafiken an den Ordner der Datei `ziel` an."""
    with open(md_datei, encoding="utf-8") as f:
        text = f.read()
    text = re.sub(r"^(#+) ", r"#\1 ", text, flags=re.MULTILINE)
    ordner = os.path.relpath(os.path.dirname(md_datei), os.path.dirname(ziel))
    return DATEI_LINK.sub(
        lambda m: f"{m[1]}({os.path.join(ordner, m[2]).replace(os.sep, '/')})", text)


def bilder_einbetten(text, ordner):
    """Ersetzt verlinkte PNG-Bilder durch eingebettete (Base64) Bilder."""
    def ersetze(m):
        with open(os.path.join(ordner, m[2]), "rb") as f:
            daten = base64.b64encode(f.read()).decode("ascii")
        return f"![{m[1]}](data:image/png;base64,{daten})"
    return BILD.sub(ersetze, text)


def schreibe(datei, text):
    with open(datei, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"Geschrieben: {os.path.relpath(datei, REPO_ORDNER)} "
          f"({os.path.getsize(datei) / 1024:.0f} kB)")


def in_zip(z, name, daten, datum):
    """Daten mit festem Zeitstempel in die ZIP schreiben, damit sich die ZIP bei
    gleichem Inhalt nicht bei jedem Lauf aendert."""
    info = zipfile.ZipInfo(name.replace(os.sep, "/"), date_time=datum.timetuple()[:6])
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    z.writestr(info, daten)


def lies(datei):
    with open(datei, "rb") as f:
        return f.read()


def packe_alles(zip_datei, versuch_ordner, datum):
    """Gemeinsamen Code und den ganzen Versuchsordner (ohne ZIPs) in der
    Ordnerstruktur des Repos packen, damit die Skripte aus der ZIP laufen."""
    dateien = [os.path.join(REPO_ORDNER, d) for d in GEMEINSAM]
    for wurzel, ordner, namen in os.walk(versuch_ordner):
        ordner[:] = sorted(o for o in ordner if o != "__pycache__")
        dateien += [os.path.join(wurzel, n) for n in sorted(namen)
                    if not n.endswith((".zip", ".pyc", ".aux", ".log", ".out", ".toc"))
                    and n != "temp-plot.html"]
    with zipfile.ZipFile(zip_datei, "w", zipfile.ZIP_DEFLATED) as z:
        for datei in dateien:
            in_zip(z, os.path.relpath(datei, REPO_ORDNER), lies(datei), datum)
    print(f"Geschrieben: {os.path.relpath(zip_datei, REPO_ORDNER)} ({len(dateien)} Dateien, "
          f"{os.path.getsize(zip_datei) / 1024:.0f} kB)")


def packe_bericht(zip_datei, bericht, datum, pdf=None):
    """Nur den Bericht (oben in der ZIP, als .md, .tex und ggf. .pdf) und die
    darin verlinkten Bilder und HTML-Grafiken packen."""
    ordner = os.path.dirname(bericht)
    with open(bericht, encoding="utf-8") as f:
        text = f.read()
    bilder = []

    def ersetze(m):
        pfad = os.path.normpath(os.path.join(ordner, m[2]))
        bilder.append(pfad)
        return f"{m[1]}({os.path.relpath(pfad, os.path.dirname(ordner)).replace(os.sep, '/')})"
    text = DATEI_LINK.sub(ersetze, text)
    bilder = list(dict.fromkeys(bilder))
    stamm = os.path.splitext(os.path.basename(bericht))[0]
    with zipfile.ZipFile(zip_datei, "w", zipfile.ZIP_DEFLATED) as z:
        in_zip(z, f"{stamm}.md", text.encode("utf-8"), datum)
        in_zip(z, f"{stamm}.tex", md_zu_latex(text).encode("utf-8"), datum)
        if pdf:
            in_zip(z, f"{stamm}.pdf", lies(pdf), datum)
        for bild in bilder:
            in_zip(z, os.path.relpath(bild, os.path.dirname(ordner)), lies(bild), datum)
    print(f"Geschrieben: {os.path.relpath(zip_datei, REPO_ORDNER)} "
          f"({len(bilder) + (3 if pdf else 2)} Dateien, "
          f"{os.path.getsize(zip_datei) / 1024:.0f} kB)")


def erstelle_abgabe(versuch_ordner, name, kopf, md_dateien, datum):
    """Bericht aus `kopf` und den Ergebnisdateien `md_dateien` (relativ zum
    Versuchsordner) erstellen und alle Abgabe-Dateien schreiben."""
    ordner = os.path.join(versuch_ordner, "abgabe")
    os.makedirs(ordner, exist_ok=True)
    bericht = os.path.join(ordner, f"{name}.md")

    teile = [kopf] + [einbinden(os.path.join(versuch_ordner, d), bericht) for d in md_dateien]
    text = "\n---\n\n".join(t.strip() + "\n" for t in teile)
    print()
    schreibe(bericht, text)
    schreibe(os.path.join(ordner, f"{name}_mit_Bildern.md"), bilder_einbetten(text, ordner))
    tex = os.path.join(ordner, f"{name}.tex")
    schreibe(tex, md_zu_latex(text))
    pdf = kompiliere(tex, datum)
    if pdf:
        print(f"Geschrieben: {os.path.relpath(pdf, REPO_ORDNER)} "
              f"({os.path.getsize(pdf) / 1024:.0f} kB)")
    packe_alles(os.path.join(ordner, f"{name}.zip"), versuch_ordner, datum)
    packe_bericht(os.path.join(ordner, f"{name}_Bericht.zip"), bericht, datum, pdf)
