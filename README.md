# OWUI-Ollama-Onenote-Import

Dieses Repository stellt folgendes bereit: Das Inhalte aus Microsoft OneNote über die Microsoft Graph API exportiert, als bereinigte Textdateien speichert und in einen lokalen Vektorstore (ChromaDB) einfügt. Die erzeugten Vektoren können anschließend in OpenWebUI genutzt werden, um einen Ollama-gestützten Wissenschatbot mit aktuellen OneNote-Inhalten zu betreiben.

## Funktionsübersicht

- **Gerätecode-Flow** über `msal`, damit sich der Nutzer ohne komplizierte Einrichtung authentifizieren kann.
- **Automatischer Abruf** aller OneNote-Abschnitte (Sections) inklusive ihrer Seiten.
- **HTML-Bereinigung** der OneNote-Inhalte zu gut lesbaren `.txt`-Dateien.
- **Ratenlimit-Pause**: Nach jeweils 600 Abschnitten wird automatisch für 5 Minuten pausiert.
- **Persistenter Vektorstore** mittels ChromaDB und Sentence-Transformer-Embeddings, wobei jeder Abschnitt separat eingebettet wird.
- **Einfache Integration** in OpenWebUI mit laufendem Ollama.

## Voraussetzungen

1. **Python 3.10 oder neuer**
2. Eine **Azure AD App-Registrierung** mit aktivierten Microsoft Graph Berechtigungen (`Notes.Read`).
3. Zugriff auf ein **OneNote-Konto**, dessen Inhalte exportiert werden sollen.
4. (Optional) Eine vorhandene **OpenWebUI + Ollama** Installation für die spätere Nutzung der Vektoren.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

## Azure AD vorbereiten

