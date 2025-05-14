# Discrepancy Finder

PyQt5-приложение для сравнения Excel-файлов (реестр и акт).
Показывает расхождения по ID и суммам, сохраняет результат в `.txt`.
Работает офлайн, не использует интернет и не передаёт данные.

[![Download](https://img.shields.io/badge/Download-Discrepancy--Finder-blue?style=for-the-badge\&logo=github)](https://github.com/ilodezis/discrepancy-finder/releases/download/v1.0.0/Discrepancy_Finder.exe)

---

## ✨ Возможности

* Поддержка `.xlsx` и `.xls`
* Автоматическое определение колонок и заголовков
* Расчёт итоговых сумм по обоим файлам
* Поддержка русского и английского интерфейса
* Сохранение расхождений в `.txt`
* Работа в офлайн-режиме, без доступа к сети

---

## 🚀 Установка и запуск из исходников

```bash
pip install -r requirements.txt
python Discrepancy_Finder.py
```

---

## ⚙ Сборка `.exe` вручную

```bash
pip install pyinstaller==6.13.0
pyinstaller Discrepancy_Finder.spec
```

* Сборка происходит через [PyInstaller](https://pyinstaller.org/)
* Готовый файл появится в папке `dist/`
* SHA256-хэш для сверки: см. файл `sha256.txt`
* Подробная инструкция: `build_instructions.md`

---

## 🔐 Информация для службы ИБ

* Программа **не использует интернет**
* Обработка персональных данных происходит **только в оперативной памяти**
* Никакие данные **не отправляются**, **не логируются**, **не сохраняются** без явного действия пользователя
* Отсутствуют модули `eval`, `exec`, `os.system`, `subprocess`
* Подробнее: `SECURITY_NOTES.md`

---

## 🔗 Полезные ссылки

* Релиз v1.0.0: [https://github.com/ilodezis/discrepancy-finder/releases/tag/v1.0.0](https://github.com/ilodezis/discrepancy-finder/releases/tag/v1.0.0)
* Инструкция по сборке `.exe`: `build_instructions.md`
* SHA256-хэш: `sha256.txt`
* Пояснение по безопасности: `SECURITY_NOTES.md`

---

Разработчик: ilodezis
