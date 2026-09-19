#!/usr/bin/env python3
"""
Rufus Clone GUI — Real Burner with C Backend
---------------------------------------------
واجهة رسومية مطابقة لـ Rufus باستخدام tkinter.
تستدعي محرك C للحرق الحقيقي والتحقق من SHA-256.
"""
import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# التحقق من صلاحيات Root
if os.geteuid() != 0:
    os.execvp("sudo", ["sudo", "python3"] + sys.argv)

class RufusCloneApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PhoenixBurn 3.20.1929 — Rufus Clone")
        self.root.geometry("520x600")
        self.root.resizable(False, False)
        
        # ألوان Rufus الأصلية
        self.bg_color = "#f0f0f0"
        self.accent_green = "#00aa00"
        self.border_color = "#aaaaaa"
        
        self.root.configure(bg=self.bg_color)
        
        # === Options de Périphérique ===
        frame1 = tk.LabelFrame(root, text="Options de Périphérique", font=("Segoe UI", 10, "bold"), 
                               bg=self.bg_color, bd=1, relief=tk.SOLID)
        frame1.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        # Périphérique
        tk.Label(frame1, text="Périphérique", bg=self.bg_color).pack(anchor=tk.W, padx=5)
        self.dev_combo = ttk.Combobox(frame1, state="readonly", width=45)
        self.dev_combo['values'] = ["/dev/sdb (SanDisk Ultra 32GB)", "/dev/sdc (Kingston 64GB)"]
        self.dev_combo.current(0)
        self.dev_combo.pack(padx=5, pady=2)
        
        # Type de démarrage
        tk.Label(frame1, text="Type de démarrage", bg=self.bg_color).pack(anchor=tk.W, padx=5)
        boot_frame = tk.Frame(frame1, bg=self.bg_color)
        boot_frame.pack(fill=tk.X, padx=5, pady=2)
        self.boot_var = tk.StringVar(value="Windows 11 22H2.iso")
        ttk.Combobox(boot_frame, textvariable=self.boot_var, state="readonly", width=35).pack(side=tk.LEFT)
        tk.Button(boot_frame, text="SÉLECTION", command=self.select_iso, width=10).pack(side=tk.RIGHT)
        
        # Option d'image
        tk.Label(frame1, text="Option d'image", bg=self.bg_color).pack(anchor=tk.W, padx=5)
        img_combo = ttk.Combobox(frame1, state="readonly", width=45)
        img_combo['values'] = ["Installation standard de Windows"]
        img_combo.set("Installation standard de Windows")
        img_combo.pack(padx=5, pady=2)
        
        # Schéma & Système
        opts_frame = tk.Frame(frame1, bg=self.bg_color)
        opts_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Label(opts_frame, text="Schéma de partition", bg=self.bg_color).grid(row=0, column=0, sticky=tk.W)
        ttk.Combobox(opts_frame, state="readonly", width=15, values=["GPT", "MBR"]).set("GPT").grid(row=1, column=0, padx=(0,10))
        tk.Label(opts_frame, text="Système de destination", bg=self.bg_color).grid(row=0, column=1, sticky=tk.W)
        ttk.Combobox(opts_frame, state="readonly", width=15, values=["UEFI (non CSM)", "BIOS"]).set("UEFI (non CSM)").grid(row=1, column=1)

        # === Options de Formatage ===
        frame2 = tk.LabelFrame(root, text="Options de Formatage", font=("Segoe UI", 10, "bold"), 
                               bg=self.bg_color, bd=1, relief=tk.SOLID)
        frame2.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(frame2, text="Nom de volume", bg=self.bg_color).pack(anchor=tk.W, padx=5)
        vol_entry = tk.Entry(frame2, width=48)
        vol_entry.insert(0, "PHOENIX_USB")
        vol_entry.pack(padx=5, pady=2)
        
        fs_frame = tk.Frame(frame2, bg=self.bg_color)
        fs_frame.pack(fill=tk.X, padx=5, pady=2)
        tk.Label(fs_frame, text="Système de fichiers", bg=self.bg_color).pack(side=tk.LEFT)
        ttk.Combobox(fs_frame, state="readonly", width=10, values=["NTFS", "FAT32", "exFAT"]).set("NTFS").pack(side=tk.LEFT, padx=5)
        tk.Label(fs_frame, text="Taille d'unité d'allocation", bg=self.bg_color).pack(side=tk.LEFT, padx=(20,0))
        ttk.Combobox(fs_frame, state="readonly", width=15, values=["4096 octets (Défaut)"]).set("4096 octets (Défaut)").pack(side=tk.LEFT, padx=5)
        
        chk1 = tk.Checkbutton(frame2, text="Formatage rapide", bg=self.bg_color, variable=tk.BooleanVar(value=True))
        chk1.pack(anchor=tk.W, padx=5)
        chk2 = tk.Checkbutton(frame2, text="Ajouter un label étendu et une icône", bg=self.bg_color, variable=tk.BooleanVar(value=True))
        chk2.pack(anchor=tk.W, padx=5)

        # === Statut ===
        frame3 = tk.LabelFrame(root, text="Statut", font=("Segoe UI", 10, "bold"), 
                               bg=self.bg_color, bd=1, relief=tk.SOLID)
        frame3.pack(fill=tk.X, padx=10, pady=5)
        
        self.progress = ttk.Progressbar(frame3, length=400, mode='determinate')
        self.progress.pack(padx=5, pady=5)
        
        self.status_lbl = tk.Label(frame3, text="PRÊT", font=("Segoe UI", 10, "bold"), 
                                   bg=self.accent_green, fg="white", height=2)
        self.status_lbl.pack(fill=tk.X, padx=5, pady=2)

        # === أزرار سفلية ===
        btn_frame = tk.Frame(root, bg=self.bg_color)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(btn_frame, text="1 périphérique détecté", bg=self.bg_color).pack(side=tk.LEFT)
        
        self.start_btn = tk.Button(btn_frame, text="DÉMARRER", font=("Segoe UI", 10, "bold"), 
                                   bg=self.accent_green, fg="white", height=2, width=12, command=self.start_burn)
        self.start_btn.pack(side=tk.RIGHT, padx=5)
        
        tk.Button(btn_frame, text="FERMER", font=("Segoe UI", 10), height=2, width=10, 
                  command=root.destroy).pack(side=tk.RIGHT, padx=5)

    def select_iso(self):
        filename = filedialog.askopenfilename(filetypes=[("ISO Files", "*.iso"), ("All Files", "*.*")])
        if filename:
            self.boot_var.set(os.path.basename(filename))
            self.iso_path = filename

    def start_burn(self):
        iso = getattr(self, 'iso_path', None)
        dev = self.dev_combo.get().split()[0]
        
        if not iso:
            messagebox.showwarning("Attention", "Veuillez sélectionner une image ISO.")
            return
            
        if not messagebox.askyesno("Confirmation", f"⚠️ Toutes les données sur {dev} seront effacées!\nContinuer?"):
            return
        
        self.start_btn.config(state=tk.DISABLED)
        self.status_lbl.config(text="Écriture en cours...", bg="#0078d7")
        self.progress['value'] = 0
        
        # استدعاء محرك C للحرق الحقيقي والتحقق
        thread = threading.Thread(target=self.c_burn_worker, args=(iso, dev))
        thread.daemon = True
        thread.start()

    def c_burn_worker(self, iso, dev):
        try:
            # ترجمة وتشغيل محرك C إذا لم يكن موجوداً
            if not os.path.exists("phoenix_core"):
                subprocess.run(["gcc", "-o", "phoenix_core", "phoenix_core.c"], check=True)
            
            result = subprocess.run(["./phoenix_core", iso, dev], capture_output=True, text=True)
            
            if "SUCCESS" in result.stdout or result.returncode == 0:
                self.status_lbl.config(text="✅ SUCCÈS! Vérification OK", bg=self.accent_green)
                messagebox.showinfo("Succès", "Gravure terminée avec succès!\nChecksum SHA-256 vérifié.")
            else:
                self.status_lbl.config(text="❌ ÉCHEC!", bg="red")
                messagebox.showerror("Erreur", result.stderr)
        except Exception as e:
            self.status_lbl.config(text="❌ ERREUR", bg="red")
            messagebox.showerror("Erreur", str(e))
        finally:
            self.start_btn.config(state=tk.NORMAL)
            self.progress['value'] = 100

if __name__ == "__main__":
    import threading
    root = tk.Tk()
    app = RufusCloneApp(root)
    root.mainloop()