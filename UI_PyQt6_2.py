import sys

from backend import update_data, get_raspisanie

from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QStackedWidget,
    QScrollArea,
    QGridLayout,
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

        # Basic dark theme styling for a more modern look
        self.setStyleSheet(
            """
            QWidget {background-color: #2b2b2b; color: white;}
            QPushButton {
                background-color: #444;
                color: white;
                padding: 6px;
                border-radius: 4px;
            }
            QPushButton:hover {background-color: #666;}
            QLabel {color: white;}
            """
        )

        self.stack = QStackedWidget()
        self.menu_page = QWidget()
        self.teachers_menu_page = QWidget()
        self.rooms_page = QWidget()
        self.schedule_page = QWidget()

        self.create_menu_page()
        self.create_teachers_menu_page()
        self.create_rooms_page()
        self.create_schedule_page()

        self.stack.addWidget(self.menu_page)
        self.stack.addWidget(self.teachers_menu_page)
        self.stack.addWidget(self.rooms_page)
        self.stack.addWidget(self.schedule_page)

        layout = QVBoxLayout(self)
        layout.addWidget(self.stack)

        # Build additional structures
        self.build_teacher_schedule()
        self.build_rooms_list()

    def build_teacher_schedule(self):
        """Create mapping of teacher -> day -> lessons"""
        self.teacher_schedule = {}
        for day, classes in self.ALL_RASPISANIE.items():
            for cls, lessons in classes.items():
                for l in lessons:
                    teacher = l.get("учитель", "")
                    if not teacher:
                        continue
                    self.teacher_schedule.setdefault(teacher, {}).setdefault(day, []).append(
                        {
                            "урок": l["урок"],
                            "предмет": l["предмет"],
                            "кабинет": l["кабинет"],
                            "класс": cls,
                        }
                    )

    def build_rooms_list(self):
        self.all_rooms = set()
        for day_data in self.ALL_RASPISANIE.values():
            for lessons in day_data.values():
                for l in lessons:
                    room = l.get("кабинет", "")
                    if room:
                        self.all_rooms.add(room)

    def check_update_rasp(self):
        if (datetime.now() - self.TIME_LAST_CHECK).seconds > 3600 or datetime.now().day > self.TIME_LAST_CHECK.day:
            self.TIME_LAST_CHECK = datetime.now()
            update_data()
            self.ALL_RASPISANIE = get_raspisanie(file_name='all.csv')
            self.DAY_RAPISANIE = get_raspisanie(file_name='day.csv')
            self.build_teacher_schedule()
            self.build_rooms_list()
            self.create_menu_page()
            self.create_teachers_menu_page()
            self.create_rooms_page()

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
                    "background-color: #3c3c3c; color: white; padding: 3px; border: 1px solid #555; border-radius: 5px; font-size: 8pt;"
                )
                cell.setWordWrap(True)
                grid.addWidget(cell, row + 1, col + 1)

        container.setLayout(grid)
        scroll.setWidget(container)
        scroll.setWidgetResizable(True)

        buttons_layout = QHBoxLayout()
        for cls in sorted(self.current_data):
            btn = QPushButton(f"{cls}")
            btn.setFont(QFont("Arial", 14))
            btn.clicked.connect(lambda _, c=cls: self.show_class_schedule(c))
            buttons_layout.addWidget(btn)

        exit_btn = QPushButton("Выход")
        exit_btn.setFont(QFont("Arial", 14))
        exit_btn.clicked.connect(QApplication.quit)

        teachers_btn = QPushButton("Учителя")
        teachers_btn.setFont(QFont("Arial", 14))
        teachers_btn.clicked.connect(lambda: self.stack.setCurrentWidget(self.teachers_menu_page))

        rooms_btn = QPushButton("Кабинеты")
        rooms_btn.setFont(QFont("Arial", 14))
        rooms_btn.clicked.connect(lambda: self.stack.setCurrentWidget(self.rooms_page))

        layout.addWidget(scroll)
        layout.addLayout(buttons_layout)
        layout.addWidget(teachers_btn)
        layout.addWidget(rooms_btn)
        layout.addWidget(exit_btn, alignment=Qt.AlignmentFlag.AlignRight)
        self.menu_page.setLayout(layout)

    def create_teachers_menu_page(self):
        layout = QVBoxLayout()
        label = QLabel("Учителя")
        label.setFont(QFont("Arial", 14))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        scroll = QScrollArea()
        container = QWidget()
        grid = QGridLayout()

        teachers = sorted(self.teacher_schedule.keys())
        for idx, teacher in enumerate(teachers):
            btn = QPushButton(teacher)
            btn.setFont(QFont("Arial", 12))
            btn.clicked.connect(lambda _, t=teacher: self.show_teacher_schedule(t))
            grid.addWidget(btn, idx // 3, idx % 3)

        container.setLayout(grid)
        scroll.setWidget(container)
        scroll.setWidgetResizable(True)

        back_btn = QPushButton("Назад")
        back_btn.setFont(QFont("Arial", 12))
        back_btn.clicked.connect(self.back_to_menu)

        layout.addWidget(label)
        layout.addWidget(scroll)
        layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        self.teachers_menu_page.setLayout(layout)

    def create_rooms_page(self):
        layout = QVBoxLayout()
        day_buttons = QHBoxLayout()

        for day in DAYS[:-1]:
            btn = QPushButton(day)
            btn.setFont(QFont("Arial", 12))
            btn.clicked.connect(lambda _, d=day: self.show_rooms_for_day(d))
            day_buttons.addWidget(btn)

        self.rooms_info_label = QLabel("")
        self.rooms_info_label.setWordWrap(True)

        back_btn = QPushButton("Назад")
        back_btn.setFont(QFont("Arial", 12))
        back_btn.clicked.connect(self.back_to_menu)

        layout.addLayout(day_buttons)
        layout.addWidget(self.rooms_info_label)
        layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        self.rooms_page.setLayout(layout)

    def show_rooms_for_day(self, day):
        occupied = set()
        day_data = self.ALL_RASPISANIE.get(day, {})
        for lessons in day_data.values():
            for l in lessons:
                room = l.get("кабинет", "")
                if room:
                    occupied.add(room)
        free = sorted(self.all_rooms - occupied)
        occupied = sorted(occupied)

        text = f"Заняты: {', '.join(occupied)}\nСвободны: {', '.join(free) if free else 'нет'}"
        self.rooms_info_label.setText(text)
        self.stack.setCurrentWidget(self.rooms_page)

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

    def show_class_schedule(self, class_name):
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
                    "background-color: #3c3c3c; color: white; padding: 8px; border: 1px solid #555; border-radius: 6px;"
                )
                text_label.setWordWrap(True)
                self.schedule_grid.addWidget(text_label, i, col + 1)

        self.stack.setCurrentWidget(self.schedule_page)

    def show_teacher_schedule(self, teacher_name):
        self.class_label.setText(f"Расписание для {teacher_name}")

        for i in reversed(range(self.schedule_grid.count())):
            widget = self.schedule_grid.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        for col, day in enumerate(DAYS[:-1]):
            header = QLabel(day)
            header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            header.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.schedule_grid.addWidget(header, 0, col + 1)

            lessons = self.teacher_schedule.get(teacher_name, {}).get(day, [])

            for i in range(1, 8):
                label = QLabel(f"{i}:")
                label.setFont(QFont("Arial", 12))
                label.setWordWrap(True)
                self.schedule_grid.addWidget(label, i, 0)

                cell_texts = [
                    f"{l['предмет']} ({l['кабинет']})\n{l['класс']}"
                    for l in lessons if l['урок'] == i
                ]

                content = "\n---\n".join(cell_texts) if cell_texts else "—"

                text_label = QLabel(content)
                text_label.setStyleSheet(
                    "background-color: #3c3c3c; color: white; padding: 8px; border: 1px solid #555; border-radius: 6px;"
                )
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
