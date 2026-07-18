import os
import sys
import shutil
import queue
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox


APP_NAME = "Stargate App Builder Pro"
APP_VERSION = "1.0"


def find_python():
    """Find a real Python interpreter, even when this app is running as an EXE."""
    candidates = []

    py_launcher = shutil.which("py")
    python_cmd = shutil.which("python")
    python3_cmd = shutil.which("python3")

    if py_launcher:
        candidates.append([py_launcher, "-3"])
    if python_cmd:
        candidates.append([python_cmd])
    if python3_cmd:
        candidates.append([python3_cmd])

    # sys.executable is safe only when running as a .py script.
    if not getattr(sys, "frozen", False):
        candidates.insert(0, [sys.executable])

    for command in candidates:
        try:
            result = subprocess.run(
                command + ["--version"],
                capture_output=True,
                text=True,
                timeout=8,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            )
            if result.returncode == 0:
                return command
        except Exception:
            pass

    return None


class AppBuilderPro(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} {APP_VERSION}")
        self.geometry("900x670")
        self.minsize(820, 600)
        self.configure(bg="#09111f")

        self.process = None
        self.log_queue = queue.Queue()
        self.building = False

        self.script_var = tk.StringVar()
        self.icon_var = tk.StringVar()
        self.output_var = tk.StringVar(
            value=os.path.join(os.path.expanduser("~"), "Desktop", "Stargate Builds")
        )
        self.name_var = tk.StringVar()
        self.onefile_var = tk.BooleanVar(value=True)
        self.windowed_var = tk.BooleanVar(value=True)
        self.clean_var = tk.BooleanVar(value=True)
        self.progress_var = tk.IntVar(value=0)
        self.status_var = tk.StringVar(value="Ready")

        self.configure_styles()
        self.build_ui()
        self.after(120, self.read_log_queue)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def configure_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Stargate.Horizontal.TProgressbar",
            troughcolor="#17243a",
            background="#1fa2ff",
            lightcolor="#1fa2ff",
            darkcolor="#1fa2ff",
            bordercolor="#17243a",
            thickness=20
        )

    def build_ui(self):
        header = tk.Frame(self, bg="#09111f")
        header.pack(fill="x", padx=25, pady=(20, 12))

        tk.Label(
            header,
            text="STARGATE",
            bg="#09111f",
            fg="#36b9ff",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w")

        tk.Label(
            header,
            text="App Builder Pro",
            bg="#09111f",
            fg="white",
            font=("Segoe UI", 25, "bold")
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Build Python applications into Windows EXE files",
            bg="#09111f",
            fg="#91a4bf",
            font=("Segoe UI", 10)
        ).pack(anchor="w", pady=(4, 0))

        panel = tk.Frame(self, bg="#111c2e")
        panel.pack(fill="x", padx=25, pady=8)

        self.add_file_row(panel, 0, "Python file (.py)", self.script_var, self.choose_script, "Choose File")
        self.add_file_row(panel, 1, "Icon file (.ico) — optional", self.icon_var, self.choose_icon, "Choose Icon")
        self.add_file_row(panel, 2, "Output folder", self.output_var, self.choose_output, "Choose Folder")

        tk.Label(
            panel,
            text="Application name",
            bg="#111c2e",
            fg="#c1cde0",
            font=("Segoe UI", 10)
        ).grid(row=3, column=0, sticky="w", padx=16, pady=(10, 4))

        name_entry = tk.Entry(
            panel,
            textvariable=self.name_var,
            bg="#0a1424",
            fg="white",
            insertbackground="white",
            relief="flat",
            font=("Segoe UI", 10)
        )
        name_entry.grid(row=4, column=0, columnspan=2, sticky="ew", padx=(16, 8), pady=(0, 14), ipady=9)

        options = tk.Frame(panel, bg="#111c2e")
        options.grid(row=5, column=0, columnspan=3, sticky="ew", padx=16, pady=(2, 14))

        self.make_check(options, "Single EXE file", self.onefile_var).pack(side="left", padx=(0, 22))
        self.make_check(options, "Windowed (no console)", self.windowed_var).pack(side="left", padx=(0, 22))
        self.make_check(options, "Clean previous build", self.clean_var).pack(side="left")

        panel.columnconfigure(0, weight=1)
        panel.columnconfigure(1, weight=1)

        progress_panel = tk.Frame(self, bg="#09111f")
        progress_panel.pack(fill="x", padx=25, pady=(8, 4))

        top_progress = tk.Frame(progress_panel, bg="#09111f")
        top_progress.pack(fill="x")

        tk.Label(
            top_progress,
            textvariable=self.status_var,
            bg="#09111f",
            fg="#c1cde0",
            font=("Segoe UI", 10)
        ).pack(side="left")

        self.percent_label = tk.Label(
            top_progress,
            text="0%",
            bg="#09111f",
            fg="#36b9ff",
            font=("Consolas", 17, "bold")
        )
        self.percent_label.pack(side="right")

        self.progress = ttk.Progressbar(
            progress_panel,
            variable=self.progress_var,
            maximum=100,
            style="Stargate.Horizontal.TProgressbar"
        )
        self.progress.pack(fill="x", pady=(6, 8))

        buttons = tk.Frame(self, bg="#09111f")
        buttons.pack(fill="x", padx=25, pady=(2, 10))

        self.build_button = self.make_button(
            buttons, "BUILD APPLICATION", self.start_build, "#1589e8", bold=True
        )
        self.build_button.pack(side="left")

        self.cancel_button = self.make_button(
            buttons, "Cancel", self.cancel_build, "#b64242"
        )
        self.cancel_button.pack(side="left", padx=10)
        self.cancel_button.config(state="disabled")

        self.open_button = self.make_button(
            buttons, "Open Output Folder", self.open_output_folder, "#32445f"
        )
        self.open_button.pack(side="left")

        log_frame = tk.Frame(self, bg="#09111f")
        log_frame.pack(fill="both", expand=True, padx=25, pady=(0, 18))

        tk.Label(
            log_frame,
            text="Build log",
            bg="#09111f",
            fg="#91a4bf",
            font=("Segoe UI", 10)
        ).pack(anchor="w", pady=(0, 5))

        self.log_text = tk.Text(
            log_frame,
            bg="#070d17",
            fg="#d8e6f8",
            insertbackground="white",
            relief="flat",
            font=("Consolas", 9),
            wrap="word",
            padx=10,
            pady=10
        )
        self.log_text.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=scrollbar.set)

    def add_file_row(self, parent, row, label, variable, command, button_text):
        base = row * 2
        tk.Label(
            parent,
            text=label,
            bg="#111c2e",
            fg="#c1cde0",
            font=("Segoe UI", 10)
        ).grid(row=base, column=0, sticky="w", padx=16, pady=(12, 4))

        entry = tk.Entry(
            parent,
            textvariable=variable,
            bg="#0a1424",
            fg="white",
            insertbackground="white",
            relief="flat",
            font=("Segoe UI", 10)
        )
        entry.grid(row=base + 1, column=0, columnspan=2, sticky="ew",
                   padx=(16, 8), pady=(0, 6), ipady=9)

        button = self.make_button(parent, button_text, command, "#2d405f")
        button.grid(row=base + 1, column=2, padx=(0, 16), pady=(0, 6))

    def make_check(self, parent, text, variable):
        return tk.Checkbutton(
            parent,
            text=text,
            variable=variable,
            bg="#111c2e",
            fg="white",
            activebackground="#111c2e",
            activeforeground="white",
            selectcolor="#0a1424",
            font=("Segoe UI", 9)
        )

    def make_button(self, parent, text, command, bg, bold=False):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg="white",
            activebackground=bg,
            activeforeground="white",
            relief="flat",
            padx=17,
            pady=9,
            cursor="hand2",
            font=("Segoe UI", 10, "bold" if bold else "normal")
        )

    def choose_script(self):
        filename = filedialog.askopenfilename(
            title="Choose Python file",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )
        if filename:
            self.script_var.set(filename)
            if not self.name_var.get().strip():
                self.name_var.set(os.path.splitext(os.path.basename(filename))[0])

    def choose_icon(self):
        filename = filedialog.askopenfilename(
            title="Choose application icon",
            filetypes=[("Icon files", "*.ico"), ("All files", "*.*")]
        )
        if filename:
            self.icon_var.set(filename)

    def choose_output(self):
        folder = filedialog.askdirectory(title="Choose output folder")
        if folder:
            self.output_var.set(folder)

    def log(self, text):
        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")

    def set_progress(self, value, status=None):
        value = max(0, min(100, int(value)))
        self.progress_var.set(value)
        self.percent_label.config(text=f"{value}%")
        if status:
            self.status_var.set(status)

    def validate_inputs(self):
        script = self.script_var.get().strip()
        icon = self.icon_var.get().strip()
        output = self.output_var.get().strip()
        name = self.name_var.get().strip()

        if not script or not os.path.isfile(script):
            messagebox.showerror("Missing Python file", "Choose a valid Python .py file.")
            return False
        if not script.lower().endswith(".py"):
            messagebox.showerror("Invalid file", "The main file must have the .py extension.")
            return False
        if icon and (not os.path.isfile(icon) or not icon.lower().endswith(".ico")):
            messagebox.showerror("Invalid icon", "Choose a valid .ico icon file.")
            return False
        if not output:
            messagebox.showerror("Missing output folder", "Choose an output folder.")
            return False
        if not name:
            messagebox.showerror("Missing name", "Enter the application name.")
            return False

        forbidden = '<>:"/\\|?*'
        if any(char in name for char in forbidden):
            messagebox.showerror("Invalid name", "Application name contains invalid Windows characters.")
            return False
        return True

    def start_build(self):
        if self.building or not self.validate_inputs():
            return

        python_command = find_python()
        if not python_command:
            messagebox.showerror(
                "Python not found",
                "Python was not found.\n\nInstall Python and enable 'Add Python to PATH', then try again."
            )
            return

        self.building = True
        self.build_button.config(state="disabled")
        self.cancel_button.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.set_progress(2, "Checking PyInstaller...")

        thread = threading.Thread(
            target=self.build_worker,
            args=(python_command,),
            daemon=True
        )
        thread.start()

    def build_worker(self, python_command):
        try:
            self.log_queue.put(("log", "Python command: " + " ".join(python_command)))
            self.log_queue.put(("progress", 7, "Checking PyInstaller..."))

            check = subprocess.run(
                python_command + ["-m", "PyInstaller", "--version"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            )

            if check.returncode != 0:
                self.log_queue.put(("log", "PyInstaller is not installed. Installing it now..."))
                self.log_queue.put(("progress", 12, "Installing PyInstaller..."))

                install = subprocess.Popen(
                    python_command + ["-m", "pip", "install", "pyinstaller"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
                )

                for line in install.stdout:
                    self.log_queue.put(("log", line.rstrip()))

                install.wait()
                if install.returncode != 0:
                    raise RuntimeError("PyInstaller installation failed.")

            script = os.path.abspath(self.script_var.get().strip())
            output = os.path.abspath(self.output_var.get().strip())
            icon = self.icon_var.get().strip()
            app_name = self.name_var.get().strip()

            os.makedirs(output, exist_ok=True)

            work_root = os.path.join(output, "_build_temp")
            spec_root = os.path.join(output, "_spec_temp")
            dist_root = output

            command = python_command + ["-m", "PyInstaller"]

            if self.onefile_var.get():
                command.append("--onefile")
            else:
                command.append("--onedir")

            if self.windowed_var.get():
                command.append("--windowed")
            else:
                command.append("--console")

            if self.clean_var.get():
                command.append("--clean")

            command += [
                "--noconfirm",
                "--name", app_name,
                "--distpath", dist_root,
                "--workpath", work_root,
                "--specpath", spec_root
            ]

            if icon:
                command += ["--icon", os.path.abspath(icon)]

            command.append(script)

            self.log_queue.put(("log", ""))
            self.log_queue.put(("log", "Build command:"))
            self.log_queue.put(("log", subprocess.list2cmdline(command)))
            self.log_queue.put(("log", ""))
            self.log_queue.put(("progress", 22, "Building application..."))

            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=os.path.dirname(script),
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            )

            progress = 22
            for line in self.process.stdout:
                text = line.rstrip()
                self.log_queue.put(("log", text))

                lower = text.lower()
                if "analyzing" in lower:
                    progress = max(progress, 35)
                elif "processing" in lower:
                    progress = max(progress, 50)
                elif "building pyz" in lower:
                    progress = max(progress, 62)
                elif "building pkg" in lower:
                    progress = max(progress, 74)
                elif "building exe" in lower:
                    progress = max(progress, 86)
                elif "completed successfully" in lower:
                    progress = 96

                self.log_queue.put(("progress", progress, "Building application..."))

            self.process.wait()

            if self.process.returncode == 0:
                final_path = (
                    os.path.join(output, app_name + ".exe")
                    if self.onefile_var.get()
                    else os.path.join(output, app_name)
                )
                self.log_queue.put(("progress", 100, "Build completed successfully"))
                self.log_queue.put(("log", ""))
                self.log_queue.put(("log", "SUCCESS"))
                self.log_queue.put(("log", f"Output: {final_path}"))
                self.log_queue.put(("success", final_path))
            else:
                raise RuntimeError(f"PyInstaller exited with code {self.process.returncode}.")

        except Exception as error:
            self.log_queue.put(("progress", 0, "Build failed"))
            self.log_queue.put(("log", ""))
            self.log_queue.put(("log", f"ERROR: {error}"))
            self.log_queue.put(("error", str(error)))
        finally:
            self.process = None
            self.log_queue.put(("finished",))

    def read_log_queue(self):
        try:
            while True:
                item = self.log_queue.get_nowait()
                kind = item[0]

                if kind == "log":
                    self.log(item[1])
                elif kind == "progress":
                    self.set_progress(item[1], item[2])
                elif kind == "success":
                    messagebox.showinfo(
                        "Build completed",
                        f"Application built successfully.\n\n{item[1]}"
                    )
                elif kind == "error":
                    messagebox.showerror(
                        "Build failed",
                        f"The application could not be built.\n\n{item[1]}\n\nCheck the build log."
                    )
                elif kind == "finished":
                    self.building = False
                    self.build_button.config(state="normal")
                    self.cancel_button.config(state="disabled")
        except queue.Empty:
            pass

        self.after(120, self.read_log_queue)

    def cancel_build(self):
        if self.process and self.process.poll() is None:
            if messagebox.askyesno("Cancel build", "Stop the current build process?"):
                try:
                    self.process.terminate()
                    self.log("Build cancelled by user.")
                    self.set_progress(0, "Build cancelled")
                except Exception as error:
                    messagebox.showerror("Cancel failed", str(error))

    def open_output_folder(self):
        folder = self.output_var.get().strip()
        if not folder:
            return
        os.makedirs(folder, exist_ok=True)
        try:
            os.startfile(folder)
        except Exception as error:
            messagebox.showerror("Cannot open folder", str(error))

    def on_close(self):
        if self.building:
            close = messagebox.askyesno(
                "Build in progress",
                "A build is currently running. Close App Builder Pro anyway?"
            )
            if not close:
                return
            if self.process and self.process.poll() is None:
                try:
                    self.process.terminate()
                except Exception:
                    pass
        self.destroy()


if __name__ == "__main__":
    app = AppBuilderPro()
    app.mainloop()
