# Aim-n-Fire Rotary Stick – Nachbau

Quelle: `models/rotary_stick.py` (alle Maße parametrisch, oben im Skript).
Neu erzeugen: `python models/rotary_stick.py`, Bilder: `python scripts/render_rotary.py` (siehe README).

## Druckteile (STL liegen schon in Druckorientierung vor)

| Datei | Taito-Pos. | Hinweis |
|---|---|---|
| grundplatte.stl | 32 (+5/6/7) | Platte auf dem Bett, keine Stützen. PETG, 4 Wände, 40 % Infill |
| rotor.stl | 27 + 12 | Rastrad und Nocke in einem Teil. 100 % Infill oder 6 Wände |
| schalterdeck.stl | 26 + 16 | Oberseite auf dem Bett, Fire-Lasche wächst nach oben |
| knopf.stl | 1 | Unterseite auf dem Bett |
| knopf_inlay.stl | 31 | Pfeil ist 0,6 mm vertieft, zum Ausmalen, oder mit Farbwechsel drucken |
| scheibe.stl | 3 | Gleitscheibe zwischen Panel und Knopf |

## Kaufteile

Die vollständige Stückliste mit Positionsnummern steht auf der Zeichnung `zeichnung_baugruppe.pdf`.

- Achse Ø8 (Parameter `SHAFT_D`), Länge ≥ **78 mm** bei 3 mm Panel (+1 mm pro mm Panel)
- 5× Microtaster, Standardgröße (Omron V), 4× Richtung + 1× Fire
- 1× Kugeldruckstück M8 + 1× Mutter ISO 4032 M8 (Parameter `PLUNGER_*`, `BALL_D`)
- 1× Druckfeder, Außen-Ø ≤ 11,5, Innen-Ø ≥ 8,5, L0 ≈ 18–20 mm, weich
- 1× Scheibe ISO 7089 8,4 (8,4 × 16 × 1,6) zwischen Rotor und Lagerbuchse (Taito Pos. 28)
- 10× Linsenschraube ISO 7045 M3×20 (Taster), 4× M3×10 (Deck an Säulen, selbstschneidend)
- 24× Scheibe ISO 7089 3,2 (je unter Schraubenkopf und Mutter, dazu 4 unter den Deckschrauben)
- 13× Mutter ISO 4032 M3 (10 Taster + 3 Madenschrauben)
- 3× Gewindestift ISO 4026 M3×10 (2× Rotor, 1× Knopf)

## Montage

1. M8-Mutter von unten in den Schlitz des Halteblocks schieben, Kugeldruckstück von außen eindrehen, aber noch nicht bis an den Rotor.
2. Achse von oben durch die Grundplatte stecken, zuerst die Scheibe 8,4, dann den Rotor (Rastrad oben) aufschieben. Rastkerbe 0° zeigt zum Kugeldruckstück. Rotor an die Lagerbuchse schieben, Madenschrauben anziehen.
3. Feder in die Tasche unten im Rotor stecken, Schalterdeck aufsetzen und an die 4 Säulen schrauben.
4. 4 Taster flach auf die Sockel des Decks legen (Schraube von oben mit Scheibe, unten Scheibe + Mutter), **Hebelspitze zur Nocke hin** (siehe `vorschau_schaltlogik.png`). In den Langlöchern so justieren, dass jeder Taster auf dem Nocken klickt, auf dem Grundkreis aber nicht (Schaltfenster ≈ 3,7 mm).
5. Fire-Taster an die Lasche schrauben, Hebel unter das Achsende. Höhe so einstellen, dass er nach ca. 1,5 mm Druckweg auslöst (Anschlag bei 3 mm).
6. Kugeldruckstück eindrehen, bis die Klicks sauber sind, dann mit mittelfester Schraubensicherung sichern.
7. Scheibe und Knopf aufsetzen, Pfeil zur gewünschten Richtung ausrichten, Madenschraube anziehen.

## Schaltlogik (Taster 0 = Kugelseite +X, dann 90° gegen den Uhrzeigersinn)

| Stellung | 0° | 45° | 90° | 135° | 180° | 225° | 270° | 315° |
|---|---|---|---|---|---|---|---|---|
| Taster | 0 | 0+1 | 1 | 1+2 | 2 | 2+3 | 3 | 3+0 |

Die Stellungen verhalten sich wie ein 8-Wege-Joystick. Die Taster lassen sich direkt als Hoch/Rechts/Runter/Links an ein Encoder-Board anschließen.

## Vor dem Druck prüfen

- Achs-Ø und -länge
- Gewinde und Kugel-Ø des Kugeldruckstücks
- Lochabstand der Taster: Parameter `SW_HOLE_FROM_BOTTOM` (5,1 mm) nachmessen
- Befestigungslöcher für das Panel: `PLATE_HOLE_POS`
