Der Scanvorgang
===============

.. contents::

dupeGuru hat 3 grundlegende Arten zu scannen: :ref:`worded-scan`, :ref:`contents-scan` und
:ref:`Bildblöcke <picture-blocks-scan>`. Die ersten beiden sind für den Standard- und den Musikmodus,
die letzte für den Bildmodus. Der Scanvorgang wird über die :doc:`Einstellungen <preferences>`
konfiguriert.

Daneben gibt es einige spezialisierte Scantypen: :ref:`relative-path-scan` im Standardmodus, der
Dateien vergleicht, ohne sie zu lesen, sowie **EXIF Zeitstempel** und :ref:`exact-picture-scan` im
Bildmodus.

.. _worded-scan:

Wortbasierte Scans
------------------

Wortbasierte Scans entnehmen jeder Datei eine Zeichenkette und zerlegen sie in Wörter. Die
Zeichenkette kann aus zwei Quellen stammen: **Dateiname** oder **Tags** (nur im Musikmodus).

Stammt sie aus Musik-Tags, müssen wir wählen, welche Tags genutzt werden. Wählen wir zum Beispiel
die Tags *Interpret* und *Titel*, erhalten wir Zeichenketten wie
"The White Stripes - Seven Nation Army".

Die Wörter werden an Leerzeichen getrennt, alle Satzzeichen werden entfernt (manche werden durch
Leerzeichen ersetzt, manche durch nichts) und alle Wörter kleingeschrieben. Die Zeichenkette
"This guy's song(remix)" ergibt zum Beispiel *this*, *guys*, *song* und *remix*.

Danach beginnt der eigentliche Vergleich. Duplikate zu finden heißt nur noch herauszufinden, wie
viele Wörter zwei Zeichenketten gemeinsam haben. Ist die :ref:`Filterempfindlichkeit
<filter-hardness>` zum Beispiel ``80``, müssen 80% der Wörter zweier Zeichenketten übereinstimmen.
Um den Übereinstimmungsanteil zu bestimmen, zählt dupeGuru zuerst die Gesamtzahl der Wörter
**beider** Zeichenketten, dann die übereinstimmenden Wörter (jedes zählt als 2), und teilt die Zahl
der übereinstimmenden Wörter durch die Gesamtzahl. Ist das Ergebnis größer oder gleich der
Filterempfindlichkeit, haben wir ein Duplikat. Zum Beispiel haben "a b c d" und "c d e" einen
Übereinstimmungsanteil von 57 (4 übereinstimmende Wörter, insgesamt 7 Wörter).

Felder
^^^^^^

Dateinamen von Musikstücken bestehen oft aus mehreren, getrennten Teilen, und das kann Probleme
machen. Nehmen wir zum Beispiel diese beiden Stücke: "Dolly Parton - I Will Always Love You" und
"Whitney Houston - I Will Always Love You". Es sind eindeutig nicht dieselben Stücke (sie stammen von
verschiedenen Interpreten), trotzdem haben sie eine Übereinstimmung von 71%! Mit einem einfachen
Scanverfahren würden wir diese Stücke also als Falschpositive erhalten, sobald wir die Schwelle etwas
senken, um gründlicher nach Duplikaten zu suchen.

Deshalb gibt es das Konzept der "Felder". Felder werden durch Bindestriche (``-``) getrennt. Beim
Scantyp "Dateiname - Felder" wird jedes Feld einzeln verglichen. Die endgültige Übereinstimmung ist
die niedrigste aller Felder. In unserem Beispiel stimmt der Titel zu 100% überein, der Interpret aber
zu 0%, die endgültige Übereinstimmung ist also 0.

Manchmal sind die Dateinamen nicht ganz einheitlich, sodass wir zum Beispiel
"The White Stripes - Seven Nation Army" und "Seven Nation Army - The White Stripes" haben. Dafür gibt
es den Scantyp "Dateiname - Felder (keine Reihenfolge)". Hier wird jedes Feld mit jedem anderen
verglichen und die höchste Übereinstimmung behalten. Die endgültige Übereinstimmung ist dann wieder
die niedrigste von allen. In unserem Fall ist sie 100.

Hinweis: Jedes Feld wird nur einmal genutzt. Deshalb haben "The White Stripes - The White Stripes"
und "The White Stripes - Seven Nation Army" eine Übereinstimmung von 0: Das zweite
"The White Stripes" kann nicht mit dem ersten Feld des anderen Namens verglichen werden, weil dieses
bereits durch das erste Feld "verbraucht" ist.

