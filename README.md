# Discrepancy Finder

**Discrepancy Finder** — офлайн-инструмент для сравнения Excel-файлов (акт и реестр).  
Определяет расхождения по ID и суммам, сохраняет результат в `.txt`.

Программа разработана для ручного использования — без установки, без доступа к сети, без логирования.

---

## 🔧 Возможности

- 📂 Поддержка `.xlsx` и `.xls`
- 🆔 Поиск несовпадений по ID и суммам
- 💾 Выгрузка отчёта в `.txt`
- 🌐 Поддержка русского и английского языков
- 🖥️ Интерфейс на PyQt5 (не консоль)
- 🔒 Полностью офлайн, без внешних подключений
- 🪪 Безопасна для работы с ПД (см. `SECURITY_NOTES.md`)

---

## 📥 Скачать

Стабильный релиз:  
👉 [Скачать .exe (v1.0.1)](https://github.com/ilodezis/discrepancy-finder/releases/latest)

Для Windows. Запуск без установки. Прав администратора не требуется.

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

