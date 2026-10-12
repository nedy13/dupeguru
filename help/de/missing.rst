In der Referenz fehlende Dateien
================================

.. contents::

Normalerweise wird dupeGuruX genutzt, um Dateien zu finden, die doppelt vorhanden sind. Manchmal ist
die Frage aber genau umgekehrt: Sie haben eine Sicherung, eine Fotosammlung auf einem NAS oder ein
sortiertes Archiv und möchten wissen, ob alle Dateien von einem anderen Ort darin enthalten sind.
Gesucht sind dann die Dateien, die **kein** Duplikat haben. Genau diese zeigt das Fenster
**In der Referenz fehlende Dateien**.

Einige typische Fälle:

* Sie haben die Fotos Ihres Handys über die Jahre in Ihre Fotosammlung kopiert, sind sich aber nicht
  sicher, ob alle dabei sind, bevor Sie das Handy zurücksetzen.
* Sie haben eine Kopie eines Ordners auf einer anderen Festplatte und möchten prüfen, ob die Kopie
  vollständig ist.
* Sie haben Bilder in eine neue Ordnerstruktur einsortiert und möchten die vergessenen finden.

Funktionsweise
--------------

Setzen Sie den Ordner, der alles enthalten soll (die Sicherung, die Sammlung), in den Zustand
**Referenz** (siehe :doc:`folders`). Die Ordner, die Sie prüfen möchten, bleiben im Zustand
**Normal**. Dann starten Sie den Scan wie gewohnt.

Nach dem Scan **fehlt** jede Datei eines normalen Ordners **in der Referenz**, die nicht zusammen
mit einer Datei eines Referenzordners in einer Duplikatgruppe gelandet ist. Dabei gelten einige
Regeln:

* Alle Referenzordner zählen zusammen als eine Referenz. Haben Sie drei Referenzordner, fehlt eine
  Datei nicht, sobald sie in irgendeinem davon ein Duplikat hat.
* Duplikate innerhalb der normalen Ordner spielen keine Rolle. Gibt es eine Datei zweimal in Ihren
  normalen Ordnern, aber nicht in der Referenz, fehlen beide Exemplare.
* Es zählen nur Übereinstimmungen, die in den Ergebnissen landen. Was ein Duplikat ist, hängt vom
  Scantyp und seinen Einstellungen ab. Mit einer niedrigen
  :ref:`Filterempfindlichkeit <filter-hardness>` kann eine Datei in der Referenz ein "Duplikat"
  haben, das ihr nur ähnlich ist, und wird dann nicht als fehlend angezeigt. Mit einer hohen wird
  eine Datei angezeigt, die zwar in der Referenz liegt, dort aber leicht verändert ist.
  Übereinstimmungen, die durch die Ausnahme-Liste oder die Einstellung "Dateitypen dürfen gemischt
  werden" wegfallen, zählen ebenfalls nicht.
* Dateien, die wegen der Einstellungen "Ignoriere Dateien kleiner als" und "Ignoriere Dateien größer
  als" gar nicht verglichen werden, erscheinen nie in der Liste. dupeGuruX kann nicht wissen, ob sie
  fehlen oder nicht.
* Dateien, die nicht gelesen werden können (zum Beispiel ein beschädigtes Bild), können kein
  Duplikat haben und erscheinen deshalb als fehlend.

Die Wahl des passenden Scantyps ist der wichtigste Schritt. Einige Empfehlungen:

* Um die Kopie eines Ordners zu prüfen (zum Beispiel eine Sicherung auf einem NAS), nutzen Sie
  :ref:`Relativer Pfad und Größe <relative-path-scan>` im Standardmodus. Dieser Scantyp liest keine
  Dateiinhalte und ist deshalb sehr schnell, auch über das Netzwerk.
* Um sicherzugehen, dass auch die Inhalte gleich sind, nutzen Sie **Inhalt** im Standardmodus. Dieser
  Scan liest jede Datei, was bei großen Sammlungen eine Weile dauert.
* Für Bilder, deren Metadaten (Stichwörter, Bewertungen, ...) an einem Ort bearbeitet wurden, am
  anderen aber nicht, nutzen Sie :ref:`Exaktes Bild (Metadaten ignorieren) <exact-picture-scan>` im
  Bildmodus.
* **Dateiname** ist für diese Aufgabe ungeeignet. Er vergleicht nur Namen, egal wo die Dateien
  liegen. Kameras vergeben Namen wie ``IMG_1234.JPG`` oder ``00001.MTS`` immer wieder, sodass eine
  fehlende Datei leicht von einer anderen Datei gleichen Namens verdeckt wird.

Das Fenster öffnen
------------------

Ist mindestens ein Referenzordner im Scan, hat das Ergebnisfenster neben **Details** einen Knopf
**Fehlt in Referenz**. Seine Beschriftung zeigt, wie viele Dateien fehlen. Sie können das Fenster
auch über das Menü **Ansicht** mit **In der Referenz fehlende Dateien** öffnen.

Findet der Scan überhaupt keine Duplikate, fehlen aber Dateien in der Referenz, fragt dupeGuruX, ob
Sie diese sehen möchten.

