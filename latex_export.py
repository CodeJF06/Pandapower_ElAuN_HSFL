"""Markdown-Bericht nach LaTeX umwandeln und zur PDF kompilieren.

Unterstuetzt genau das, was die Berichte verwenden: Ueberschriften, Absaetze,
fett, Code, Links, Listen, Tabellen, Bilder, Codebloecke und Trennlinien.
Die erste Ueberschrift (#) wird zum Titel, die Tabelle direkt danach mit leerer
Kopfzeile (Name, Datum, ...) zur Titelseite, der Abschnitt "Inhalt" zum
Inhaltsverzeichnis. Die Ueberschriften behalten ihre eigene Nummerierung
(z. B. "1.1 ..."), LaTeX nummeriert nicht zusaetzlich. Das Ergebnis laeuft mit pdflatex (MiKTeX, TeX Live, Overleaf).
"""

import datetime
import os
import re
import shutil
import subprocess

# Unicode-Zeichen, die pdflatex ohne Zusatzpakete nicht kennt
ZEICHEN = {
    "Ω": r"$\Omega$", "φ": r"$\varphi$", "Δ": r"$\Delta$", "−": r"$-$", "…": r"\dots{}",
    "→": r"$\rightarrow$", "±": r"$\pm$", "≈": r"$\approx$", "×": r"$\times$",
    "·": r"$\cdot$", "°": r"\textdegree{}", "≤": r"$\leq$", "≥": r"$\geq$",
}
SONDER = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
          "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}",
          "^": r"\textasciicircum{}"}
INLINE = re.compile(r"`([^`]+)`|\*\*(.+?)\*\*|\[([^\]]+)\]\(([^)]+)\)")
EBENEN = {2: "section", 3: "subsection", 4: "subsubsection", 5: "paragraph"}

PRAEAMBEL = r"""\documentclass[11pt,a4paper]{article}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{lmodern}
\usepackage[ngerman]{babel}
\usepackage[a4paper,margin=2.3cm]{geometry}
\usepackage{textcomp}
\usepackage{graphicx}
\usepackage{float}
\usepackage{booktabs}
\usepackage{array}
\usepackage{makecell}
\usepackage{adjustbox}
\usepackage{xcolor}
\usepackage{caption}
\usepackage[hidelinks]{hyperref}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0.6em}
\renewcommand{\arraystretch}{1.15}
\renewcommand{\theadfont}{\bfseries}
\setcounter{secnumdepth}{0}
\captionsetup{font=small}
"""


def text(s, formelzeichen=True):
    """Normalen Text fuer LaTeX maskieren. Formelzeichen wie S_r, u_k oder I_max
    werden als Index gesetzt (S mit Index r)."""
    s = "".join(SONDER.get(c, c) for c in s)
    if formelzeichen:
        s = re.sub(r"\b([A-Za-z])\\_([A-Za-z]{1,8})\b", r"\1$_\\mathrm{\2}$", s)
    return "".join(ZEICHEN.get(c, c) for c in s)


def code(s):
    """Code in Schreibmaschinenschrift; Umbruch nach / und _ erlaubt, damit
    lange Dateinamen in schmalen Tabellenspalten nicht ueberlaufen."""
    s = text(s, formelzeichen=False).replace("/", r"/\allowbreak{}")
    return r"\texttt{" + s.replace(r"\_", r"\_\allowbreak{}") + "}"


def inline(s):
    """Inline-Markdown (Code, fett, Links) umwandeln, Rest maskieren."""
    teile, pos = [], 0
    for m in INLINE.finditer(s):
        teile.append(text(s[pos:m.start()]))
        if m[1] is not None:
            teile.append(code(m[1]))
        elif m[2] is not None:
            teile.append(r"\textbf{" + inline(m[2]) + "}")
        elif m[4].startswith("#"):                     # Anker im Bericht: nur Text
            teile.append(inline(m[3]))
        else:
            teile.append(r"\href{" + m[4].replace("%", r"\%").replace("#", r"\#") + "}{"
                         + inline(m[3]) + "}")
        pos = m.end()
    teile.append(text(s[pos:]))
    return "".join(teile)