Der Scan nach *Tags* arbeitet immer mit Feldern. Bei dieser Scanmethode wählen wir außerdem, welche
Tags verglichen werden, und jeder Tag ist ein Feld.

.. _word-weighting:

Wortgewichtung
^^^^^^^^^^^^^^

Ist diese Option aktiviert, ändert sich die Berechnung der Übereinstimmung leicht: Längere Wörter
zählen mehr. Statt mit dem Wert 1 zählt jedes Wort bei den übereinstimmenden Wörtern und der
Gesamtzahl mit der Zahl seiner Buchstaben. Mit Wortgewichtung haben "ab cde fghi" und "ab cde fghij"
eine Übereinstimmung von 53% (insgesamt 19 Buchstaben, 10 übereinstimmende Buchstaben: 4 für "ab"
und 6 für "cde").

.. _similarity-matching:

Ähnliche Wörter
^^^^^^^^^^^^^^^

Ist diese Option aktiviert, zählen ähnliche Wörter als Übereinstimmung. Zum Beispiel haben
"The White Stripes" und "The White Stripe" damit eine Übereinstimmung von 100 statt 66.

Zwei Wörter gelten als ähnlich, wenn sie sich mit wenigen Bearbeitungsschritten (einen Buchstaben
entfernen, einen hinzufügen usw.) angleichen lassen. Das Verfahren ähnelt der
`Levenshtein-Distanz`_. Für technisch Interessierte: Genutzt wird Pythons `get_close_matches`_ mit
einer Schwelle von ``0.8``.

**Warnung:** Nutzen Sie diese Option mit Vorsicht. Wahrscheinlich erhalten Sie damit viele
Falschpositive in Ihren Ergebnissen. Dafür finden Sie Duplikate, die Sie sonst nicht gefunden hätten.
Außerdem ist der Scan mit dieser Option deutlich langsamer.

.. _contents-scan:

Inhalts-Scans
-------------

Inhalts-Scans sind viel einfacher als wortbasierte Scans. Wir lesen die Dateien, und ist der Inhalt
exakt gleich, gelten die beiden Dateien als Duplikate.

Das dauert natürlich deutlich länger als der Vergleich von Dateinamen. Um nicht unnötig ganze Dateien
zu lesen, schauen wir zuerst auf die Dateigrößen. Nachdem die Dateien nach Größe gruppiert sind,
verwerfen wir jede Datei, die allein in ihrer Gruppe ist. Erst dann lesen wir den Inhalt der übrigen
Dateien.

Zum Vergleich der Inhalte werden Hashes berechnet. Es ist zwar bekannt, dass sich Dateien mit
gleichem MD5-Hash leicht fälschen lassen, aber eine solche Datei muss absichtlich gefälscht sein. Die
Wahrscheinlichkeit, dass zwei Dateien zufällig denselben Hash *und* dieselbe Größe haben, ist
verschwindend gering.

Die :ref:`Filterempfindlichkeit <filter-hardness>` wird bei diesem Scan ignoriert.

Das Lesen der Dateien braucht bei diesem Scan die meiste Zeit, und dupeGuru liest mehrere Dateien
gleichzeitig. Auf schnellen Laufwerken (SSDs, besonders NVMe-Laufwerke) macht das den Scan um ein
Vielfaches schneller. Auf einer Festplatte, deren Lesekopf beim gleichzeitigen Lesen vieler Dateien
hin und her springen muss, hilft es weniger. Siehe :ref:`scan-workers`.

Die Hashes werden in einem Zwischenspeicher (dem "Hash-Cache") aufbewahrt. Solange eine Datei
dieselbe Größe und Änderungszeit hat, wird sie beim nächsten Scan nicht erneut gelesen.

Ordner
^^^^^^

Dies ist ein besonderer Inhalts-Scan. Er funktioniert wie ein normaler Inhalts-Scan, sucht aber
statt doppelter Dateien nach doppelten Ordnern. Ein Ordner ist ein Duplikat eines anderen, wenn alle
seine Dateien denselben Inhalt haben wie die Dateien des anderen Ordners.

Dieser Scan ist natürlich rekursiv, Unterordner werden mitgeprüft. dupeGuru behält nur die größten
Fische: Enthalten zwei übereinstimmende Ordner Unterordner, erscheinen diese Unterordner nicht
zusätzlich in den Ergebnissen.

In diesem Modus erhalten wir Ordner statt Dateien als Ergebnisse.

.. _relative-path-scan:

Relativer Pfad und Größe
------------------------

