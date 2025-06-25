import sys
from backend import update_data, get_rasp
from datetime import date, datetime
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QStackedWidget, QScrollArea, QGridLayout, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap

from config import all_rooms

DAYS = ["ПОНЕДЕЛЬНИК", "ВТОРНИК", "СРЕДА", "ЧЕТВЕРГ", "ПЯТНИЦА", "СУББОТА"]


class ScheduleApp(QWidget):
    def __init__(self):
        super().__init__()

        update_data()

        self.TIME_LAST_CHECK = datetime.now()
        self.DAY_RAPISANIE, self.ALL_RASPISANIE = get_rasp()

        self.current_day_index = date.today().weekday() % len(DAYS)
        self.current_data = self.get_raspisanie_changes()
        self.name_classes = sorted(self.current_data)
        self.setWindowTitle("Расписание")
        self.showFullScreen()

        self.stack = QStackedWidget()
        self.menu_page = QWidget()
        self.add_corner_icon(self.menu_page)
        self.schedule_page = QWidget()
        self.add_corner_icon(self.schedule_page)
        self.teacher_schedule_page = QWidget()
        self.add_corner_icon(self.teacher_schedule_page)

        self.create_menu_page()
        self.create_schedule_page()
        self.create_teacher_schedule_page()
        self.create_free_rooms_page()

        self.stack.addWidget(self.menu_page)
        self.stack.addWidget(self.schedule_page)
        self.stack.addWidget(self.teacher_schedule_page)
        self.stack.addWidget(self.free_rooms_page)

        layout = QVBoxLayout(self)
        layout.addWidget(self.stack)

    def get_raspisanie_changes(self):
        return self.DAY_RAPISANIE.get(DAYS[self.current_day_index], self.ALL_RASPISANIE[DAYS[self.current_day_index]])

    def get_raspisanie_const(self):
        return self.ALL_RASPISANIE[DAYS[self.current_day_index]]

    def check_update_rasp(self):
        if (datetime.now() - self.TIME_LAST_CHECK).seconds > 3600 or datetime.now().day > self.TIME_LAST_CHECK.day:
            self.TIME_LAST_CHECK = datetime.now()
            update_data()
            self.DAY_RAPISANIE, self.ALL_RASPISANIE = get_rasp()
            self.create_menu_page()

    def create_menu_page(self):
        layout = QVBoxLayout()

        self.current_data = self.get_raspisanie_changes()

        header_layout = QHBoxLayout()

        if not hasattr(self, 'day_label'):
            self.day_label = QLabel(DAYS[self.current_day_index])
        self.day_label.setFont(QFont("Arial", 12))
        self.day_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        prev_day_btn = QPushButton("←")
        prev_day_btn.setFixedWidth(40)
        prev_day_btn.clicked.connect(self.prev_day)
        header_layout.addWidget(prev_day_btn)

        header_layout.addWidget(self.day_label)

        next_day_btn = QPushButton("→")
        next_day_btn.setFixedWidth(40)
        next_day_btn.clicked.connect(self.next_day)
        header_layout.addWidget(next_day_btn)

        self.teacher_dropdown = QComboBox()
        self.teacher_dropdown.setFont(QFont("Arial", 12))
        self.teacher_dropdown.currentTextChanged.connect(self.show_teacher_schedule_from_menu)
        header_layout.addWidget(self.teacher_dropdown)

        self.classes_dropdown = QComboBox()
        self.classes_dropdown.setFont(QFont("Arial", 12))
        self.classes_dropdown.currentTextChanged.connect(self.show_class_schedule_from_menu)
        header_layout.addWidget(self.classes_dropdown)

        layout.addLayout(header_layout)

        self.menu_scroll = QScrollArea()
        self.menu_container = QWidget()
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
                if not lessons or (len(lessons) == 1 and {'урок': row + 1, 'отличается' : True} in lessons):
                    content = "—"
                else:
                    content = "\n---\n".join(
                        f"{l['предмет']} {f'({l['кабинет']})' if l['кабинет'] else ''}\n{l['учитель']}" for l in lessons)
                cell = QLabel(content)
                cell.setStyleSheet(
                    f"background-color: {'yellow' if any(l.get('отличается', False) for l in lessons) else 'white'}; color: black; padding: 3px; border: 1px solid gray; border-radius: 5px; font-size: 8pt;")
                cell.setWordWrap(True)
                cell.setFixedWidth(140)
                grid.addWidget(cell, row + 1, col + 1)

        self.menu_container.setLayout(grid)
        self.menu_container.update()
        self.menu_scroll.setWidget(self.menu_container)
        self.menu_scroll.setWidgetResizable(True)

        exit_btn = QPushButton("Выход")
        exit_btn.setFont(QFont("Arial", 14))
        exit_btn.clicked.connect(QApplication.quit)

        layout.addWidget(self.menu_scroll)
        free_rooms_btn = QPushButton("Свободные кабинеты")
        free_rooms_btn.setFont(QFont("Arial", 14))
        free_rooms_btn.clicked.connect(self.show_free_rooms)
        layout.addWidget(free_rooms_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        layout.addWidget(exit_btn, alignment=Qt.AlignmentFlag.AlignRight)

        self.menu_page.setLayout(layout)

        self.TEACHER_RASP = self.group_by_teacher()
        self.teacher_dropdown.clear()
        self.teacher_dropdown.addItem("Выберите учителя")
        self.teacher_dropdown.addItems(sorted(self.TEACHER_RASP.keys()))

        self.classes_dropdown.clear()
        self.classes_dropdown.addItem("Выберите класс")
        self.classes_dropdown.addItems(self.name_classes)

        # self.stack.setCurrentWidget(self.teacher_schedule_page)

    def show_teacher_schedule_from_menu(self, teacher):
        if teacher != "Выберите учителя":
            self.show_teacher_schedule(teacher)

    def show_class_schedule_from_menu(self, name_class):
        if name_class != "Выберите класс":
            self.show_schedule(name_class)

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

    def create_teacher_schedule_page(self):
        self.teacher_schedule_layout = QVBoxLayout()
        self.teacher_schedule_grid = QGridLayout()
        scroll = QScrollArea()
        container = QWidget()
        container.setLayout(self.teacher_schedule_grid)
        scroll.setWidget(container)
        scroll.setWidgetResizable(True)

        self.teacher_name_label = QLabel("")
        self.teacher_name_label.setFont(QFont("Arial", 20))
        self.teacher_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        back_btn = QPushButton("Назад")
        back_btn.setFont(QFont("Arial", 12))
        back_btn.setFixedSize(120, 40)
        back_btn.clicked.connect(lambda: self.stack.setCurrentWidget(self.menu_page))

        self.teacher_schedule_layout.addWidget(self.teacher_name_label)
        self.teacher_schedule_layout.addWidget(scroll)
        self.teacher_schedule_layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        self.teacher_schedule_page.setLayout(self.teacher_schedule_layout)

    def show_schedule(self, class_name : str):
        self.class_label.setText(f"Расписание для {class_name}")

        for i in reversed(range(self.schedule_grid.count())):
            widget = self.schedule_grid.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        for col, day in enumerate(DAYS):
            header = QLabel(day)
            header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            header.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.schedule_grid.addWidget(header, 0, col + 1)

            if not day in self.ALL_RASPISANIE:
                continue
            lessons = self.ALL_RASPISANIE[day].get(class_name, [])

            for i in range(1, 8):
                label = QLabel(f"{i}:")
                label.setFont(QFont("Arial", 12))
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

    def group_by_teacher(self):
        teachers = {}
        for day, classes in self.ALL_RASPISANIE.items():
            for cls, lessons in classes.items():
                for lesson in lessons:
                    teacher = lesson['учитель']
                    teachers.setdefault(teacher, {}).setdefault(day, []).append({
                        **lesson,
                        'класс': cls
                    })
        return teachers

    def show_teacher_schedule(self, teacher_name):
        self.teacher_name_label.setText(f"Расписание: {teacher_name}")
        self.teacher_schedule_grid.setSpacing(10)

        for i in reversed(range(self.teacher_schedule_grid.count())):
            widget = self.teacher_schedule_grid.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        for col, day in enumerate(DAYS):
            header = QLabel(day)
            header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            header.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.teacher_schedule_grid.addWidget(header, 0, col + 1)

            lessons = self.TEACHER_RASP.get(teacher_name, {}).get(day, [])

            for i in range(1, 8):
                label = QLabel(f"{i}:")
                label.setFont(QFont("Arial", 12))
                self.teacher_schedule_grid.addWidget(label, i, 0)

                cell_texts = [
                    f"{l['предмет']} ({l['кабинет']})\n{l['класс']}"
                    for l in lessons if l['урок'] == i
                ]
                content = "\n---\n".join(cell_texts) if cell_texts else "—"
                cell = QLabel(content)
                cell.setStyleSheet("background-color: white; color: black; padding: 8px; border: 1px solid #999; border-radius: 6px;")
                cell.setWordWrap(True)
                self.teacher_schedule_grid.addWidget(cell, i, col + 1)

        self.stack.setCurrentWidget(self.teacher_schedule_page)

    def prev_day(self):
        self.current_day_index = (self.current_day_index - 1) % len(DAYS)
        self.update_day_schedule()

    def next_day(self):
        self.current_day_index = (self.current_day_index + 1) % len(DAYS)
        self.update_day_schedule()

    def update_day_schedule(self):
        self.day_label.setText(DAYS[self.current_day_index])
        self.show_menu_page()

    def show_menu_page(self):
        self.day_label.setText(DAYS[self.current_day_index])
        self.current_data = self.get_raspisanie_changes()

        container = self.menu_container
        layout = container.layout()

        if layout is None:
            layout = QGridLayout()
            container.setLayout(layout)
        else:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()

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
            header.setFixedWidth(140)
            layout.addWidget(header, 0, col + 1)

        for row in range(7):
            label = QLabel(f"{row + 1}")
            label.setFont(QFont("Arial", 12))
            layout.addWidget(label, row + 1, 0)

            for col, cls in enumerate(class_names):
                lessons = all_lessons.get((row + 1, cls), [])
                if not lessons or (len(lessons) == 1 and {'урок': row + 1, 'отличается': True} in lessons):
                    content = "—"
                else:
                    content = "\n---\n".join(
                        f"{l['предмет']} {f'({l['кабинет']})' if l['кабинет'] else ''}\n{l['учитель']}" for l in
                        lessons)
                cell = QLabel(content)
                cell.setStyleSheet(
                    f"background-color: {'yellow' if any(l.get('отличается', False) for l in lessons) else 'white'}; color: black; padding: 3px; border: 1px solid gray; border-radius: 5px; font-size: 8pt;")
                cell.setWordWrap(True)
                cell.setFixedWidth(140)
                layout.addWidget(cell, row + 1, col + 1)

        self.menu_container.update()
        self.stack.setCurrentWidget(self.menu_page)

    def add_corner_icon(self, page):
        icon = QLabel(page)
        icon.setPixmap(QPixmap("icon.ico").scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        icon.setGeometry(page.width() - 620, 1090, 40, 40)
        icon.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        icon.setStyleSheet("background: transparent;")
        icon.raise_()

    def create_free_rooms_page(self):
        self.free_rooms_page = QWidget()
        self.add_corner_icon(self.free_rooms_page)

        self.free_rooms_layout = QVBoxLayout()
        self.free_rooms_grid = QGridLayout()
        scroll = QScrollArea()
        container = QWidget()
        container.setLayout(self.free_rooms_grid)
        scroll.setWidget(container)
        scroll.setWidgetResizable(True)

        self.free_rooms_label = QLabel(f"Свободные кабинеты на {DAYS[self.current_day_index]}")
        self.free_rooms_label.setFont(QFont("Arial", 20))
        self.free_rooms_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        back_btn = QPushButton("Назад")
        back_btn.setFont(QFont("Arial", 12))
        back_btn.setFixedSize(120, 40)
        back_btn.clicked.connect(self.back_to_menu)

        self.free_rooms_layout.addWidget(self.free_rooms_label)
        self.free_rooms_layout.addWidget(scroll)
        self.free_rooms_layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        self.free_rooms_page.setLayout(self.free_rooms_layout)

    def show_free_rooms(self):
        for i in reversed(range(self.free_rooms_grid.count())):
            widget = self.free_rooms_grid.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        busy_rooms_by_lesson = {i: set() for i in range(1, 8)}
        for cls, lessons in self.current_data.items():
            for lesson in lessons:
                if lesson.get('кабинет', False):
                    busy_rooms_by_lesson[lesson['урок']].add(lesson['кабинет'])

        for col, room in enumerate(all_rooms):
            header = QLabel(str(room))
            header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            header.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.free_rooms_grid.addWidget(header, 0, col + 1)

        for row in range(1, 8):
            label = QLabel(f"Урок {row}")
            label.setFont(QFont("Arial", 12))
            self.free_rooms_grid.addWidget(label, row, 0)

            for col, room in enumerate(all_rooms):
                is_busy = str(room) in busy_rooms_by_lesson[row]
                if not is_busy:
                    cell = QLabel("Свободен")
                    cell.setStyleSheet("background-color: #ccffcc; color: black; padding: 6px; border: 1px solid gray; border-radius: 5px;")
                    cell.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.free_rooms_grid.addWidget(cell, row, col + 1)

        self.stack.setCurrentWidget(self.free_rooms_page)


    def back_to_menu(self):
        self.check_update_rasp()
        self.stack.setCurrentWidget(self.menu_page)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ScheduleApp()
    window.show()
    sys.exit(app.exec())
