# Discrepancy Finder 🕵️‍♂️

![tests](https://github.com/ilodezis/discrepancy-finder/actions/workflows/tests.yml/badge.svg)

**English version below 👇**

`Discrepancy Finder` — кроссплатформенный офлайн‑инструмент для поиска расхождений между двумя Excel‑файлами (реестр ↔ акт).
Изначально написан для сверки реестров в Яндексе в 2025 году.

---

## 🔧 Ключевые возможности

| Что умеет | Как реализовано |
|-----------|-----------------|
| 📂 Читает `.xlsx / .xlsm / .xls` | `pandas` + `openpyxl` / `xlrd` |
| 🔎 Сам находит заголовок и колонки | строка с ID может быть не первой, «Сумма» важнее «Сумма НДС» |
| 💸 Понимает суммы текстом | `1 234,56`, `1,234.56`, `(100,00)`, `-5 ₽` |
| 🧾 Дубли ID суммируются | частичные оплаты не теряются (`duplicate_ids` в конфиге) |
| 🆔 Сверяет ID и суммы | `12345`, `12345.0` и ` 12345 ` считаются одним ID |
| 🚩 Показывает потерянные заказы | статусы «Нет в акте» / «Нет в реестре» |
| 💾 Экспорт отчёта | `.xlsx` или `.txt` (табуляция) |
| 🌐 Локализация (ru / en) | строки в `i18n/*.json`, новые языки подхватываются сами |
| ⚙️ Настройки без ребилда | `config.yaml` (в exe — положи свой рядом с exe) |
| ⏱ UI не зависает | загрузка и сравнение в `QThreadPool` |
| 🔒 Полностью офлайн | **нет** сетевых вызовов (см. `SECURITY_NOTES.md`) |

---

## 📥 Скачать готовый билд

| ОС | Ссылка |
|----|--------|
| Windows | [Releases](https://github.com/ilodezis/discrepancy-finder/releases) |
| macOS (Apple Silicon) | [Releases](https://github.com/ilodezis/discrepancy-finder/releases) |

---

## 🚀 Быстрый старт из исходников

```bash
git clone https://github.com/ilodezis/discrepancy-finder
cd discrepancy-finder
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Тесты:

```bash
pip install -r requirements-dev.txt
pytest
```

---

## 🧮 Как идёт сверка

1. В каждом файле ищется строка заголовков: первая строка, где есть колонка из `id_columns`.
2. Выбираются колонки ID и суммы. Точное совпадение с ключевым словом важнее частичного, а при частичном берётся самое короткое название. Какие колонки выбраны, видно в подсказке к имени файла в статус‑баре.
3. Строки «Итого» / «Всего» / «Total» и строки без ID выкидываются, суммы по одинаковым ID складываются.
4. Реестр и акт склеиваются по ID. В отчёт попадают заказы, где `|Реестр − Акт| > epsilon`, и заказы, которые есть только в одном из файлов.
5. Если какие‑то суммы не удалось распознать, программа предупредит и посчитает их как 0.

---

## 🗂️ Структура проекта

```plaintext
├── main.py                   # GUI: окна, кнопки, таблица результатов
├── logic.py                  # бизнес‑логика: чтение Excel и сверка (без Qt)
├── background.py             # фоновые задачи для QThreadPool
├── config.yaml               # настройки (epsilon, колонки, цвета, размеры)
├── i18n/                     # JSON‑файлы переводов
├── style.qss                 # Qt‑стили
├── assets/                   # иконка, шрифт Inter
├── tests/                    # pytest для logic.py
├── pyproject.toml            # настройки black / ruff / pytest
├── .pre-commit-config.yaml   # black + ruff
├── requirements.txt          # зависимости приложения
├── requirements-dev.txt      # + тесты, линтеры, PyInstaller
├── Discrepancy_Finder.spec   # PyInstaller спецификация
├── build_instructions.md     # как собрать .exe / .app
├── SECURITY_NOTES.md         # модель безопасности
```

---

## 🛠️ Кастомизация

### 🎨 Тема и цвета
Правь `style.qss` и `colors` в `config.yaml`.

### ⚙️ Конфиг
`config.yaml`: `epsilon`, ключевые слова для колонок ID и суммы, поведение при дублях ID, размер окна.
В собранной версии положи изменённый `config.yaml` рядом с exe.

### 🌐 Добавить язык
1. Скопируй `i18n/en.json` → `i18n/xx.json`.
2. Переведи значения (включая `language_name`).
3. Перезапусти приложение: язык появится в списке при старте.

---

## 🔐 Безопасность

* **Нет** сетевых вызовов (`requests`, `urllib`, sockets).
* **Нет** опасных системных вызовов (`subprocess`, `eval`).
* Технический лог пишется локально в `~/discrepancy_finder.log`, без ID и сумм.
* Подробности в `SECURITY_NOTES.md`.

---

## 📄 Лицензия

MIT — свободное использование и модификация с сохранением упоминания авторства.

---

## 📬 Обратная связь

* Issues: <https://github.com/ilodezis/discrepancy-finder/issues>
* Telegram: [@ilodezis](https://t.me/ilodezis)

---
---

# Discrepancy Finder (EN)

`Discrepancy Finder` is a cross‑platform offline tool that detects mismatches between two Excel files (registry ↔ act).
Originally built for registry reconciliation at Yandex in 2025.

---

## 🔧 Features

* Reads `.xlsx` / `.xlsm` / `.xls` via **pandas + openpyxl / xlrd**
* Finds the header row and the ID / amount columns automatically ("Amount" wins over "Amount VAT")
* Parses amounts stored as text: `1 234,56`, `1,234.56`, `(100.00)`
* Sums duplicate IDs (split payments) instead of dropping them
* Treats `12345`, `12345.0` and ` 12345 ` as the same ID
* Flags orders missing from either file
* Exports the report as `.xlsx` or tab‑separated `.txt`
* Localization via `i18n/*.json`, new languages are picked up automatically
* All settings live in `config.yaml` (drop your own next to the exe to override)
* Non‑blocking UI (`QThreadPool`)
* **100 % offline**, see `SECURITY_NOTES.md`

---

## 🚀 Quick start (source)

```bash
git clone https://github.com/ilodezis/discrepancy-finder
cd discrepancy-finder
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Run tests with `pip install -r requirements-dev.txt && pytest`.
Build instructions are in `build_instructions.md`.

---

## 🧮 How matching works

1. The header row is the first row containing one of `id_columns`.
2. Exact keyword matches beat partial ones; among partial matches the shortest column name wins. Hover the file name in the status bar to see which columns were picked.
3. Total rows and rows without an ID are dropped, amounts of repeated IDs are summed.
4. Files are joined by ID. The report lists IDs where `|Registry − Act| > epsilon` and IDs present in only one file.
5. Amounts that can't be parsed are counted as 0, and you get a warning about them.

---

## 🔐 Security
No network or dangerous sys‑calls. A technical log is written locally to `~/discrepancy_finder.log` without IDs or amounts. Details in `SECURITY_NOTES.md`.

---

## 📄 License
MIT License — free to use and modify.

---

## 📬 Feedback
* GitHub Issues
* Telegram [@ilodezis](https://t.me/ilodezis)
