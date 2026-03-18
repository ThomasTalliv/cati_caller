# James PM

Lokalt projektledelsesværktøj der læser direkte fra dine ROADMAP.md filer.

## Installation

```bash
pip install -r requirements.txt
```

## Start

```bash
python main.py
```

Åbn i browser: http://localhost:8000

## Konfiguration

Som standard læser James PM fra:
```
/Users/thomasciliushansen/Documents/Claude/01 Projekter/
```

Brug env-variabel til at ændre stien:
```bash
JAMES_PM_BASE_PATH="/din/sti/her" python main.py
```

## Features

- **Dashboard** — projektoverblik, dagens fokus, kritiske afhængigheder
- **GTD Kanban** — drag-and-drop board med Inbox / Next Actions / Waiting For / Done
- **Projekt-detalje** — milestones, WBS-træ, inline redigering, beslutningslog
- **Brainstorm modal** — `Cmd+B` åbner hurtig-input til Inbox eller Next Actions

## Filstruktur

```
james-pm/
├── main.py          # FastAPI app
├── parser.py        # Markdown parser
├── writer.py        # Atomic filskrivning
├── config.py        # Konfiguration
├── requirements.txt
└── static/
    ├── index.html   # Dashboard
    ├── gtd.html     # GTD Kanban
    ├── project.html # Projekt-detalje
    ├── style.css
    └── app.js
```