def zellen(zeile):
    return [z.strip() for z in zeile.strip().strip("|").split("|")]


def kopfzelle(k):
    """Kopfzelle fett, Einheit in eckigen Klammern in eine zweite Zeile."""
    m = re.match(r"^(.*\S)\s+(\[[^\]]+\])$", k)
    if m:
        return r"\thead{" + inline(m[1]) + r" \\ {" + inline(m[2]) + "}}"   # {} wegen \\[
    return r"\textbf{" + inline(k) + "}"


def tabelle(zeilen):
    """Markdown-Tabelle -> tabular mit booktabs, bei Bedarf auf Seitenbreite skaliert."""
    kopf = zellen(zeilen[0])
    koerper = [zellen(z) for z in zeilen[2:]]
    spalten = ""
    for nr, a in enumerate(zellen(zeilen[1])):
        if a.endswith(":") and not a.startswith(":"):
            spalten += "r"
        elif max(len(z[nr]) for z in koerper) > 30:      # langer Text: umbrechen
            spalten += r">{\raggedright\arraybackslash}p{4.5cm}"
        else:
            spalten += "l"
    aus = [r"\begin{table}[H]", r"\centering", r"\begin{adjustbox}{max width=\linewidth}",
           r"\begin{tabular}{" + spalten + "}", r"\toprule"]
    if any(kopf):
        aus += [" & ".join(kopfzelle(k) for k in kopf) + r" \\", r"\midrule"]
    aus += [" & ".join(inline(z) for z in zeile) + r" \\" for zeile in koerper]
    aus += [r"\bottomrule", r"\end{tabular}", r"\end{adjustbox}", r"\end{table}"]
    return "\n".join(aus)


def bild(alt, pfad):
    return "\n".join([r"\begin{figure}[H]", r"\centering",
                      r"\includegraphics[width=\linewidth,height=0.42\textheight,"
                      r"keepaspectratio]{" + pfad + "}",
                      r"\caption{" + inline(alt) + "}", r"\end{figure}"])


