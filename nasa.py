#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import requests
from datetime import datetime, timedelta
import json
import webbrowser
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import os
from PIL import Image, ImageTk

class AsteroidTracker:
    def __init__(self, root):
        self.root = root
        self.setup_ui()
        self.load_config()
        self.setup_plots()

    def setup_ui(self):
        self.root.title("\ud83c\udf20 NASA Asteroid Tracker Pro")
        self.root.geometry("1200x750")
        self.root.configure(bg="#0a192f")
        self.root.minsize(1000, 650)

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.configure_styles()

        self.create_menu()
        self.create_header()
        self.create_main_frame()
        self.create_status_bar()

    def configure_styles(self):
        style_configs = {
            "TFrame": {"configure": {"background": "#0a192f"}},
            "TLabel": {
                "configure": {
                    "background": "#0a192f",
                    "foreground": "#ccd6f6",
                    "font": ("Segoe UI", 10)
                }
            },
            "TButton": {
                "configure": {
                    "background": "#64ffda",
                    "foreground": "#0a192f",
                    "font": ("Segoe UI", 10, "bold"),
                    "padding": 8,
                    "borderwidth": 0
                },
                "map": {
                    "background": [("active", "#1de9b6")],
                    "foreground": [("active", "#0a192f")]
                }
            },
            "Treeview": {
                "configure": {
                    "background": "#172a45",
                    "fieldbackground": "#172a45",
                    "foreground": "#ccd6f6",
                    "rowheight": 28
                }
            },
            "Treeview.Heading": {
                "configure": {
                    "background": "#112240",
                    "foreground": "#64ffda",
                    "font": ("Segoe UI", 10, "bold"),
                    "padding": 5
                }
            },
            "TCombobox": {
                "configure": {
                    "fieldbackground": "#172a45",
                    "background": "#172a45",
                    "foreground": "#ccd6f6",
                    "selectbackground": "#1e4b7b"
                }
            }
        }

        for style, config in style_configs.items():
            self.style.configure(style, **config.get("configure", {}))
            if "map" in config:
                self.style.map(style, **config["map"])

    def create_menu(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0, bg="#112240", fg="#ccd6f6")
        file_menu.add_command(label="Load API Key", command=self.load_api_key)
        file_menu.add_command(label="Save Data", command=self.save_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        help_menu = tk.Menu(menubar, tearoff=0, bg="#112240", fg="#ccd6f6")
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="NASA API Docs", command=lambda: webbrowser.open("https://api.nasa.gov/"))
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

    def create_header(self):
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill="x", padx=10, pady=10)

        try:
            if os.path.exists("nasa_logo.png"):
                img = Image.open("nasa_logo.png").resize((60, 60), Image.LANCZOS)
                self.nasa_logo = ImageTk.PhotoImage(img)
                ttk.Label(header_frame, image=self.nasa_logo).pack(side="left", padx=(0, 15))
        except Exception:
            pass

        ttk.Label(header_frame, text="NASA Asteroid Tracker Pro", font=("Segoe UI", 18, "bold"), foreground="#64ffda").pack(side="left")

        self.date_label = ttk.Label(header_frame, text=f"Date: {datetime.now().strftime('%Y-%m-%d')}", font=("Segoe UI", 10))
        self.date_label.pack(side="right")

    def create_main_frame(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(control_frame, text="Date Range:").pack(side="left", padx=(0, 5))
        self.days_var = tk.StringVar(value="1")
        days_options = ["1", "3", "7"]
        days_dropdown = ttk.Combobox(control_frame, textvariable=self.days_var, values=days_options, state="readonly", width=5)
        days_dropdown.pack(side="left", padx=(0, 15))

        self.hazardous_only = tk.BooleanVar()
        hazardous_check = ttk.Checkbutton(control_frame, text="Show Potentially Hazardous Only", variable=self.hazardous_only)
        hazardous_check.pack(side="left", padx=(0, 15))

        ttk.Button(control_frame, text="Fetch Asteroid Data", command=self.start_fetch_thread).pack(side="left")

        results_frame = ttk.Frame(main_frame)
        results_frame.pack(fill="both", expand=True)

        self.tree_frame = ttk.Frame(results_frame)
        self.tree_frame.pack(fill="both", expand=True, side="left")

        columns = ("Name", "Size (m)", "Hazardous", "Speed (km/h)", "Miss Distance (km)", "Approach Date")
        self.tree = ttk.Treeview(self.tree_frame, columns=columns, show="headings", selectmode="extended")

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=120)
        self.tree.column("Name", width=150)
        self.tree.column("Approach Date", width=120)

        scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.plot_frame = ttk.Frame(results_frame, width=300)
        self.plot_frame.pack(fill="both", expand=True, side="right", padx=(10, 0))

        stats_frame = ttk.Frame(main_frame)
        stats_frame.pack(fill="x", pady=(10, 0))

        self.total_label = ttk.Label(stats_frame, text="Total Asteroids: 0", font=("Segoe UI", 10, "bold"), foreground="#64ffda")
        self.total_label.pack(side="left", padx=(0, 20))

        self.hazardous_label = ttk.Label(stats_frame, text="Potentially Hazardous: 0", font=("Segoe UI", 10, "bold"), foreground="#ff5555")
        self.hazardous_label.pack(side="left", padx=(0, 20))

        self.largest_label = ttk.Label(stats_frame, text="Largest: N/A", font=("Segoe UI", 10, "bold"))
        self.largest_label.pack(side="left", padx=(0, 20))

        self.fastest_label = ttk.Label(stats_frame, text="Fastest: N/A", font=("Segoe UI", 10, "bold"))
        self.fastest_label.pack(side="left")

    def create_status_bar(self):
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Frame(self.root, height=25)
        status_bar.pack(fill="x", side="bottom")
        ttk.Label(status_bar, textvariable=self.status_var, anchor="w", font=("Segoe UI", 9)).pack(fill="x", padx=10)

    def setup_plots(self):
        self.figure, self.ax = plt.subplots(figsize=(5, 4), dpi=100)
        self.figure.patch.set_facecolor("#0a192f")
        self.ax.set_facecolor("#172a45")

        for spine in self.ax.spines.values():
            spine.set_edgecolor("#64ffda")

        self.ax.tick_params(colors="#ccd6f6")
        self.ax.title.set_color("#64ffda")
        self.ax.xaxis.label.set_color("#ccd6f6")
        self.ax.yaxis.label.set_color("#ccd6f6")

        self.canvas = FigureCanvasTkAgg(self.figure, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def load_config(self):
        self.api_key = "G6NAxklvMSP6kHsNOH1Uq6Wvi7APGcmSdamCTRjd"
        try:
            if os.path.exists("config.json"):
                with open("config.json") as f:
                    config = json.load(f)
                    self.api_key = config.get("api_key", self.api_key)
        except Exception:
            pass

    def load_api_key(self):
        key = simpledialog.askstring("API Key", "Enter your NASA API key:", parent=self.root)
        if key:
            self.api_key = key.strip()
            try:
                with open("config.json", "w") as f:
                    json.dump({"api_key": self.api_key}, f)
                messagebox.showinfo("Success", "API key saved successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save API key: {str(e)}")

    def start_fetch_thread(self):
        self.status_var.set("Fetching data from NASA API...")
        threading.Thread(target=self.fetch_asteroid_data, daemon=True).start()

    def fetch_asteroid_data(self):
        try:
            days = int(self.days_var.get())
            start_date = datetime.now().strftime("%Y-%m-%d")
            end_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

            url = f"https://api.nasa.gov/neo/rest/v1/feed?start_date={start_date}&end_date={end_date}&api_key={self.api_key}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            self.process_data(data)
        except requests.exceptions.RequestException as e:
            self.status_var.set("Error fetching data")
            messagebox.showerror("API Error", f"Failed to fetch data: {str(e)}")
        except Exception as e:
            self.status_var.set("Error processing data")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def process_data(self, data):
        self.tree.delete(*self.tree.get_children())
        total_count = data.get("element_count", 0)
        hazardous_count = 0
        asteroids = []
        largest_size = 0
        largest_name = ""
        fastest_speed = 0
        fastest_name = ""

        for date in data["near_earth_objects"]:
            for asteroid in data["near_earth_objects"][date]:
                if self.hazardous_only.get() and not asteroid["is_potentially_hazardous_asteroid"]:
                    continue
                name = asteroid["name"]
                size = asteroid["estimated_diameter"]["meters"]["estimated_diameter_max"]
                hazardous = asteroid["is_potentially_hazardous_asteroid"]
                if hazardous:
                    hazardous_count += 1
                if size > largest_size:
                    largest_size = size
                    largest_name = name
                approach_data = asteroid["close_approach_data"][0] if asteroid["close_approach_data"] else {}
                if not approach_data:
                    continue
                speed = float(approach_data["relative_velocity"]["kilometers_per_hour"])
                distance = float(approach_data["miss_distance"]["kilometers"])
                approach_date = approach_data.get("close_approach_date_full", "N/A").split()[0]
                if speed > fastest_speed:
                    fastest_speed = speed
                    fastest_name = name
                asteroids.append({"name": name, "size": size, "hazardous": hazardous, "speed": speed, "distance": distance, "date": approach_date})

        self.total_label.config(text=f"Total Asteroids: {total_count}")
        self.hazardous_label.config(text=f"Potentially Hazardous: {hazardous_count}")
        self.largest_label.config(text=f"Largest: {largest_name} ({largest_size:.2f}m)")
        self.fastest_label.config(text=f"Fastest: {fastest_name} ({fastest_speed:,.0f} km/h)")

        for asteroid in asteroids:
            self.tree.insert("", "end", values=(asteroid["name"], f"{asteroid['size']:.2f}", "⚠️ Yes" if asteroid["hazardous"] else "✅ No", f"{asteroid['speed']:,.0f}", f"{asteroid['distance']:,.0f}", asteroid["date"]))

        self.update_plots(asteroids)
        self.status_var.set(f"Data loaded - {len(asteroids)} asteroids displayed")

    def update_plots(self, asteroids):
        self.ax.clear()
        if not asteroids:
            self.ax.text(0.5, 0.5, "No data to display", ha="center", va="center", color="#ccd6f6")
            self.canvas.draw()
            return
        sizes = [ast["size"] for ast in asteroids]
        self.ax.hist(sizes, bins=10, color="#64ffda", edgecolor="#0a192f")
        self.ax.set_title("Asteroid Size Distribution", color="#64ffda")
        self.ax.set_xlabel("Diameter (meters)", color="#ccd6f6")
        self.ax.set_ylabel("Count", color="#ccd6f6")
        self.canvas.draw()

    def save_data(self):
        try:
            file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
            if file_path:
                data = []
                for item in self.tree.get_children():
                    values = self.tree.item(item)["values"]
                    data.append({"Name": values[0], "Size": values[1], "Hazardous": values[2], "Speed": values[3], "Distance": values[4], "Approach Date": values[5]})
                with open(file_path, "w") as f:
                    json.dump(data, f, indent=2)
                messagebox.showinfo("Success", "Data saved successfully")
                self.status_var.set(f"Data saved to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save data: {str(e)}")
            self.status_var.set("Error saving data")

    def show_about(self):
        about_text = """
NASA Asteroid Tracker Pro

Version: 1.0.0
Developed by: Bruno Moura

This application uses NASA's Near Earth Object Web Service API
to track potentially hazardous asteroids approaching Earth.

API Documentation: https://api.nasa.gov/
        """
        messagebox.showinfo("About", about_text.strip())

if __name__ == "__main__":
    root = tk.Tk()
    app = AsteroidTracker(root)
    root.mainloop()