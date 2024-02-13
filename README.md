
# Simulationsmodell für das Ladeverhalten von Elektromobilität

Dieses Repository enthält ein 'Simulationsmodell' mit 'python', mit dem das Ladeverhalten von Elektroautos an Ladestationen simuliert werden kann. Entwickelt wurde es im Rahmen meiner Bachelorarbeit an der HAW Hamburg.


# Szenarien in Notebooks
Im Verlauf der Arbeit wurde das 'Simulationsmodell' schrittweise um weitere Funktionen ergänzt, sowie entsprechende 'Szenarien' entwickelt und ausgewertet. Die Auswertung dieser Einstellungen auf den Lastverlauf findet in den entsprechenden Jupyter-Notebooks statt. Aus diesen Notebooks heraus wird die Simulation in [model_v2.py](model_v2.py) aufgerufen. Dabei wird für jedes Notebooks ein JSON-file mit den Benutzer-Einstellungen für die Simulation aufgerufen.

# finales Simulationsmodell
Das finaly Simulationsmodell befindet sich in [model_final.py](model_final.py). In dem Notebook [Simulation_final.ipynb](Simulation_final.ipynb) wird die Nutzung des finalen Simulationsmodells demonstriert. Die zugehörigen Benutzer-Einstellungen finden sich in [settings_final.json](settings_final.json).

# Hinzufügen von weiteren Ladekurven
In der Arbeit werden real gemessene Ladekurven von Elektroautos verwendet. Sollen zusätzlich weitere Modelle hinzugefügt werden, ist das Vorgehen in [Ladekurven_parquetfiles.ipynb](Ladekurven_parquetfiles.ipynb) erklärt.

# ausführliche Informationen
Ausführliche Informationen zur Methodik sind der Bachelorarbeit selbst zu entnehmen.