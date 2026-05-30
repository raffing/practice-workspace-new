# Practice Workspace

Un'app desktop moderna per gestire pratiche professionali, task e file collegati. Interfaccia minimale, shortcut da tastiera avanzate e tema automatico.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![PySide6](https://img.shields.io/badge/PySide6-6.6+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## ✨ Caratteristiche

- 🎨 Tema Light / Dark / Auto con rilevamento automatico del sistema
- 📝 Editor Markdown con syntax highlighting per pratiche, task, tag, persone e file
- 🌲 Pannello laterale per la navigazione di pratiche, task e allegati
- ⌨️ Shortcut avanzate per la gestione veloce dei contenuti
- 📂 Autocomplete per pratiche e file con navigazione da tastiera
- 🔗 Percorsi deterministici senza scansioni globali del filesystem
- 💾 Persistenza di tema, geometria finestra e ultimo workspace aperto

---

## 🚀 Installazione

```bash
# Clona il repository
git clone https://github.com/tuo-username/practice-workspace.git

cd practice-workspace

# Crea ambiente virtuale
python -m venv venv

# Attivazione Windows
venv\Scripts\activate

# Attivazione Linux/macOS
source venv/bin/activate

# Installa dipendenze
pip install -r requirements.txt

# Avvia applicazione
python main.py
```

### Dipendenze

| Pacchetto | Versione minima | Utilizzo |
|------------|----------------|-----------|
| PySide6 | 6.6.0 | GUI Qt |
| PyYAML | 6.0 | Metadati pratiche |
| darkdetect | 0.8.0 | Tema automatico |

---

## 📖 Utilizzo

### Primo avvio

1. Cliccare **📂 Apri Workspace**
2. Selezionare una cartella di lavoro
3. Se assente, viene creato automaticamente `Agenda.md`
4. Iniziare a scrivere

### Formato di Agenda.md

```md
# [Nome Pratica](percorso/relativo)

- Task da fare @file.pdf #urgente
  - Subtask indentato

- [x] Task completata
```

> **Nota:** la sintassi `# [Nome Pratica](percorso)` viene interpretata dall'applicazione e non rappresenta un collegamento Markdown tradizionale.

### Sintassi supportata

| Elemento | Significato |
|-----------|-------------|
| `# [Pratica](path)` | Definizione pratica |
| `- Task` | Task aperta |
| `- [x] Task` | Task completata |
| `@file.ext` | Collegamento a file |
| `@Persona` | Menzione persona |
| `#tag` | Tag |

---

### Autocomplete

| Trigger | Funzione |
|----------|-----------|
| `#` | Selezione o creazione pratica |
| `@` | Selezione file della pratica corrente |

---

### Shortcut

| Tasti | Azione |
|--------|---------|
| Ctrl+S | Salva documento |
| Ctrl+D | Cambia stato task |
| Ctrl+Shift+↑ | Sposta riga verso l'alto |
| Ctrl+Shift+↓ | Sposta riga verso il basso |
| Ctrl+F | Vai al filtro |
| Ctrl+E | Vai all'editor |
| Ctrl+N | Nuova pratica |
| Ctrl+P | Apri Command Palette |
| F5 | Aggiorna pannello laterale |
| Tab | Indenta selezione |
| Shift+Tab | Dedenta selezione |

---

### Command Palette (`Ctrl+P`)

- 🔍 Apri pratica
- 📄 Apri file
- ➕ Nuova pratica
- ✅ Nuovo task
- 🎨 Cambia tema
- 💾 Salva documento
- 🔍 Vai al filtro
- ✏️ Vai all'editor
- 🔄 Aggiorna albero

---

## 🏗️ Struttura del progetto

```text
practice_workspace/
├── main.py
├── requirements.txt
├── README.md
└── app/
    ├── __init__.py
    ├── constants.py
    ├── theme.py
    ├── models.py
    ├── parser.py
    ├── highlighter.py
    ├── main_window.py
    └── widgets/
        ├── __init__.py
        ├── editor.py
        ├── autocomplete.py
        ├── command_palette.py
        └── file_navigator.py
```

### Descrizione moduli

| File | Responsabilità |
|--------|---------------|
| main.py | Entry point |
| parser.py | Parsing di Agenda.md |
| models.py | Modelli dati |
| highlighter.py | Syntax highlighting |
| theme.py | Gestione tema |
| editor.py | Editor principale |
| autocomplete.py | Popup suggerimenti |
| command_palette.py | Command Palette |
| file_navigator.py | Navigazione filesystem |

---

## 🎯 Filosofia

- Deterministico: ogni pratica possiede un percorso esplicito
- Minimale: nessun elemento superfluo
- Keyboard First: tutte le operazioni principali sono eseguibili da tastiera
- Locale: dati conservati esclusivamente nel filesystem
- Human Readable: i contenuti restano sempre leggibili anche senza l'app

---

## 📄 Licenza

MIT © 2026 Raffaele

---

## 🤝 Contribuire

Pull request e segnalazioni sono benvenute.

Per modifiche sostanziali è consigliata l'apertura preventiva di una issue per discutere la proposta.
