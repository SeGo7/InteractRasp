# InteractRasp

This repository contains a small demo of an interactive schedule viewer.

## Components

- **schedule_api.py** – Flask based API that serves day and week schedules.
- **gui_app.py** – Tkinter GUI that fetches data from the API and displays it.

## Usage

1. Install dependencies (``ttkbootstrap`` is optional but provides a modern look):

```bash
pip install flask requests ttkbootstrap
```

2. Start the API server:

```bash
python schedule_api.py
```

3. In another terminal run the GUI application:

```bash
python gui_app.py
```

The GUI allows selecting a class to view its schedule for the day and also shows the week schedule.
If ``ttkbootstrap`` is not installed, the application will fall back to the standard Tk look.
