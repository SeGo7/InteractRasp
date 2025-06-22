import sys
import requests
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QComboBox,
    QTableWidget, QTableWidgetItem, QTabWidget, QTreeWidget, QTreeWidgetItem,
    QMessageBox
)

API_URL = "http://127.0.0.1:5000"


class ScheduleWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("School Schedule")
        self.resize(800, 600)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Day tab
        self.day_tab = QWidget()
        self.day_layout = QVBoxLayout(self.day_tab)
        self.class_combo = QComboBox()
        self.class_combo.currentIndexChanged.connect(self.display_day_schedule)
        self.day_layout.addWidget(self.class_combo)

        self.day_table = QTableWidget(0, 4)
        self.day_table.setHorizontalHeaderLabels(["Lesson", "Subject", "Room", "Teacher"])
        self.day_layout.addWidget(self.day_table)

        # Week tab
        self.week_tab = QWidget()
        self.week_layout = QVBoxLayout(self.week_tab)
        self.week_tree = QTreeWidget()
        self.week_tree.setHeaderHidden(True)
        self.week_layout.addWidget(self.week_tree)

        self.tabs.addTab(self.day_tab, "Day")
        self.tabs.addTab(self.week_tab, "Week")

        self.fetch_data()

    def fetch_data(self):
        try:
            day_resp = requests.get(f"{API_URL}/api/day")
            week_resp = requests.get(f"{API_URL}/api/week")
            day_resp.raise_for_status()
            week_resp.raise_for_status()
            self.day_data = day_resp.json()
            self.week_data = week_resp.json()
        except Exception as exc:
            QMessageBox.warning(self, "Error", f"Could not fetch data: {exc}")
            self.day_data = {}
            self.week_data = {}
            return

        self.class_combo.addItems(sorted(self.day_data.keys()))
        if self.class_combo.count() > 0:
            self.class_combo.setCurrentIndex(0)
            self.display_day_schedule()
        self.display_week_schedule()

    def display_day_schedule(self):
        cls = self.class_combo.currentText()
        schedule = self.day_data.get(cls, [])
        self.day_table.setRowCount(len(schedule))
        for row, entry in enumerate(schedule):
            self.day_table.setItem(row, 0, QTableWidgetItem(str(entry['урок'])))
            self.day_table.setItem(row, 1, QTableWidgetItem(entry['предмет']))
            self.day_table.setItem(row, 2, QTableWidgetItem(entry['кабинет']))
            self.day_table.setItem(row, 3, QTableWidgetItem(entry['учитель']))
        self.day_table.resizeColumnsToContents()

    def display_week_schedule(self):
        self.week_tree.clear()
        for day, classes in self.week_data.items():
            day_item = QTreeWidgetItem([day])
            self.week_tree.addTopLevelItem(day_item)
            for cls, schedule in classes.items():
                cls_item = QTreeWidgetItem([cls])
                day_item.addChild(cls_item)
                for entry in schedule:
                    text = f"{entry['урок']}. {entry['предмет']} - {entry['кабинет']} ({entry['учитель']})"
                    cls_item.addChild(QTreeWidgetItem([text]))
            day_item.setExpanded(True)


def main():
    app = QApplication(sys.argv)
    window = ScheduleWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
