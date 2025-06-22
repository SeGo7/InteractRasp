import tkinter as tk
from tkinter import ttk
import requests

API_URL = 'http://127.0.0.1:5000'

class ScheduleApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('School Schedule')
        self.geometry('700x400')

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True)

        self.day_frame = ttk.Frame(self.notebook)
        self.week_frame = ttk.Frame(self.notebook)

        self.notebook.add(self.day_frame, text='Day')
        self.notebook.add(self.week_frame, text='Week')

        # Widgets for day view
        self.class_var = tk.StringVar()
        self.class_combo = ttk.Combobox(self.day_frame, textvariable=self.class_var)
        self.class_combo.pack(pady=10)
        self.class_combo.bind('<<ComboboxSelected>>', self.display_day_schedule)

        self.day_tree = ttk.Treeview(self.day_frame, columns=('lesson', 'subject', 'room', 'teacher'), show='headings')
        for col in self.day_tree['columns']:
            self.day_tree.heading(col, text=col.capitalize())
        self.day_tree.pack(fill='both', expand=True)

        # Widgets for week view
        self.week_text = tk.Text(self.week_frame)
        self.week_text.pack(fill='both', expand=True)

        self.fetch_data()

    def fetch_data(self):
        try:
            day_resp = requests.get(f'{API_URL}/api/day')
            week_resp = requests.get(f'{API_URL}/api/week')
            day_resp.raise_for_status()
            week_resp.raise_for_status()
            self.day_data = day_resp.json()
            self.week_data = week_resp.json()
        except Exception as exc:
            self.day_data = {}
            self.week_data = {}
            self.week_text.insert('1.0', f'Error fetching data: {exc}')
            return
        self.class_combo['values'] = sorted(self.day_data.keys())
        if self.class_combo['values']:
            self.class_combo.current(0)
            self.display_day_schedule()
        self.display_week_schedule()

    def display_day_schedule(self, event=None):
        for i in self.day_tree.get_children():
            self.day_tree.delete(i)
        cls = self.class_var.get()
        for entry in self.day_data.get(cls, []):
            self.day_tree.insert('', 'end', values=(entry['урок'], entry['предмет'], entry['кабинет'], entry['учитель']))

    def display_week_schedule(self):
        self.week_text.delete('1.0', tk.END)
        for day, classes in self.week_data.items():
            self.week_text.insert(tk.END, f'{day}\n')
            for cls, schedule in classes.items():
                self.week_text.insert(tk.END, f'  {cls}\n')
                for entry in schedule:
                    line = f"    {entry['урок']}. {entry['предмет']} - {entry['кабинет']} ({entry['учитель']})\n"
                    self.week_text.insert(tk.END, line)
            self.week_text.insert(tk.END, '\n')

if __name__ == '__main__':
    app = ScheduleApp()
    app.mainloop()
