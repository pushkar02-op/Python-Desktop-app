# gui.py
import tkinter as tk
from tkinter import messagebox
import subprocess
import sys

def start_flask_app():
    db_host = db_host_entry.get()
    db_password = db_password_entry.get()

    if not db_host or not db_password:
        messagebox.showwarning("Input Error", "Please enter both DB_HOST and DB_PASSWORD")
        return

    subprocess.Popen([sys.executable, "main.py", db_host, db_password])

    root.destroy()

root = tk.Tk()
root.title("Flask App Configuration")

tk.Label(root, text="DB_HOST:").grid(row=0, column=0)
db_host_entry = tk.Entry(root)
db_host_entry.grid(row=0, column=1)

tk.Label(root, text="DB_PASSWORD:").grid(row=1, column=0)
db_password_entry = tk.Entry(root, show="*")
db_password_entry.grid(row=1, column=1)

tk.Button(root, text="Start Flask App", command=start_flask_app).grid(row=2, column=0, columnspan=2)

root.mainloop()
