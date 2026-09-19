#!/usr/bin/env python3
"""
PhoenixBurn GUI — Rufus Style for AnduinOS
------------------------------------------
واجهة رسومية كاملة. لا تحتاج لكتابة أي مسار.
تبحث عن الفلاشات بصرامة وتعرضها في قائمة.
"""
import os
import sys
import json
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# التحقق من صلاحيات Root
if os.geteuid() != 0:
    print("ERROR: Please run with sudo (sudo python3 phoenixburn_gui.py)")
    sys.exit(1)

class PhoenixBurnApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PhoenixBurn v5.0 — Rufus Style")
        self.root.geometry("550x400")
        self.root.resizable(False, False)
        
        # الألوان العصرية
        self.bg_color = "#f0f0f0"
        self.accent_color = "#0078d7" # لون Rufus
        
        self.root.configure(bg=self.bg_color)
        
        # --- العنوان ---
        header = tk.Frame(root, bg=self.accent_color, height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text="PhoenixBurn", font=("Segoe UI", 20, "bold"), 
                 bg=self.accent_color, fg="white").pack(side=tk.LEFT, padx=20, pady=10)

        # --- المحتوى الرئيسي ---
        main_frame = tk.Frame(root, bg=self.bg_color, padx=30, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. اختيار الجهاز (Device)
        tk.Label(main_frame, text="Device:", font=("Segoe UI", 11, "bold"), bg=self.bg_color).pack(anchor=tk.W)
        self.drive_combo = ttk.Combobox(main_frame, state="readonly", width=50)
        self.drive_combo.pack(fill=tk.X, pady=(5, 15))
        
        btn_refresh = tk.Button(main_frame, text="🔄 Refresh Drives", command=self.refresh_drives, bg="#e0e0e0")
        btn_refresh.pack(anchor=tk.E, pady=(0, 10))

        # 2. اختيار الملف (Boot Selection)
        tk.Label(main_frame, text="Boot selection:", font=("Segoe UI", 11, "bold"), bg=self.bg_color).pack(anchor=tk.W)
        file_frame = tk.Frame(main_frame, bg=self.bg_color)
        file_frame.pack(fill=tk.X, pady=(5, 15))
        
        self.iso_var = tk.StringVar()
        tk.Entry(file_frame, textvariable=self.iso_var, state="readonly").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        tk.Button(file_frame, text="SELECT", command=self.select_iso, bg="#e0e0e0").pack(side=tk.RIGHT)

        # 3. زر البدء (Start)
        self.start_btn = tk.Button(main_frame, text="START", font=("Segoe UI", 12, "bold"), 
                                   bg=self.accent_color, fg="white", height=2, command=self.start_burn)
        self.start_btn.pack(fill=tk.X, pady=20)

        # 4. الحالة والتقدم
        self.status_lbl = tk.Label(main_frame, text="Ready", font=("Segoe UI", 9), bg=self.bg_color, fg="#555")
        self.status_lbl.pack(anchor=tk.W)
        
        self.progress = ttk.Progressbar(main_frame, length=400, mode='determinate')
        self.progress.pack(fill=tk.X, pady=5)

        # تشغيل البحث عند الافتتاح
        self.refresh_drives()

    def refresh_drives(self):
        """بحث صارم عن الفلاشات الخارجية فقط"""
        try:
            result = subprocess.run(['lsblk', '-d', '-J', '-o', 'NAME,PATH,SIZE,TYPE,RM,MODEL'], 
                                    capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            drives_list = []
            self.drives_map = {} # لتخزين المسار الحقيقي
            
            for dev in data['blockdevices']:
                if dev.get('type') == 'disk' and str(dev.get('rm')) == '1':
                    # حماية إضافية: استبعاد أقراص النظام الرئيسية
                    name = dev.get('name', '')
                    if name not in ['sda', 'nvme0n1', 'vda']:
                        display_name = f"{dev.get('model', 'USB Drive').strip()} ({dev.get('size', 'Unknown')})"
                        path = dev.get('path')
                        drives_list.append(display_name)
                        self.drives_map[display_name] = path

            if drives_list:
                self.drive_combo['values'] = drives_list
                self.drive_combo.current(0)
                self.status_lbl.config(text=f"Found {len(drives_list)} drive(s).")
            else:
                self.drive_combo['values'] = ["No USB drives found"]
                self.status_lbl.config(text="No drives detected. Check connection.")
        except Exception as e:
            self.status_lbl.config(text=f"Error: {e}")

    def select_iso(self):
        filename = filedialog.askopenfilename(filetypes=[("ISO Files", "*.iso"), ("All Files", "*.*")])
        if filename:
            self.iso_var.set(filename)

    def start_burn(self):
        selected_display = self.drive_combo.get()
        iso_file = self.iso_var.get()
        
        if "No USB" in selected_display:
            messagebox.showwarning("Warning", "Please plug in a USB drive and click Refresh.")
            return
        if not iso_file:
            messagebox.showwarning("Warning", "Please select an ISO file.")
            return
            
        device_path = self.drives_map.get(selected_display)
        
        if not messagebox.askyesno("Confirm", f"WARNING: All data on\n{selected_display}\nwill be ERASED.\nContinue?"):
            return
            
        self.start_btn.config(state=tk.DISABLED)
        self.status_lbl.config(text="Starting process...")
        self.progress['value'] = 0
        
        # تشغيل الحرق في خلفية حتى لا تتجمد الواجهة
        thread = threading.Thread(target=self.burn_worker, args=(iso_file, device_path))
        thread.daemon = True
        thread.start()

    def burn_worker(self, iso_path, dev_path):
        try:
            # فك التحميل
            subprocess.run(['umount', dev_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            total_size = os.path.getsize(iso_path)
            cmd = ['dd', f'if={iso_path}', f'of={dev_path}', 'bs=4M', 'status=progress', 'conv=fsync']
            
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                if 'bytes' in line:
                    try:
                        # محاولة استخراج النسبة المئوية من مخرجات dd
                        parts = line.split()
                        for part in parts:
                            if '%' in part:
                                pct = int(part.replace('%', ''))
                                self.progress['value'] = pct
                                self.status_lbl.config(text=f"Writing: {pct}%")
                    except:
                        pass
            
            process.wait()
            if process.returncode == 0:
                self.status_lbl.config(text="✅ Success! Safe to remove.")
                messagebox.showinfo("Success", "Burning completed successfully!")
            else:
                self.status_lbl.config(text="❌ Failed.")
                messagebox.showerror("Error", "Burning failed.")
                
        except Exception as e:
            self.status_lbl.config(text="❌ Error.")
            messagebox.showerror("Error", str(e))
        finally:
            self.start_btn.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = PhoenixBurnApp(root)
    root.mainloop()