def md_zu_latex(md):
    """Wandelt den Markdown-Bericht in ein vollstaendiges LaTeX-Dokument um."""
    zeilen = md.splitlines()
    koerper, titel, untertitel, meta = [], "Bericht", [], []
    absatz, i, vor_erstem_abschnitt = [], 0, True

    def absatz_fertig():
        if absatz:
            (untertitel if vor_erstem_abschnitt and not meta else koerper).append(
                inline(" ".join(absatz)))
            absatz.clear()

    while i < len(zeilen):
        z = zeilen[i]
        kopf = re.match(r"^(#+) (.*)", z)
        if kopf:
            absatz_fertig()
            ebene, inhalt = len(kopf[1]), kopf[2].strip()
            if ebene == 1:
                titel = inline(inhalt)
            elif inhalt == "Inhalt":                   # eigenes Inhaltsverzeichnis
                i += 1
                while i < len(zeilen) and not zeilen[i].startswith("#"):
                    i += 1
                continue
            else:
                if vor_erstem_abschnitt:
                    vor_erstem_abschnitt = False
                koerper.append("\\" + EBENEN.get(ebene, "paragraph") + "{" + inline(inhalt) + "}")
        elif z.startswith("|"):
            absatz_fertig()
            block = []
            while i < len(zeilen) and zeilen[i].startswith("|"):
                block.append(zeilen[i])
                i += 1
            if vor_erstem_abschnitt and not meta and not any(zellen(block[0])):
                meta = [zellen(b) for b in block[2:]]  # Name, Datum, ... fuer die Titelseite
            else:
                koerper.append(tabelle(block))
            continue
        elif re.match(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$", z):
            absatz_fertig()
            m = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)", z)
            koerper.append(bild(m[1], m[2]))
        elif z.startswith("```"):
            absatz_fertig()
            code = []
            i += 1
            while i < len(zeilen) and not zeilen[i].startswith("```"):
                code.append(zeilen[i])
                i += 1
            koerper.append("\\begin{verbatim}\n" + "\n".join(code) + "\n\\end{verbatim}")
        elif z.startswith("- "):
            absatz_fertig()
            punkte = []
            while i < len(zeilen) and zeilen[i].startswith("- "):
                punkte.append(r"\item " + inline(zeilen[i][2:]))
                i += 1
            koerper.append("\\begin{itemize}\n" + "\n".join(punkte) + "\n\\end{itemize}")
            continue
        elif z.strip() == "---":
            absatz_fertig()
            if not vor_erstem_abschnitt:
                koerper.append(r"\clearpage")
        elif not z.strip():
            absatz_fertig()
        else:
            absatz.append(z.strip())
        i += 1
    absatz_fertig()

    titelseite = [r"\begin{titlepage}", r"\centering", r"\vspace*{3cm}",
                  r"{\LARGE\bfseries " + titel + r"\par}", r"\vspace{1cm}"]
    titelseite += [r"{\large " + u + r"\par}" for u in untertitel[:1]]
    if meta:
        titelseite += [r"\vspace{2cm}", r"\begin{tabular}{ll}"]
        titelseite += [r"\textbf{" + inline(a) + "} & " + inline(b) + r" \\"
                       for a, b, *_ in meta]
        titelseite += [r"\end{tabular}"]
    titelseite += [r"\vfill"] + [inline_absatz for inline_absatz in untertitel[1:]]
    titelseite += [r"\end{titlepage}", r"\tableofcontents", r"\clearpage"]

    return (PRAEAMBEL + "\n\\begin{document}\n\n" + "\n".join(titelseite) + "\n\n"
            + "\n\n".join(koerper) + "\n\n\\end{document}\n")


def kompiliere(tex_datei, datum=None):
    """Kompiliert die .tex-Datei zur PDF (zweimal fuer das Inhaltsverzeichnis).
    Mit `datum` bekommt die PDF diesen festen Zeitstempel und bleibt bei gleichem
    Inhalt byte-gleich. Gibt den Pfad der PDF zurueck oder None, wenn kein LaTeX
    installiert ist oder die Kompilierung fehlschlaegt."""
    pdflatex = shutil.which("pdflatex")
    if not pdflatex:
        print("Kein pdflatex gefunden: .tex-Datei z. B. in Overleaf oder mit MiKTeX kompilieren.")
        return None
    ordner, name = os.path.split(os.path.abspath(tex_datei))
    stamm = os.path.splitext(name)[0]
    umgebung = dict(os.environ)
    if datum:
        zeit = datetime.datetime(datum.year, datum.month, datum.day, 12, 0,
                                 tzinfo=datetime.timezone.utc)
        umgebung.update(SOURCE_DATE_EPOCH=str(int(zeit.timestamp())), FORCE_SOURCE_DATE="1")
    try:
        for _ in range(2):
            lauf = subprocess.run([pdflatex, "-interaction=nonstopmode", "-halt-on-error", name],
                                  cwd=ordner, capture_output=True, text=True, errors="replace",
                                  env=umgebung)
            if lauf.returncode != 0:
                print("pdflatex-Fehler, letzte Zeilen der Ausgabe:")
                print("\n".join(lauf.stdout.splitlines()[-15:]))
                return None
        return os.path.join(ordner, stamm + ".pdf")
    finally:
        for endung in (".aux", ".log", ".out", ".toc"):
            pfad = os.path.join(ordner, stamm + endung)
            if os.path.exists(pfad):
                os.remove(pfad)
