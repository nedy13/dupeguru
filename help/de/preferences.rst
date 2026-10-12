Einstellungen
=============

Einige neuere Einstellungen sind noch nicht ins Deutsche übersetzt. Die Oberfläche zeigt sie auf
Englisch, deshalb sind sie hier ebenfalls auf Englisch angegeben.

**Folgende Tags scannen:**
    Beim Scantyp **Tags** wählen Sie hier, welche Tags verglichen werden.

**Wortgewichtung:**
    Siehe :ref:`word-weighting`.

**Gleiche ähnliche Wörter ab:**
    Siehe :ref:`similarity-matching`.

**Gleiche Bilder mit unterschiedlicher Auflösung ab:**
    Ist diese Box gewählt, dürfen Bilder unterschiedlicher Abmessungen in derselben Duplikatgruppe
    sein.

**Match pictures of different rotations:**
    Ist diese Box gewählt, dürfen unterschiedlich gedrehte Bilder in derselben Duplikatgruppe sein.

    Diese beiden Optionen gibt es nur für den Scan nach Bildblöcken. Der Scantyp
    :ref:`exact-picture-scan` findet nur Bilder mit denselben Pixeln.

**Relative path scan: also compare modification times, tolerance:**
    Nur für den Scantyp :ref:`relative-path-scan`. Ist diese Box gewählt, sind zwei Dateien mit
    gleichem Pfad und gleicher Größe nur dann Duplikate, wenn sich ihre Änderungszeiten höchstens um
    die angegebene Zahl von Sekunden unterscheiden. Die voreingestellte Toleranz von 2 Sekunden
    deckt Laufwerke ab, die die Zeit nicht genau speichern (FAT, exFAT, manche Netzlaufwerke).
    Standardmäßig ist die Option aus, weil das Kopieren einer Datei oft ihre Änderungszeit ändert,
    Einzelheiten unter :ref:`relative-path-scan`.

.. _filter-hardness:

**Filter Empfindlichkeit:**
    Die Schwelle, ab der zwei Dateien als Duplikate gelten. Ein niedrigerer Wert ergibt mehr
    Duplikate. Was die Schwelle bedeutet, hängt vom Scantyp ab (siehe :doc:`scan`). Sie gilt nur für
    :ref:`wortbasierte Scans <worded-scan>` und :ref:`Bildblöcke <picture-blocks-scan>`.

**Dateitypen dürfen gemischt werden:**
    Ist diese Box gewählt, dürfen Duplikatgruppen Dateien mit unterschiedlichen Dateiendungen
    enthalten. Ist sie es nicht, dann eben nicht!

**Ignoriere Duplikate mit Hardlinks auf dieselbe Datei:**
    Ist diese Option aktiviert, prüft dupeGuru, ob Duplikate auf denselben `Inode`_ verweisen. Ist
    das der Fall, gelten sie nicht als Duplikate. (Nur für macOS und Linux)

**Nutze reguläre Ausdrücke beim Filtern:**
    Ist diese Box gewählt, behandelt die Filterfunktion Ihre Eingabe als **regulären Ausdruck**. Sie
    zu erklären, würde den Rahmen dieser Dokumentation sprengen. Ein guter Einstieg ist
    `regular-expressions.info`_.

**Entferne leere Ordner beim Löschen oder Verschieben:**
    Ist diese Option aktiviert, wird ein Ordner gelöscht, wenn er nach dem Löschen oder Verschieben
    einer Datei leer ist.

**Kopieren und Verschieben:**
    Bestimmt, wie sich die Aktionen Kopieren und Verschieben (im Menü Aktionen) verhalten.

* **Direkt ins Ziel:** Alle Dateien landen direkt im gewählten Ziel, ohne dass der Quellpfad
  nachgebildet wird.
* **Relativen Pfad neu erstellen:** Der Pfad der Quelldatei wird im Zielordner nachgebildet, bis zum
  Ordner, der in der Ordnerliste ausgewählt ist. Haben Sie zum Beispiel ``/Users/foobar/SomeFolder``
  zur Ordnerliste hinzugefügt und verschieben ``/Users/foobar/SomeFolder/SubFolder/SomeFile.ext``
  nach ``/Users/foobar/MyDestination``, ist das endgültige Ziel der Datei
  ``/Users/foobar/MyDestination/SubFolder`` (``SomeFolder`` wurde vom Quellpfad abgetrennt).
