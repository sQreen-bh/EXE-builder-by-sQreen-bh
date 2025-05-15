import os
import tempfile
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sys
import subprocess
import shutil
import sv_ttk

class EXELauncherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("EXE builder")
        self.root.geometry("650x450")
        self.root.resizable(False, False)
        
        self.set_app_icon()
        sv_ttk.set_theme("dark")
        self.setup_ui()
    
    def set_app_icon(self):
        icon_paths = [
            'icon.ico',
            os.path.join(os.path.dirname(__file__), 'icon.ico'),
            os.path.join(sys._MEIPASS, 'icon.ico') if hasattr(sys, '_MEIPASS') else None
        ]
        
        for path in icon_paths:
            if path and os.path.exists(path):
                try:
                    self.root.iconbitmap(path)
                    break
                except:
                    continue

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        header = ttk.Label(
            main_frame, 
            text="Склейка exe файлов", 
            font=('Segoe UI', 14, 'bold')
        )
        header.pack(pady=(0, 20))
        
        self.create_file_selector(main_frame, "Первый EXE файл:", "file1")
        self.create_file_selector(main_frame, "Второй EXE файл:", "file2")
        self.create_file_selector(main_frame, "Сохранить файл как:", "output", is_output=True)
        self.create_file_selector(main_frame, "Иконка для лаунчера:", "icon", is_icon=True)
        
        create_btn = ttk.Button(
            main_frame, 
            text="Создать файл", 
            command=self.create_launcher,
            style='Accent.TButton'
        )
        create_btn.pack(pady=20, ipadx=10, ipady=5)
        
        self.status = ttk.Label(
            main_frame, 
            text="Выберите EXE файлы, укажите выходной файл и иконку",
            foreground="#888"
        )
        self.status.pack(fill=tk.X, pady=(10, 0))
    
    def create_file_selector(self, parent, label_text, field_name, is_output=False, is_icon=False):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=5)
        
        label = ttk.Label(frame, text=label_text, width=20)
        label.pack(side=tk.LEFT)
        
        entry = ttk.Entry(frame)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        setattr(self, f"entry_{field_name}", entry)
        
        browse_text = "Выбрать иконку" if is_icon else "Сохранить..." if is_output else "Обзор..."
        filetypes = (("Icon files", "*.ico"),) if is_icon else (("Executable files", "*.exe"), ("All files", "*.*"))
        
        browse_btn = ttk.Button(
            frame, 
            text=browse_text, 
            width=12,
            command=lambda: self.browse_file(entry, is_output, is_icon)
        )
        browse_btn.pack(side=tk.RIGHT)
    
    def browse_file(self, entry_widget, is_output=False, is_icon=False):
        if is_icon:
            filename = filedialog.askopenfilename(
                title="Выберите файл иконки",
                filetypes=(("Icon files", "*.ico"), ("All files", "*.*")))
        elif is_output:
            filename = filedialog.asksaveasfilename(
                title="Сохранить лаунчер как",
                defaultextension=".exe",
                filetypes=(("Executable files", "*.exe"), ("All files", "*.*")))
        else:
            filename = filedialog.askopenfilename(
                title="Выберите EXE файл",
                filetypes=(("Executable files", "*.exe"), ("All files", "*.*")))
        
        if filename:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, filename)
    
    def create_launcher(self):
        file1 = self.entry_file1.get()
        file2 = self.entry_file2.get()
        output_file = self.entry_output.get()
        icon_file = self.entry_icon.get()

        if not all([file1, file2, output_file]):
            messagebox.showerror("Ошибка", "Пожалуйста, укажите EXE файлы и выходной файл!")
            return

        try:
            for path in [file1, file2]:
                if not os.path.exists(path):
                    messagebox.showerror("Ошибка", f"Файл не найден: {path}")
                    return

            self.status.config(text="Создание лаунчера...")
            self.root.update()
            
            script_path = self.create_launcher_script(file1, file2)
            
            if self.build_exe(script_path, output_file, icon_file):
                self.status.config(text=f"Лаунчер успешно создан: {output_file}")
                messagebox.showinfo(
                    "Готово", 
                    "Склеинный exe файл успешно создан!\n\n"
                )
        except Exception as e:
            self.status.config(text="Ошибка при создании файла")
            messagebox.showerror("Ошибка", f"Произошла ошибка:\n{str(e)}")
        finally:
            if 'script_path' in locals() and os.path.exists(script_path):
                try:
                    os.remove(script_path)
                except:
                    pass
    
    def create_launcher_script(self, file1, file2):
        file1_escaped = file1.replace('\\', '\\\\').replace("'", "\\'")
        file2_escaped = file2.replace('\\', '\\\\').replace("'", "\\'")
        
        script_content = f"""import os
import subprocess
import sys
import ctypes

def run_programs():
    try:
        if sys.platform == 'win32':
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        
        subprocess.Popen([r'{file1_escaped}'], shell=True)
        subprocess.Popen([r'{file2_escaped}'], shell=True)
    except Exception as e:
        with open('launcher_error.log', 'w') as f:
            f.write(f"Ошибка: {{e}}")

if __name__ == '__main__':
    run_programs()
"""
        script_path = os.path.join(tempfile.gettempdir(), "exe_launcher_temp.py")
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        return script_path
    
    def build_exe(self, script_path, output_path, icon_path=None):
        try:
            build_dir = os.path.join(tempfile.gettempdir(), 'pyi_build')
            spec_dir = os.path.join(tempfile.gettempdir(), 'pyi_spec')
            
            os.makedirs(build_dir, exist_ok=True)
            os.makedirs(spec_dir, exist_ok=True)
            
            if icon_path:
                icon_path = os.path.abspath(icon_path)
                if not os.path.isfile(icon_path):
                    messagebox.showwarning("Предупреждение", "Файл иконки не найден, сборка без иконки")
                    icon_path = None
                elif not icon_path.lower().endswith('.ico'):
                    messagebox.showwarning("Предупреждение", "Рекомендуется использовать файл .ico, сборка без иконки")
                    icon_path = None
            
            cmd = [
                sys.executable,
                '-m',
                'PyInstaller',
                '--onefile',
                '--windowed',
                '--name', os.path.splitext(os.path.basename(output_path))[0],
                '--distpath', os.path.dirname(output_path),
                '--workpath', build_dir,
                '--specpath', spec_dir,
                '--clean',
                script_path
            ]

            if icon_path:
                cmd.extend(['--icon', icon_path])
            
            print("Executing:", " ".join(cmd))
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            
            if result.returncode != 0:
                error_msg = result.stderr if result.stderr else "Неизвестная ошибка PyInstaller"
                raise Exception(f"PyInstaller error:\n{error_msg}")
            
            if not os.path.exists(output_path):
                raise Exception(f"Выходной файл не был создан: {output_path}")
            
            return True
        except subprocess.CalledProcessError as e:
            raise Exception(f"Ошибка сборки EXE: {e.stderr}")
        except Exception as e:
            raise Exception(f"Ошибка: {str(e)}")
        finally:
            shutil.rmtree(build_dir, ignore_errors=True)
            shutil.rmtree(spec_dir, ignore_errors=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = EXELauncherApp(root)
    root.mainloop()
