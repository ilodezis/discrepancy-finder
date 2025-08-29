# Discrepancy Finder 🕵️‍♂️

**English version below 👇**

`Discrepancy Finder` — кроссплатформенный офлайн‑инструмент для поиска расхождений между двумя Excel‑файлами (реестр ↔ акт). Версия **1.1.x**: конфиги, переводы и стили вынесены в отдельные файлы, тяжёлая логика переведена в фоновый поток, код приведён к PEP‑8.

---

## 🔧 Ключевые возможности

| Что умеет | Как реализовано |
|-----------|-----------------|
| 📂 Читает `.xlsx / .xls` | `pandas + openpyxl` |
| 🆔 Сверяет ID и суммы | автопоиск колонок, фильтр «эпсилон» |
| 💾 Экспорт отчёта в `.txt` | отдельная кнопка *Save* |
| 🌐 Локализация (ru / en) | строки в `i18n/*.json` |
| 🎨 Кастомизация внешнего вида | `style.qss`, цвета в `config.yaml` |
| ⚙️ Настройки без ребилда | все «магические» цифры в `config.yaml` |
| ⏱ UI не зависает | сравнение в `QRunnable` + `QThreadPool` |
| 🔒 Полностью офлайн | **нет** сетевых вызовов (см. `SECURITY_NOTES.md`) |

---

## 📥 Скачать готовый билд

| ОС | Ссылка |
|----|--------|
| Windows | [Discrepancy Finder 1.1.0 .exe](https://github.com/ilodezis/discrepancy-finder/releases/tag/v.1.1.0-win) |
| macOS (Apple Silicon) | [Discrepancy Finder 1.1.0 .app](https://github.com/ilodezis/discrepancy-finder/releases/tag/v1.1.0-mac) |

---

## 🚀 Быстрый старт из исходников

```bash
git clone https://github.com/ilodezis/discrepancy-finder
cd discrepancy-finder
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

---

## 🗂️ Структура проекта

```plaintext
├── main.py                   # GUI: окна, кнопки, меню
├── logic.py                  # бизнес‑логика: Excel + сравнение
├── background.py             # QRunnable для фонового сравнения
├── config.yaml               # настройки (epsilon, цвета, размеры)
├── i18n/                     # JSON‑файлы переводов
│   ├── en.json
│   └── ru.json
├── style.qss                 # Qt‑стили
├── assets/                   # иконки, шрифт Inter
├── .pre-commit-config.yaml   # black + ruff автоформат
├── requirements.txt          # минимальные версии библиотек
├── Discrepancy_Finder.spec   # PyInstaller спецификация
├── build_instructions.md     # как собрать .exe /.app
├── SECURITY_NOTES.md         # описание модели безопасности
```

---

## 🛠️ Кастомизация

### 🎨 Тема и цвета
Правь `style.qss` — приложение подхватит изменения без ребилда.

### ⚙️ Конфиг
`config.yaml` → меняешь `epsilon` или фон окна, сохраняешь, перезапускаешь.

### 🌐 Добавить язык
1. Скопируй `i18n/en.json` → `i18n/xx.json`.
2. Переведи значения.
3. Запусти `main.py`, выбери новый язык — интерфейс переключится.

---

## 🔐 Безопасность

* **Нет** сетевых вызовов (`requests`, `urllib`, sockets).
* **Нет** опасных системных вызовов (`subprocess`, `eval`).
* Код проверен `ruff`, аудит описан в `SECURITY_NOTES.md`.
* Программа работает строго локально.

---

## 📄 Лицензия

MIT — свободное использование и модификация с сохранением упоминания авторства.

---

## 📬 Обратная связь

* Issues: <https://github.com/ilodezis/discrepancy-finder/issues>
* Telegram: [@ilodezis](https://t.me/ilodezis)

---
---

# Discrepancy Finder (EN)

`Discrepancy Finder` is a cross‑platform offline tool that detects mismatches between two Excel files (registry ↔ act). Version **1.1.x** moves configs, translations, and styles to separate files, runs heavy logic in a background thread and formats code to PEP‑8.

---

## 🔧 Features

* Reads `.xlsx`/`.xls` via **pandas + openpyxl**
* Compares by **ID** and **Amount**
* Exports report as `.txt`
* Localization via `i18n/*.json` (ru / en by default)
* Fully customizable look via `style.qss`
* All tweakable settings live in `config.yaml`
* Non‑blocking UI (`QRunnable` + `QThreadPool`)
* **100 % offline** — see `SECURITY_NOTES.md`

---

## 📥 Download binaries

| OS | Link |
|----|------|
| Windows | [Discrepancy Finder 1.1.0 .exe](https://github.com/ilodezis/discrepancy-finder/releases/tag/v1.1.0-win) |
| macOS (Apple Silicon) | [Discrepancy Finder 1.1.0 .app](https://github.com/ilodezis/discrepancy-finder/releases/tag/v1.1.0-mac) |

---

## 🚀 Quick start (source)

```bash
git clone https://github.com/ilodezis/discrepancy-finder
cd discrepancy-finder
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

---

## 🗂️ Project layout

```plaintext
├── main.py                   # GUI: windows, buttons, menu
├── logic.py                  # business logic: Excel comparison
├── background.py             # QRunnable background comparison
├── config.yaml               # settings (epsilon, colors, sizes)
├── i18n/                     # JSON translations
│   ├── en.json
│   └── ru.json
├── style.qss                 # Qt stylesheet
├── assets/                   # icons, Inter font
├── .pre-commit-config.yaml   # black + ruff autoformat
├── requirements.txt          # minimal library versions
├── Discrepancy_Finder.spec   # PyInstaller spec
├── build_instructions.md     # build instructions
├── SECURITY_NOTES.md         # security model description
```

---

## 🛠️ Customisation
* **Theme** — edit `style.qss`.
* **Settings** — tweak `config.yaml` (e.g. `epsilon`, window size).
* **New language** — add `i18n/xx.json`, restart app.

---

## 🔐 Security
No network or dangerous sys‑calls. Details in `SECURITY_NOTES.md`.

---

## 📄 License
MIT License — free to use and modify.

---

## 📬 Feedback
* GitHub Issues
* Telegram [@ilodezis](https://t.me/ilodezis)
