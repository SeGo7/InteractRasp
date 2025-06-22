import sys

from backend import update_data, get_raspisanie

from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QStackedWidget, QScrollArea, QGridLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

DAYS = ["ПОНЕДЕЛЬНИК", "ВТОРНИК", "СРЕДА", "ЧЕТВЕРГ", "ПЯТНИЦА", "СУББОТА"]


class ScheduleApp(QWidget):
    def __init__(self):
        super().__init__()

        update_data()
        self.TIME_LAST_CHECK = datetime.now()
        self.ALL_RASPISANIE = get_raspisanie(file_name='all.csv')
        self.DAY_RAPISANIE = get_raspisanie(file_name='day.csv')

        self.current_data = None
        self.setWindowTitle("Расписание")
        self.showFullScreen()

        self.stack = QStackedWidget()
        self.menu_page = QWidget()
        self.schedule_page = QWidget()

        self.create_menu_page()
        self.create_schedule_page()

        self.stack.addWidget(self.menu_page)
        self.stack.addWidget(self.schedule_page)

        layout = QVBoxLayout(self)
        layout.addWidget(self.stack)

    def check_update_rasp(self):
        if (datetime.now() - self.TIME_LAST_CHECK).seconds > 3600 or datetime.now().day > self.TIME_LAST_CHECK.day:
            self.TIME_LAST_CHECK = datetime.now()
            update_data()
            self.ALL_RASPISANIE = get_raspisanie(file_name='all.csv')
            self.DAY_RAPISANIE = get_raspisanie(file_name='day.csv')
            self.create_menu_page()

    def create_menu_page(self):
        layout = QVBoxLayout()
        today_day_name = DAYS[datetime.today().weekday()] if datetime.today().weekday() < 6 else \
            DAYS[(datetime.today().weekday()) % 6]

        self.current_data = self.DAY_RAPISANIE.get(today_day_name, self.ALL_RASPISANIE[today_day_name])

        label = QLabel(today_day_name)
        label.setFont(QFont("Arial", 12))

        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        scroll = QScrollArea()
        container = QWidget()
        grid = QGridLayout()

        all_lessons = {}
        for cls, lessons in self.current_data.items():
            for lesson in lessons:
                key = (lesson['урок'], cls)
                all_lessons.setdefault(key, []).append(lesson)

        class_names = sorted(self.current_data.keys())

        for col, cls in enumerate(class_names):
            header = QLabel(cls)
            header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            header.setAlignment(Qt.AlignmentFlag.AlignCenter)
            grid.addWidget(header, 0, col + 1)

        for row in range(7):
            label = QLabel(f"{row + 1}")
            label.setFont(QFont("Arial", 12))
            grid.addWidget(label, row + 1, 0)

            for col, cls in enumerate(class_names):
                lessons = all_lessons.get((row + 1, cls), [])
                if not lessons:
                    content = "—"
                else:
                    content = "\n---\n".join(
                        f"{l['предмет']} ({l['кабинет']})\n{l['учитель']}" for l in lessons)
                cell = QLabel(content)
                cell.setStyleSheet(
                    "background-color: white; color: black; padding: 3px; border: 1px solid gray; border-radius: 5px; font-size: 8pt;")
                cell.setWordWrap(True)
                grid.addWidget(cell, row + 1, col + 1)

        container.setLayout(grid)
        scroll.setWidget(container)
        scroll.setWidgetResizable(True)

        buttons_layout = QHBoxLayout()
        for cls in sorted(self.current_data):
            btn = QPushButton(f"{cls}")
            btn.setFont(QFont("Arial", 14))
            btn.clicked.connect(lambda _, c=cls: self.show_schedule(c))
            buttons_layout.addWidget(btn)

        exit_btn = QPushButton("Выход")
        exit_btn.setFont(QFont("Arial", 14))
        exit_btn.clicked.connect(QApplication.quit)

        layout.addWidget(scroll)
        layout.addLayout(buttons_layout)
        layout.addWidget(exit_btn, alignment=Qt.AlignmentFlag.AlignRight)
        self.menu_page.setLayout(layout)

    def create_schedule_page(self):
        self.schedule_layout = QVBoxLayout()
        self.schedule_grid = QGridLayout()
        self.schedule_grid.setSpacing(10)

        scroll = QScrollArea()
        container = QWidget()
        container.setLayout(self.schedule_grid)
        scroll.setWidget(container)
        scroll.setWidgetResizable(True)

        self.class_label = QLabel("")
        self.class_label.setFont(QFont("Arial", 20))
        self.class_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        back_btn = QPushButton("Назад")
        back_btn.setFont(QFont("Arial", 12))
        back_btn.setFixedSize(120, 40)
        back_btn.clicked.connect(self.back_to_menu)

        self.schedule_layout.addWidget(self.class_label)
        self.schedule_layout.addWidget(scroll)
        self.schedule_layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        self.schedule_page.setLayout(self.schedule_layout)

    def show_schedule(self, class_name):
        self.class_label.setText(f"Расписание для {class_name}")

        for i in reversed(range(self.schedule_grid.count())):
            widget = self.schedule_grid.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        for col, day in enumerate(DAYS[:-1]):
            header = QLabel(day)
            header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            header.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.schedule_grid.addWidget(header, 0, col + 1)

            if not day in self.ALL_RASPISANIE:
                continue
            lessons = self.ALL_RASPISANIE[day][class_name]

            for i in range(1, 8):
                label = QLabel(f"{i}:")
                label.setFont(QFont("Arial", 12))
                label.setWordWrap(True)
                self.schedule_grid.addWidget(label, i, 0)

                cell_texts = [
                    f"{l['предмет']} ({l['кабинет']})\n{l['учитель']}"
                    for l in lessons if l['урок'] == i
                ]

                content = "\n---\n".join(cell_texts) if cell_texts else "—"

                text_label = QLabel(content)
                text_label.setStyleSheet(
                    "background-color: white; color: black; padding: 8px; border: 1px solid #999; border-radius: 6px;")
                text_label.setWordWrap(True)
                self.schedule_grid.addWidget(text_label, i, col + 1)

            self.stack.setCurrentWidget(self.schedule_page)

    def back_to_menu(self):
        self.check_update_rasp()
        self.stack.setCurrentWidget(self.menu_page)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ScheduleApp()
    window.show()
    sys.exit(app.exec())