Die Liste wird laufend aktualisiert: Kopieren oder verschieben Sie Dateien aus diesem Fenster,
verschwinden sie aus der Liste, sobald sie nicht mehr fehlen.

Die Liste durchsehen
--------------------

Die Liste zeigt Dateiname, Ordner, Größe und Änderungszeit jeder fehlenden Datei. Ein Klick auf eine
Spaltenüberschrift sortiert die Liste.

**Nach Name oder Ordner filtern:**
    Zeigt nur die Dateien, deren Name oder Ordner den eingegebenen Text enthält. Groß- und
    Kleinschreibung spielen keine Rolle. Der Text über der Liste nennt die Zahl der angezeigten
    Dateien.
**Vorschau:**
    Ist diese Box gewählt, zeigt die Auswahl einer Datei diese in einem Vorschaufenster, zusammen
    mit ihren Eigenschaften (Größe, Datumsangaben, Abmessungen und bei Fotos der EXIF-Zeitstempel
    und die Kamera). Das geht viel schneller, als jede Datei mit einer anderen Anwendung zu öffnen.
    Im Vorschaufenster wechseln die Pfeiltasten und Bild auf/Bild ab zur vorherigen oder nächsten
    Datei der Liste, die **Leertaste** hakt die aktuelle Datei an oder ab und **Escape** schließt
    das Fenster.
**Öffne Auswahl mit Standard-Anwendung:**
    Öffnet die ausgewählten Dateien mit der Anwendung, die ihrem Dateityp zugeordnet ist. Ein
    Doppelklick auf eine Datei macht dasselbe, oder zeigt sie in der Vorschau, wenn die Box
    **Vorschau** gewählt ist.
**Öffne den Über-Ordner der Auswahl:**
    Öffnet den Ordner, der die ausgewählten Dateien enthält.

Dateien anhaken
---------------

Jede Datei hat ein Kästchen zum Anhaken. Die angehakten Dateien sind die Dateien, mit denen
**Kopieren / Verschieben** und **Als CSV exportieren** arbeiten. Sie haken eine Datei an, indem Sie auf ihr Kästchen
klicken, oder indem Sie sie auswählen und die **Leertaste** drücken (auch im Vorschaufenster). Der
Knopf **Anhaken** hat ein Menü, um alle angezeigten Dateien anzuhaken, alle Haken zu entfernen oder
die Haken der angezeigten Dateien umzukehren. Zusammen mit dem Filter können Sie so zum Beispiel
alle Dateien eines bestimmten Ordners mit wenigen Klicks anhaken.

Ist keine Datei angehakt, arbeitet **Kopieren / Verschieben** stattdessen mit den ausgewählten Dateien.

Die fehlenden Dateien kopieren oder verschieben
-----------------------------------------------

Der Knopf **Kopieren / Verschieben** bietet vier Aktionen:

**In die Referenz kopieren... / In die Referenz verschieben...:**
    Kopiert oder verschiebt die Dateien in einen Referenzordner. Sind mehrere Referenzordner in
    Ihrer Ordnerliste, werden Sie gefragt, welcher genutzt werden soll.
**In einen Ordner kopieren... / In einen Ordner verschieben...:**
    Kopiert oder verschiebt die Dateien in einen Ordner Ihrer Wahl.

In jedem Fall legt dupeGuruX die Unterordner der Datei unterhalb des Ordners, aus dem sie stammt,
neu an. Haben Sie zum Beispiel ``/home/ich/Handy`` und die Referenz ``/mnt/nas/Fotos`` gescannt,
wird die fehlende Datei ``/home/ich/Handy/2024/Urlaub/IMG_1234.JPG`` nach
``/mnt/nas/Fotos/2024/Urlaub/`` kopiert. Bevor etwas passiert, nennt dupeGuruX die Zahl der Dateien
und das Ziel und bittet Sie um Bestätigung.

Dateien werden nie überschrieben. Gibt es im Ziel bereits eine Datei mit demselben Namen, bekommt die
Kopie eine Nummer vor ihren Namen gestellt, etwa ``[000] IMG_1234.JPG``. Beim Verschieben bleibt die
Änderungszeit der Dateien erhalten. Beim Kopieren ebenfalls, soweit das Ziel es erlaubt.

Dateien, die in einen Referenzordner kopiert oder verschoben wurden, und Dateien, die irgendwohin
verschoben wurden, verschwinden aus der Liste. Dateien, die in einen anderen Ordner kopiert wurden,
bleiben in der Liste, denn sie fehlen weiterhin in der Referenz. Beim Verschieben gilt die
Einstellung "Entferne leere Ordner beim Löschen oder Verschieben" für die Ordner, die die Dateien
verlassen.

Die Liste exportieren
---------------------

**Als CSV exportieren** speichert die angehakten Dateien, oder alle angezeigten Dateien, wenn keine
angehakt ist, in eine CSV-Datei mit Name, Ordner, Größe und Änderungszeit. Diese Datei können Sie mit
einer Tabellenkalkulation öffnen oder als Aufgabenliste nutzen.
