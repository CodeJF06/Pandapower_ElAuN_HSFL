"""Labor EAN-V5, Aufgabe 2: Graphische Darstellung des Netzes.

Erstellt die Netzgrafik mit simple_plotly (wie in der Anleitung) und ergaenzend
eine Ergebnisdarstellung mit pf_res_plotly. Beide werden als Bild (PNG) und
als interaktive HTML-Datei gespeichert; beim Ausfuehren (F5) entsteht
ergebnisse/aufgabe2.md.
"""

# ===========================================================================
# EINGABEN  -  nur hier aendern
# ===========================================================================

TITEL = "Aufgabe 2: Graphische Darstellung des Netzes"
AUSGABE = "ergebnisse/aufgabe2.md"

NOTIZEN = {
    "netz": (
        "Die Grafik zeigt die Knoten (blau), die Leitungen (grau), den "
        "Transformator (grün) und das externe Netz (gelb). Damit sie wie "
        "Abbildung 1 aussieht, haben die Knoten in `netz.py` Koordinaten bekommen: "
        "links der Kabelring (S1, S2), rechts der Freileitungsring (S3, S4). Ohne "
        "Koordinaten erzeugt pandapower eine automatische Anordnung. Lasten, "
        "Generatoren und die offenen Trennstellen stellt `simple_plotly` nicht dar."
    ),
    "ergebnis": (
        "Die Ergebnisdarstellung färbt die Knoten nach ihrer Spannung und die "
        "Leitungen nach ihrer Auslastung. Gut zu erkennen sind die niedrigen "
        "Spannungen im Freileitungsstrang S3 und die Überlastung des ersten "
        "Kabelabschnitts in S1."
    ),
}

# ===========================================================================
# Ab hier muss nichts mehr geaendert werden
# ===========================================================================

import os  # noqa: E402
import tempfile  # noqa: E402

import pandapower as pp  # noqa: E402
import plotly.io as pio  # noqa: E402
from pandapower.plotting.plotly import pf_res_plotly, simple_plotly  # noqa: E402

import netz  # noqa: E402

pio.templates.default = "plotly_white"


def speichere(fig, ordner, name, titel):
    """Speichert die Grafik als HTML (immer) und als PNG (wenn kaleido einen
    Browser findet). Gibt den Markdown-Text fuer den Bericht zurueck."""
    fig.write_html(os.path.join(ordner, f"{name}.html"), include_plotlyjs="cdn",
                   div_id=name)                  # feste ID: Datei aendert sich nicht bei jedem Lauf
    try:
        fig.write_image(os.path.join(ordner, f"{name}.png"), width=900, height=700, scale=2)
        print(f"Bild gespeichert:       {os.path.join(ordner, name)}.png")
        return f"![{titel}]({name}.png)\n\nInteraktive Fassung: [{name}.html]({name}.html)"
    except Exception as fehler:          # kaleido oder Browser fehlt
        print(f"PNG nicht moeglich ({fehler}); nur HTML gespeichert.")
        return f"Interaktive Grafik: [{name}.html]({name}.html) (Bildexport nicht verfügbar)"


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    ordner = os.path.dirname(AUSGABE)
    os.makedirs(ordner, exist_ok=True)

    net = netz.erstelle_netz(ring=False)
    pp.runpp(net)

    with tempfile.TemporaryDirectory() as tmp:     # plotly schreibt sonst temp-plot.html
        fig_netz = simple_plotly(net, auto_open=False, filename=os.path.join(tmp, "n.html"))
        fig_ergebnis = pf_res_plotly(net, climits_volt=(0.85, 1.0), climits_load=(0, 120),
                                     auto_open=False, filename=os.path.join(tmp, "e.html"))

    netz.schreibe_md(AUSGABE, [
        f"# {TITEL}",
        "## Netzgrafik\n\nErstellt wie in der Anleitung:\n\n"
        "```python\nfrom pandapower.plotting.plotly import simple_plotly\n"
        "import plotly.io as pio\npio.templates.default = \"plotly_white\"\n"
        "simple_plotly(net)\n```",
        speichere(fig_netz, ordner, "aufgabe2_netz", "Netzgrafik mit simple_plotly"),
        NOTIZEN.get("netz"),
        "## Ergänzend: Ergebnisdarstellung (Strahlennetz)\n\n"
        "Erstellt mit `pf_res_plotly(net)` nach der Lastflussberechnung "
        "(Farbskalen: Spannung 0,85–1,0 p.u., Auslastung 0–120 %).",
        speichere(fig_ergebnis, ordner, "aufgabe2_ergebnis",
                  "Ergebnisdarstellung mit pf_res_plotly: Spannung und Auslastung"),
        NOTIZEN.get("ergebnis"),
    ])


if __name__ == "__main__":
    main()
