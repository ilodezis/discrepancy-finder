# Discrepancy Finder

**English version below 👇**

**Discrepancy Finder** — инструмент для сравнения Excel-файлов (акт и реестр).  
Определяет расхождения по ID и суммам, сохраняет результат в `.txt` в случае необходимости.

---

## 🔧 Возможности

- 📂 Поддержка `.xlsx` и `.xls`
- 🆔 Поиск несовпадений по ID и суммам
- 💾 Выгрузка отчёта в `.txt`
- 🌐 Поддержка русского и английского языков
- 🖥️ Интерфейс на PyQt5
- 🔒 Полностью офлайн, без внешних подключений
- 🪪 Безопасна для работы с ПД (см. `SECURITY_NOTES.md`)

---

## 📥 Скачать

Стабильный релиз:  
👉 [Скачать .exe (v1.0.2-win)](https://github.com/ilodezis/discrepancy-finder/releases/tag/v.1.0.2-win)

👉 [Скачать .app (v1.0.2-mac)](https://github.com/ilodezis/discrepancy-finder/releases/tag/v.1.0.2-mac)

Для Windows и macOS. 

---

## 🛠️ Как собрать `.exe` вручную

См. [build_instructions.md](build_instructions.md)  
Подходит для Windows с Python 3.11+ и установленным `PyInstaller`.

---

## 🧾 Структура проекта

```plaintext
├── Discrepancy_Finder.py        # основной GUI-файл
├── requirements.txt             # зависимости
├── Discrepancy_Finder.spec      # PyInstaller конфиг
├── assets/                      # иконка и шрифт
├── README.md
├── build_instructions.md
├── sha256.txt                   # хэш для сверки бинарника
└── SECURITY_NOTES.md           # безопасность и поведение
````

---

## 🔐 Безопасность и аудит

Discrepancy Finder не содержит:

* сетевых вызовов (нет `requests`, `urllib`, сокетов)
* критичных системных вызовов (`os.system`, `subprocess`, `eval`)
* логирования, сбора метрик, сохранения истории

Вся логика и риски подробно описаны в [SECURITY\_NOTES.md](SECURITY_NOTES.md).
Программа предназначена **исключительно для локального запуска вручную**.

---

## 📄 Лицензия

MIT License — свободное использование и модификация.

---

## 📬 Обратная связь

Для связи: [issues](https://github.com/ilodezis/discrepancy-finder/issues) или Telegram @ilodezis

---
---

# Discrepancy Finder

**Discrepancy Finder** is a tool for comparing Excel files (registry and act).
It detects discrepancies by ID and amounts, and can optionally save the result as a `.txt` file.

---

## 🔧 Features

* 📂 Supports `.xlsx` and `.xls`
* 🆔 Detects mismatches by ID and amounts
* 💾 Exports reports in `.txt`
* 🌐 Russian and English language support
* 🖥️ PyQt5-based interface
* 🔒 Fully offline, no external connections
* 🪪 Safe for working with personal data (see `SECURITY_NOTES.md`)

---

## 📥 Download

Stable release:

👉 [Download .exe (v1.0.1)](https://github.com/ilodezis/discrepancy-finder/releases/tag/v1.0.1)

👉 [Download .dmg (v1.0.1-mac)](https://github.com/ilodezis/discrepancy-finder/releases/tag/v.1.0.1-mac)

For Windows and macOS.

---

## 🛠️ How to build `.exe` manually

See [build\_instructions.md](build_instructions.md) — works on Windows with Python 3.11+ and installed `PyInstaller`.

---

## 🧾 Project structure

```plaintext
├── Discrepancy_Finder.py        # main GUI file
├── requirements.txt             # dependencies
├── Discrepancy_Finder.spec      # PyInstaller config
├── assets/                      # icon and font
├── README.md
├── build_instructions.md
├── sha256.txt                   # binary hash for verification
└── SECURITY_NOTES.md           # security and behavior notes
```

---

## 🔐 Security & Audit

Discrepancy Finder contains **no**:

* network calls (`requests`, `urllib`, sockets)
* critical system calls (`os.system`, `subprocess`, `eval`)
* logging, metric collection, or history tracking

All logic and risks are described in detail in [SECURITY\_NOTES.md](SECURITY_NOTES.md).

The program is designed **strictly for manual local use**.

---

## 📄 License

MIT License — free to use and modify.

---

## 📬 Feedback

For feedback: [issues](https://github.com/ilodezis/discrepancy-finder/issues) or Telegram @ilodezis

