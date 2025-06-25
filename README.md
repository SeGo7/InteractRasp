# Интерактивное расписание

Это приложение на Python с графическим интерфейсом на PyQt для отображения и управления школьным расписанием.

## Требования

* **Python 3.10+**
* Установленные зависимости:

```bash
pip install -r requirements.txt
```

## Сборка в `.exe`

Для сборки исполняемого файла используется **PyInstaller**:

### Установка PyInstaller

```bash
pip install pyinstaller
```

### Сборка

```bash
pyinstaller --noconfirm --windowed --onefile --icon=icon.ico RaspisanieCOD.py; xcopy /E /I /Y /Q /C tmp dist\\tmp\\; cp icon.ico dist/icon.ico
```



* `--noconfirm` — не задавать вопросов в процессе
* `--windowed` — скрыть консольное окно (для GUI)
* `--onefile` — собрать в один `.exe`

Готовый файл будет в папке `dist/`.