Dieser Scantyp im Standardmodus ist für eine Aufgabe gemacht: die Kopie eines Ordners mit ihrem
Original zu vergleichen, zum Beispiel eine Sicherung auf einem NAS. Zwei Dateien sind Duplikate, wenn
sie unterhalb des Ordners, in dem sie gefunden wurden, denselben Pfad haben und gleich groß sind.
Keine Datei wird gelesen, nur die Ordner werden aufgelistet. Das macht diesen Scan sehr schnell,
auch über das Netzwerk. Der Vergleich zweier Kopien einer großen Fotosammlung (je etwa 85.000
Dateien, eine davon auf einem NAS) dauert etwa so lange wie das Auflisten der Ordner, ein paar
Sekunden.

Angenommen, Sie haben ``/mnt/nas/Fotos`` und ``/home/ich/Fotos`` zu Ihrer Ordnerliste hinzugefügt.
Dann sind ``/mnt/nas/Fotos/2015/Urlaub/IMG_1234.JPG`` und ``/home/ich/Fotos/2015/Urlaub/IMG_1234.JPG``
Duplikate, wenn sie gleich groß sind. ``/home/ich/Fotos/2016/IMG_1234.JPG`` ist es nicht, selbst bei
gleichem Namen und gleicher Größe, weil die Datei in einem anderen Ordner liegt. Die Ordner, die Sie
zur Ordnerliste hinzufügen, müssen deshalb in beiden Kopien auf derselben Ebene liegen:
``/mnt/nas/Fotos`` und ``/home/ich/Fotos`` funktionieren, ``/mnt/nas`` und ``/home/ich/Fotos`` nicht,
weil die Pfade dann nur auf einer Seite mit ``Fotos/`` beginnen würden. Die Pfade werden exakt
verglichen, auch Groß- und Kleinschreibung.

Optional können auch die Änderungszeiten verglichen werden (siehe :doc:`preferences`), mit einer
Toleranz von einigen Sekunden. Lassen Sie diese Option aus, solange Sie sie nicht brauchen: Die
Änderungszeit einer Kopie ist oft nicht die ihres Originals, obwohl der Inhalt gleich ist. Manche
Arten des Kopierens setzen sie auf den Zeitpunkt der Kopie, FAT- und exFAT-Laufwerke (USB-Sticks,
SD-Karten) speichern sie nur auf 2 Sekunden genau und in Ortszeit, was sie um eine Stunde verschieben
kann, und manche Netzlaufwerke runden sie auf die Sekunde.

Zusammen mit einem Referenzordner ist dieser Scantyp der schnellste Weg, die
:doc:`in einer Kopie fehlenden Dateien <missing>` zu finden. Natürlich verrät er nicht, ob der Inhalt
zweier Dateien mit gleichem Pfad und gleicher Größe wirklich gleich ist. Wenn Sie das sicher wissen
müssen, nutzen Sie stattdessen einen :ref:`Inhalts-Scan <contents-scan>`.

Die :ref:`Filterempfindlichkeit <filter-hardness>` wird bei diesem Scan ignoriert.

.. _picture-blocks-scan:

Bildblöcke
----------

Der Bildmodus von dupeGuru unterscheidet sich deutlich von seinen beiden Geschwistern. Seine
Scantypen sind völlig anders. Der erste ist sein Scan "Inhalt", was etwas zu allgemein ist, deshalb
nennen wir ihn hier "Bildblöcke".

Zuerst öffnen wir jedes Bild als RGB-Bitmap und zerlegen es in Blöcke: Wir legen ein 15x15-Raster
darüber und berechnen die durchschnittliche Farbe jeder Rasterzelle. Das ist die Phase der
"Bildanalyse". Sie ist sehr zeitaufwendig, deshalb wird ihr Ergebnis in einer Datenbank (dem
"Bild-Cache") gespeichert.

Danach können wir die Bilder vergleichen. Jede Rasterzelle (eine Durchschnittsfarbe) wird mit der
entsprechenden Zelle des anderen Bildes verglichen und ein Farbunterschied berechnet (einfach die
Summe der Unterschiede von R, G und B). Alle diese Summen werden zu einer Gesamtpunktzahl addiert.

Ist diese Punktzahl kleiner oder gleich ``100 - Schwelle``, haben wir eine Übereinstimmung.

