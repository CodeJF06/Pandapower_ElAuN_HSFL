# Labor EAN-V4: Einführung in die Netzberechnung

Netzberechnung mit [pandapower](https://www.pandapower.org/) für das Labor
*Elektrische Anlagen und Netze 1* (WS 2026/27): ein Niederspannungsstrang mit
vier Knoten, Lasten und Generatoren, Lastflussberechnung und automatische
Dokumentation der Ergebnisse als Markdown.

**Ergebnisse:** [Abgabe_EAN-V4.md](Abgabe_EAN-V4.md)

![Netzmodell aus Aufgabe 2 mit allen Elementen](ergebnisse/aufgabe2_netz.png)

## Dateien

| Datei | Inhalt |
| :--- | :--- |
| `aufgabe1_grundgeruest.py` | Aufgabe 1 in einfacher Form: Netz aufbauen, rechnen, Ergebnisse ausgeben |
| `aufgabe1.py` | Aufgabe 1 mit Netzdaten oben, Netzplan und Markdown-Export |
| `aufgabe2_grundgeruest.py` | Teilaufgaben 2.1–2.6 in einfacher Form |
| `aufgabe2.py` | Aufgabe 2 mit Varianten, Spannungsprofilen, automatischer Kompensation (2.6) und Beobachtungen |
| `abgabe.py` | rechnet beide Aufgaben und erstellt die Abgabe |
| `Abgabe_EAN-V4.md` | Abgabe mit verlinkten Bildern (für GitHub) |
| `abgabe/Abgabe_EAN-V4_mit_Bildern.md` | Abgabe als einzelne Datei, Bilder eingebettet |
| `abgabe/Abgabe_EAN-V4.zip` | alles: Skripte, Abgabe und Bilder |
| `abgabe/Abgabe_EAN-V4_Bericht.zip` | nur der Bericht: `Abgabe_EAN-V4.md` und die Bilder |
| `ergebnisse/` | Ergebnisse je Aufgabe und alle Bilder |

## Ausführen

```bash
pip install -r requirements.txt
```

```bash
python abgabe.py
```

Das rechnet beide Aufgaben neu und schreibt alle Ergebnisse, die Abgabe und die
ZIP-Datei. Einzelne Aufgaben lassen sich auch direkt starten
(`python aufgabe1.py`, `python aufgabe2.py`) oder in Spyder mit F5.
Alle Ausgaben landen immer neben den Skripten, egal aus welchem Ordner sie
gestartet werden.

## Netz anpassen

In `aufgabe1.py` und `aufgabe2.py` steht oben ein Abschnitt `NETZDATEN`. Nur dort
wird etwas geändert, alle Werte in kW, kvar und m:

```python
KNOTEN = ["Knoten 1", "Knoten 2", "Knoten 3", "Knoten 4"]
LEITUNGEN = [("Knoten 1", "Knoten 2", 150), ...]        # von, nach, Länge in m
LASTEN = [{"name": "V1", "knoten": "Knoten 4", "p_kw": 40, "q_kvar": 15}]
GENERATOREN = [{"name": "G4", "knoten": "Knoten 4", "p_kw": 0, "q_kvar": 0, "an": False}]
```

In `aufgabe2.py` beschreibt `ABSCHNITTE` jede Teilaufgabe: eine gemeinsame
Einstellung und die Varianten, die berechnet werden, z. B.
`{"titel": "P = 10 kW", "G4": {"p_kw": 10}}`. Jede Variante startet vom Netz
oben. Beobachtungen stehen bei `"notiz"` und erscheinen in der Abgabe.

## Vorzeichen

- **Lasten:** P, Q > 0 = Bezug (Q > 0 induktiv)
- **Generatoren (Static Generator):** P > 0 = Einspeisung; Q < 0 = Aufnahme von
  Blindleistung (induktiv, untererregt), Q > 0 = Abgabe (kapazitiv, übererregt)
- **Externes Netz:** P, Q > 0 = Bezug aus dem vorgelagerten Netz, < 0 = Rückspeisung

## Grenzen

- Der Netzplan ist für einen Strang ausgelegt; bei verzweigten Netzen stimmen die
  Tabellen, aber die Zeichnung kann sich überlagern.
- Konvergiert eine Variante nicht, wird das in der Abgabe vermerkt und die
  übrigen Varianten werden trotzdem berechnet.
