# Сборка Discrepancy Finder (.exe / .app)

Сборка делается [PyInstaller](https://pyinstaller.org/) по файлу `Discrepancy_Finder.spec`.
Собирать нужно на той ОС, под которую нужен билд: Windows → `.exe`, macOS → `.app`.

## 🔧 Требования

- Python 3.11+
- pip

## 📦 Установка зависимостей

```bash
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
pip install -r requirements-dev.txt
```

> PyInstaller старше 6.22 не дружит со свежим numpy 2.x: exe собирается, но падает при запуске.

## 🏗️ Сборка

```bash
pyinstaller Discrepancy_Finder.spec --noconfirm
```

Результат:

- Windows: `dist/Discrepancy_Finder.exe` (один файл)
- macOS: `dist/Discrepancy Finder.app`

## ⚙️ Настройки в собранной версии

`config.yaml` вшит в exe. Чтобы поменять настройки без пересборки, положи свой
`config.yaml` рядом с exe: он будет прочитан вместо встроенного.

## 🔒 Контрольная сумма

```bash
# Windows
certutil -hashfile dist\Discrepancy_Finder.exe SHA256
# macOS / Linux
shasum -a 256 dist/Discrepancy_Finder
```