1. Melde dich im [Azure Portal](https://portal.azure.com/) an.
2. Erstelle unter „App-Registrierungen“ eine neue **öffentliche Client-App**.
3. Notiere dir die **Anwendungs-(Client-)ID** und den **Verzeichnis-(Tenant-)Bezeichner**.
4. Füge unter „API-Berechtigungen“ die **Microsoft Graph** Berechtigung `Notes.Read` (delegiert) hinzu und bestätige ggf. den Admin-Consent.
5. Gewährleiste, dass die App als **öffentlich (mobile & Desktop)** konfiguriert ist, damit der Gerätecode-Flow genutzt werden kann.

> ℹ️ Für produktive Szenarien kannst du zusätzliche delegierte Berechtigungen vergeben, z. B. `Notes.Read.All`, sofern dein Tenant dies benötigt. Die Authentifizierung erfolgt immer im Kontext des angemeldeten Benutzers.

## Client- und Tenant-ID verwalten

Die Skripte erwarten die Client- und Tenant-ID entweder als CLI-Parameter (siehe unten) oder über Umgebungsvariablen. Für eine dauerhafte Konfiguration kannst du sie z. B. in deiner Shell hinterlegen:

```bash
export ONENOTE_CLIENT_ID="<DEINE_CLIENT_ID>"
export ONENOTE_TENANT_ID="<DEIN_TENANT_ODER_COMMON>"
```

Der CLI-Aufruf kann diese Variablen direkt verwenden:

```bash
python scripts/import_onenote.py \
  --client-id "$ONENOTE_CLIENT_ID" \
  --tenant-id "$ONENOTE_TENANT_ID" \
  --output-dir data/sections \
  --vectorstore vectorstore \
  --collection onenote-sections
```

Alternativ können die IDs weiterhin manuell über die CLI-Argumente angegeben werden. Wichtig ist, dass sie zur zuvor angelegten Azure-App passen.

## Nutzung

```bash
python scripts/import_onenote.py \
  --client-id <DEINE_CLIENT_ID> \
  --tenant-id common \
  --output-dir data/sections \
  --vectorstore vectorstore \
  --collection onenote-sections
```

Der Gerätecode wird im Terminal angezeigt. Folge den Anweisungen, melde dich im Browser an und gib den Code ein. Der Export startet automatisch.

### CLI-Optionen

| Option | Beschreibung |
| --- | --- |
| `--client-id` | *Pflicht.* Client-ID der Azure-App. |
| `--tenant-id` | Azure Tenant (`common`, `organizations`, `consumers` oder spezifische GUID). |
| `--output-dir` | Ordner für die erzeugten `.txt`-Dateien. |
| `--vectorstore` | Speicherort für den persistierten ChromaDB Vektorstore. |
| `--collection` | Name der Chroma-Kollektion. |
| `--pause-after` | Anzahl Abschnitte vor einer Pause (Standard 600). |
| `--pause-seconds` | Dauer der Pause (Standard 300 Sekunden). |
| `--scopes` | Zusätzliche OAuth-Scopes, Standard `Notes.Read` + `offline_access`. |
| `--embedding-model` | SentenceTransformer-Modell (Standard `sentence-transformers/all-MiniLM-L6-v2`). |

## Arbeitsablauf im Überblick

1. **Authentifizierung**: Das Skript startet den Gerätecode-Flow. Nach erfolgreichem Login wird das Token automatisch gespeichert (`token_cache.json`).
2. **Abruf der Abschnitte**: Es werden nacheinander alle Sections (`/me/onenote/sections`) geladen. Für jede Section werden alle Seiten gelesen und zu einem Textblock zusammengeführt.
3. **Bereinigung & Speicherung**: Die HTML-Inhalte werden mit BeautifulSoup bereinigt und als UTF-8 Textdatei im Ausgabeverzeichnis gespeichert.
4. **Vektorisierung**: Jeder Abschnitt wird getrennt eingebettet und mitsamt Metadaten (`section_id`, `section_name`, `file_path`) in ChromaDB gespeichert.
5. **Ratenlimit-Pause**: Nach 600 Abschnitten pausiert das Skript 5 Minuten (konfigurierbar), um API-Grenzen einzuhalten.

## Integration in OpenWebUI + Ollama

1. **Ollama Modell vorbereiten**: Stelle sicher, dass Ollama läuft und die gewünschten Sprachmodelle verfügbar sind (`ollama run llama2`).
2. **OpenWebUI konfigurieren**:
   - Setze die Umgebungsvariable `OPENWEBUI_VECTOR_STORE_PATH` auf den Pfad deines `vectorstore` Ordners.
   - Starte OpenWebUI neu. Die ChromaDB-Kollektion `onenote-sections` steht nun als Wissensbasis zur Verfügung.
3. **Neues Wissen testen**: Lade in OpenWebUI den gewünschten Ollama-Chat. Aktiviere den Wissensmodus und wähle die `onenote-sections`-Kollektion aus.
4. **Aktualisierung**: Führe das Skript erneut aus, wenn sich deine OneNote-Daten geändert haben. Bestehende Einträge werden aktualisiert (Upsert), sodass keine doppelten Vektoren entstehen.

## Tipps für das Abschlussprojekt

- **Zeitplanung**: Die Entwicklung und Tests lassen sich in ca. 40 Arbeitsstunden bewältigen. Beginne mit der Einrichtung von Azure und dem Test des Gerätecode-Flows.
- **Fehlersuche**: Aktiviere ggf. das Logging (z. B. via `MSAL_VERBOSE=1`), um Authentifizierungsprobleme schnell zu finden.
- **Datenschutz**: Bewahre die exportierten Textdateien sicher auf. Erwäge, sensible Daten zu pseudonymisieren, bevor du sie in den Vektorstore einfügst.
- **Erweiterungen**: Du kannst zusätzliche Metadaten (z. B. Abschnitts-Notizbuch, Änderungsdatum) speichern, indem du die Metadaten im Skript erweiterst.

## Lizenz

Dieses Projekt steht unter der [MIT-Lizenz](LICENSE).