* **Absoluten Pfad neu erstellen:** Der Pfad der Quelldatei wird im Zielordner vollständig
  nachgebildet. Verschieben Sie zum Beispiel ``/Users/foobar/SomeFolder/SubFolder/SomeFile.ext``
  nach ``/Users/foobar/MyDestination``, ist das endgültige Ziel der Datei
  ``/Users/foobar/MyDestination/Users/foobar/SomeFolder/SubFolder``.

In allen Fällen löst dupeGuru Namenskonflikte, indem es dem Dateinamen eine Nummer voranstellt, wenn
der Name im Ziel bereits existiert.

**Eigener Befehl:**
    Diese Einstellung bestimmt den Befehl, der durch "Eigenen Befehl ausführen" aufgerufen wird. So
    können Sie jede externe Anwendung starten. Das ist zum Beispiel nützlich, wenn Sie ein gutes
    Vergleichsprogramm (diff) installiert haben.

Der Befehl hat dasselbe Format wie in einer Kommandozeile, mit zwei Platzhaltern: **%d** und **%r**.
Sie werden durch den Pfad des ausgewählten Duplikats (%d) und den Pfad seiner Referenzdatei (%r)
ersetzt.

Enthält der Pfad Ihres Programms Leerzeichen, setzen Sie ihn in Anführungszeichen "". Auch die
Platzhalter sollten Sie in Anführungszeichen setzen, denn die Pfade der Duplikate und Referenzen
können ebenfalls Leerzeichen enthalten. Hier ein Beispiel::

    "C:\Program Files\SuperDiffProg\SuperDiffProg.exe" "%d" "%r"

Fortgeschritten
---------------

Diese Einstellungen sind für erfahrene Benutzer oder sehr spezielle Situationen. Die meisten
Benutzer müssen sie nicht ändern.

**Include existence check after scan completion:**
    Prüft nach dem Scan, ob die Dateien jeder Übereinstimmung noch existieren, und lässt die aus,
    die inzwischen gelöscht oder verschoben wurden. Ein langer Inhalts-Scan kann Stunden dauern, und
    in dieser Zeit können Dateien verschwinden. Diese Prüfung muss jede Datei erneut ansehen, was auf
    Netzlaufwerken langsam ist. Beim Scantyp :ref:`relative-path-scan`, der die Dateien erst Sekunden
    vorher auflistet, findet sie nie statt.

**Ignore difference in mtime when loading cached digests:**
    Der Hash-Cache bewahrt den Hash jeder Datei zusammen mit ihrem Pfad, ihrer Größe und ihrer
    Änderungszeit auf. Normalerweise wird eine Datei, deren Änderungszeit sich geändert hat, erneut
    gelesen. Mit dieser Option wird ein gespeicherter Hash genutzt, solange Pfad und Größe gleich
    sind. Nutzen Sie sie nur, wenn Sie wissen, dass sich der Inhalt nicht geändert hat, zum Beispiel
    nachdem ein Programm Dateien neue Änderungszeiten gegeben hat, ohne sie zu verändern.

.. _scan-workers:

**Parallel scan workers:**
    Wie viele Dateien gleichzeitig gehasht und wie viele Bilder gleichzeitig analysiert werden.
    **Automatic** nutzt alle Prozessorkerne Ihres Computers zum Dekodieren und Analysieren der
    Bilder, und zum Hashen von Dateien etwas mehr gleichzeitige Lesevorgänge, als es Kerne gibt. Auf
    Computern mit zwei Kernen oder weniger scannt dupeGuru mit einem einzigen Thread. Stellen Sie
    **1** ein, um immer mit einem Thread zu scannen, zum Beispiel damit der Computer während eines
    langen Scans gut bedienbar bleibt, oder eine Zahl, um höchstens so viele gleichzeitig zu nutzen.
    Viele gleichzeitige Lesevorgänge sind auf SSDs am schnellsten; auf einer einzelnen Festplatte
    kann eine kleine Zahl schneller sein.

.. _Inode: https://de.wikipedia.org/wiki/Inode
.. _regular-expressions.info: http://www.regular-expressions.info