Eine Schwelle von 100 verlangt zusätzlich, dass die Bilder exakt gleich sind. Durch die
Durchschnittsbildung kann der Vergleich der Zellen nämlich auch für Bilder ``0`` ergeben, die nicht
exakt gleich sind. Weil "100%" aber "exakt gleich" nahelegt, verwerfen wir diese Fälle. Wenn Sie sehr,
sehr ähnliche Bilder finden, aber kleine Unterschiede zulassen möchten, wählen Sie 99%.

Dieser zweite Teil des Scans ist rechenintensiv und kann einige Zeit dauern. Er wurde für
Mehrkern-Prozessoren gebaut und so gut wie möglich optimiert. Wegen der Unschärfe der Aufgabe müssen
wir aber trotzdem jedes Bild mit jedem anderen vergleichen, der Aufwand wächst also quadratisch (ist
``N`` die Zahl der zu vergleichenden Bilder, sind ``N*N`` Vergleiche nötig).

Beide Teile des Scans laufen gleichzeitig auf allen Prozessorkernen Ihres Computers: Die Bilder
werden in mehreren Prozessen analysiert, und ebenso werden sie verglichen. Auf einem Computer mit
vielen Kernen macht das den Scan um ein Vielfaches schneller. Siehe :ref:`scan-workers`.

Dieser Algorithmus ist sehr einfach, funktioniert in der Praxis aber recht gut. Wenn Sie einen
besseren Algorithmus kennen und dupeGuru verbessern möchten, melden Sie sich!

EXIF Zeitstempel
----------------

Dieser ist einfach. Wir lesen die EXIF-Informationen jedes Bildes und entnehmen den Tag
``DateTimeOriginal``. Ist dieser Tag bei zwei Bildern gleich, gelten sie als Duplikate.

**Warnung:** Bearbeitete Bilder behalten oft denselben EXIF-Zeitstempel, achten Sie bei diesem
Scantyp also auf Falschpositive.

.. _exact-picture-scan:

Exaktes Bild (Metadaten ignorieren)
-----------------------------------

Fotoprogramme schreiben Stichwörter, Bewertungen, Beschreibungen oder den Autor oft in die Bilddatei
selbst (als EXIF-, IPTC- oder XMP-Metadaten). Danach ist die Datei nicht mehr dieselbe, ein
:ref:`Inhalts-Scan <contents-scan>` findet sie also nicht mehr, obwohl sich das Bild überhaupt nicht
geändert hat. Und :ref:`Bildblöcke <picture-blocks-scan>` sind unscharf: Sie finden Bilder, die sich
ähneln. Das ist nicht, was Sie wollen, wenn Sie wissen müssen, ob *genau dieses Bild* in Ihrer
Sammlung ist.

Dieser Scantyp vergleicht die Bilder selbst, Pixel für Pixel, und ignoriert alles andere. Wir
dekodieren jedes Bild, drehen es so, wie die Kamera es in der EXIF-Ausrichtung festgehalten hat, und
berechnen einen Hash aus seinen Abmessungen und Pixeln. Zwei Bilder mit demselben Hash sind
Duplikate. Also:

* Ein Bild, dessen Stichwörter, Bewertung, Kommentar, eingebettete Vorschau oder sonstige Metadaten
  geändert wurden, ist ein Duplikat des Originals.
* Ein Bild, das verkleinert, beschnitten, (in seinen Pixeln) gedreht, bearbeitet oder erneut als JPEG
  gespeichert wurde, selbst mit derselben Qualität, ist **kein** Duplikat. Die JPEG-Kompression
  verändert die Pixel bei jedem Speichern ein wenig.

Wie die Analyse der Bildblöcke geschieht das Dekodieren der Bilder in mehreren Prozessen gleichzeitig
(siehe :ref:`scan-workers`), und das Ergebnis wird im Hash-Cache aufbewahrt. Weitere Scans derselben
Bilder gehen deshalb fast sofort. Weil Bilder mit gleichem Hash einfach zusammengefasst werden, gibt
es keine Vergleichsphase: Bei großen Sammlungen ist dieser Scan viel schneller als Bildblöcke.

Bilder, die nicht dekodiert werden können, bleiben beim Scan außen vor und haben deshalb nie ein
Duplikat.

Die :ref:`Filterempfindlichkeit <filter-hardness>` und die Einstellungen "Gleiche Bilder mit
unterschiedlicher Auflösung ab" und "Gleiche unterschiedlich gedrehte Bilder ab" werden bei diesem Scan
ignoriert.

.. _Levenshtein-Distanz: https://de.wikipedia.org/wiki/Levenshtein-Distanz
.. _get_close_matches: https://docs.python.org/3/library/difflib.html#difflib.get_close_matches
