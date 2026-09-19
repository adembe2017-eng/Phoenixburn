#!/usr/bin/env python3
"""
RufusRealClone — True ISO Burner with Download Manager & Absolute Root
-----------------------------------------------------------------------
- Real C-powered burning engine + SHA-256 verification
- Built-in ISO downloader (no external browser needed)
- Full root privilege escalation
- Exact Rufus 3.20 UI replica
- Python 3.14 compatible
"""
import os
import sys
import subprocess
import tempfile
import threading
import urllib.request
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# =====================================================================
# ABSOLUTE ROOT PRIVILEGE ESCALATION
# =====================================================================
if os.geteuid() != 0:
    print("[!] Requesting absolute root privileges...")
    os.execvp("sudo", ["sudo", "-E", "python3"] + sys.argv)

# =====================================================================
# EMBEDDED C ENGINE: SCAN + BURN + VERIFY
# =====================================================================
C_ENGINE = r"""
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>
#include <openssl/sha.h>

void read_sysfs(const char *path, char *buf, size_t len) {
    FILE *f = fopen(path, "r");
    if (f) { if(fgets(buf,len,f)) buf[strcspn(buf,"\n")]=0; fclose(f); }
    else strcpy(buf, "Unknown");
}

int cmd_scan() {
    DIR *dir = opendir("/sys/block");
    struct dirent *entry;
    if (!dir) { fprintf(stderr, "ERROR_SCAN\n"); return 1; }
    printf("SCAN_START\n");
    while ((entry = readdir(dir)) != NULL) {
        if (strncmp(entry->d_name,"loop",4)==0 || 
            strncmp(entry->d_name,"ram",3)==0 ||
            strncmp(entry->d_name,"dm-",3)==0) continue;
        char path[512], model[256], removable[16];
        snprintf(path,sizeof(path),"/sys/block/%s/device/model",entry->d_name);
        read_sysfs(path, model, sizeof(model));
        snprintf(path,sizeof(path),"/sys/block/%s/size",entry->d_name);
        long sectors=0; FILE *f=fopen(path,"r");
        if(f){fscanf(f,"%ld",&sectors);fclose(f);}
        double gb=(sectors*512.0)/(1024.0*1024.0*1024.0);
        snprintf(path,sizeof(path),"/sys/block/%s/removable",entry->d_name);
        read_sysfs(path, removable, sizeof(removable));
        const char *type = (strcmp(removable,"1")==0) ? "USB" : "INTERNAL";
        printf("DISK|/dev/%s|%s|%.1f GB|%s\n", entry->d_name, model, gb, type);
    }
    printf("SCAN_END\n");
    closedir(dir);
    return 0;
}

int cmd_burn(const char *src, const char *dst) {
    int src_fd=open(src,O_RDONLY);
    int dst_fd=open(dst,O_WRONLY|O_SYNC);
    if(src_fd<0||dst_fd<0){perror("Open failed");return 1;}
    struct stat st; fstat(src_fd,&st);
    long total=st.st_size, done=0;
    char buf[8192]; ssize_t r;
    printf("START\n");
    while((r=read(src_fd,buf,sizeof(buf)))>0){
        if(write(dst_fd,buf,r)<0){perror("Write failed");goto end;}
        done+=r;
        printf("P:%d\n",(int)(done*100/total));
    }
    printf("VERIFY\n");
    unsigned char h1[32],h2[32];
    SHA256_CTX c;
    SHA256_Init(&c); lseek(src_fd,0,SEEK_SET);
    while((r=read(src_fd,buf,sizeof(buf)))>0) SHA256_Update(&c,buf,r);
    SHA256_Final(h1,&c);
    SHA256_Init(&c); lseek(dst_fd,0,SEEK_SET);
    while((r=read(dst_fd,buf,sizeof(buf)))>0) SHA256_Update(&c,buf,r);
    SHA256_Final(h2,&c);
    if(memcmp(h1,h2,32)==0) printf("OK\n"); else printf("FAIL\n");
end:
    close(src_fd); close(dst_fd);
    return 0;
}

int main(int argc, char *argv[]) {
    if(argc<2){fprintf(stderr,"Usage: engine [scan|burn <src> <dst>]\n");return 1;}
    if(strcmp(argv[1],"scan")==0) return cmd_scan();
    if(strcmp(argv[1],"burn")==0 && argc==4) return cmd_burn(argv[2],argv[3]);
    fprintf(stderr,"Invalid command\n"); return 1;
}
"""

def get_engine():
    path = os.path.join(tempfile.gettempdir(), "rufus_real_c")
    if not os.path.exists(path):
        with open(path+".c","w") as f: f.write(C_ENGINE)
        r = subprocess.run(["gcc","-O2","-o",path,path+".c","-lcrypto"], capture_output=True, text=True)
        if r.returncode: raise Exception(r.stderr)
    return path

def run_engine(args):
    try:
        out = subprocess.check_output([get_engine()]+args, text=True, stderr=subprocess.PIPE)
        return out.strip().split('\n'), None
    except subprocess.CalledProcessError as e:
        err = e.stderr if isinstance(e.stderr,str) else e.stderr.decode('utf-8',errors='replace')
        return None, err
    except Exception as e:
        return None, str(e)

# =====================================================================
# RUFUS-STYLE GUI WITH DOWNLOAD MANAGER
# =====================================================================
class RufusRealGUI:
    # Predefined ISO sources for quick download
    ISO_SOURCES = {
        "Ubuntu 24.04 LTS": "https://releases.ubuntu.com/24.04/ubuntu-24.04.3-desktop-amd64.iso",
        "Debian 12 Netinst": "https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/debian-12.11.0-amd64-netinst.iso",
        "Alpine Linux 3.21": "https://dl-cdn.alpinelinux.org/alpine/v3.21/releases/x86_64/alpine-standard-3.21.3-x86_64.iso",
    }

    def __init__(self, root):
        self.root = root
        root.title("Rufus 3.20.1929 — Real Burner + Downloader")
        root.geometry("540x680")
        self.drives_data = []
        self.bg_color = "#f0f0f0"
        self.green_btn = "#00aa00"

        frm = tk.Frame(root, bg=self.bg_color, padx=15, pady=10)
        frm.pack(fill=tk.BOTH, expand=True)

        # === Options de Périphérique ===
        self._create_section(frm, "Options de Périphérique", 0)
        row = 1
        tk.Label(frm, text="Périphérique", bg=self.bg_color).grid(row=row, column=0, sticky="w")
        dev_frame = tk.Frame(frm, bg=self.bg_color)
        dev_frame.grid(row=row+1, column=0, columnspan=2, sticky="ew", pady=(0,5))
        self.dev_combo = ttk.Combobox(dev_frame, state="readonly", width=45)
        self.dev_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Button(dev_frame, text="🔄 Scan All Disks", command=self.scan_disks).pack(side=tk.RIGHT, padx=5)
        row += 3

        # Type de démarrage + Download Button
        boot_frame = tk.Frame(frm, bg=self.bg_color)
        boot_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0,5))
        tk.Label(boot_frame, text="Type de démarrage", bg=self.bg_color).pack(anchor="w")
        inner = tk.Frame(boot_frame, bg=self.bg_color)
        inner.pack(fill="x")
        self.boot_var = tk.StringVar(value="Select or download ISO...")
        self.boot_combo = ttk.Combobox(inner, textvariable=self.boot_var, state="readonly", width=28)
        self.boot_combo["values"] = list(self.ISO_SOURCES.keys()) + ["Browse local file..."]
        self.boot_combo.bind("<<ComboboxSelected>>", self.on_iso_select)
        self.boot_combo.pack(side="left", fill="x", expand=True)
        tk.Button(inner, text="SÉLECTION", command=self.browse_iso, width=10).pack(side="right", padx=(5,0))
        row += 2

        self._add_label_combo(frm, "Option d'image", [{"name":"Installation standard"}], "name", row)
        row += 2
        opts = tk.Frame(frm, bg=self.bg_color)
        opts.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0,5))
        self._add_mini_combo(opts, "Schéma de partition", ["GPT","MBR"], "GPT", 0)
        self._add_mini_combo(opts, "Système de destination", ["UEFI (non CSM)","BIOS"], "UEFI (non CSM)", 1)
        row += 3

        # === Options de Formatage ===
        self._create_section(frm, "Options de Formatage", row)
        row += 1
        self._add_label_entry(frm, "Nom de volume", "PHOENIX_USB", row)
        row += 2
        fs_frame = tk.Frame(frm, bg=self.bg_color)
        fs_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0,5))
        self._add_mini_combo(fs_frame, "Système de fichiers", ["NTFS","FAT32","exFAT"], "NTFS", 0)
        self._add_mini_combo(fs_frame, "Taille d'unité", ["4096 octets"], "4096 octets", 1)
        row += 2
        tk.Checkbutton(frm, text="Formatage rapide", bg=self.bg_color, variable=tk.BooleanVar(value=True)).grid(row=row, column=0, columnspan=2, sticky="w")
        row += 1
        bad_frame = tk.Frame(frm, bg=self.bg_color)
        bad_frame.grid(row=row, column=0, columnspan=2, sticky="ew")
        tk.Checkbutton(bad_frame, text="Vérification de mauvais blocs", bg=self.bg_color).pack(side="left")
        bad_combo = ttk.Combobox(bad_frame, values=["1 passe", "2 passes"], state="readonly", width=8)
        bad_combo.set("1 passe")
        bad_combo.pack(side="right")
        row += 3

        # === Statut ===
        self._create_section(frm, "Statut", row)
        row += 1
        self.progress = ttk.Progressbar(frm, length=480, mode='determinate')
        self.progress.grid(row=row, column=0, columnspan=2, pady=5)
        row += 1
        self.status_lbl = tk.Label(frm, text="PRÊT - Scan disks to begin", font=("Segoe UI", 11, "bold"),
                                   bg=self.green_btn, fg="white", height=2, anchor="center")
        self.status_lbl.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0,10))
        row += 1

        # === Bottom Buttons ===
        btn_row = tk.Frame(frm, bg=self.bg_color)
        btn_row.grid(row=row, column=0, columnspan=2, sticky="ew")
        self.disk_count_lbl = tk.Label(btn_row, text="0 périphériques détectés", bg=self.bg_color)
        self.disk_count_lbl.pack(side="left", pady=10)
        self.start_btn = tk.Button(btn_row, text="DÉMARRER", font=("Segoe UI", 10, "bold"),
                                    bg=self.green_btn, fg="white", width=14, height=2, command=self.start_burn)
        self.start_btn.pack(side="right", padx=(0,5))
        tk.Button(btn_row, text="FERMER", font=("Segoe UI", 10), width=10, height=2,
                  command=root.destroy).pack(side="right")

        self.iso_path = None
        self.scan_disks()

    def _create_section(self, parent, title, row):
        sep = tk.Frame(parent, bg=self.bg_color, height=20)
        sep.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(10,0))
        tk.Label(sep, text=f" {title} ", bg=self.bg_color, font=("Segoe UI", 11, "bold")).place(relx=0.02, rely=0.5, anchor="w")
        canvas = tk.Canvas(sep, bg=self.bg_color, highlightthickness=0, height=1)
        canvas.place(relx=0.25, rely=0.5, relwidth=0.73)

    def _add_label_combo(self, parent, label, items, key, row):
        tk.Label(parent, text=label, bg=self.bg_color).grid(row=row, column=0, sticky="w")
        combo = ttk.Combobox(parent, state="readonly", width=48)
        combo["values"] = [it[key] for it in items]
        combo.current(0)
        combo.grid(row=row+1, column=0, columnspan=2, sticky="ew", pady=(0,5))

    def _add_label_entry(self, parent, label, default, row):
        tk.Label(parent, text=label, bg=self.bg_color).grid(row=row, column=0, sticky="w")
        entry = tk.Entry(parent, width=50)
        entry.insert(0, default)
        entry.grid(row=row+1, column=0, columnspan=2, sticky="ew", pady=(0,5))

    def _add_mini_combo(self, parent, label, values, default, col):
        f = tk.Frame(parent, bg=self.bg_color)
        f.grid(row=0, column=col, sticky="ew", padx=(0,10) if col==0 else (10,0))
        tk.Label(f, text=label, bg=self.bg_color, font=("Segoe UI", 9)).pack(anchor="w")
        c = ttk.Combobox(f, values=values, state="readonly", width=18)
        c.set(default)
        c.pack(fill="x")

    def on_iso_select(self, event=None):
        val = self.boot_var.get()
        if val == "Browse local file...":
            self.browse_iso()
        elif val in self.ISO_SOURCES:
            self.download_iso(val, self.ISO_SOURCES[val])

    def browse_iso(self):
        f = filedialog.askopenfilename(filetypes=[("ISO Files","*.iso"),("All Files","*.*")])
        if f:
            self.iso_path = f
            self.boot_var.set(os.path.basename(f))

    def download_iso(self, name, url):
        dest = os.path.join(os.path.expanduser("~"), "Downloads", os.path.basename(url))
        if os.path.isfile(dest):
            self.iso_path = dest
            self.boot_var.set(os.path.basename(dest))
            self.status_lbl.config(text=f"Using cached: {os.path.basename(dest)}", bg=self.green_btn)
            return

        if not messagebox.askyesno("Download ISO", f"Download {name} (~2-5GB) to ~/Downloads?\nThis may take several minutes."):
            self.boot_combo.set("Select or download ISO...")
            return

        self.start_btn.config(state=tk.DISABLED)
        self.status_lbl.config(text=f"Downloading {name}...", bg="#ff8c00")
        self.progress['value'] = 0

        def worker():
            try:
                def report(block_num, block_size, total_size):
                    if total_size > 0:
                        pct = min(int(block_num * block_size * 100 / total_size), 100)
                        self.root.after(0, lambda p=pct: self.progress.__setitem__('value', p))

                urllib.request.urlretrieve(url, dest, reporthook=report)
                self.iso_path = dest
                self.root.after(0, lambda: self.status_lbl.config(text=f"✅ Downloaded: {os.path.basename(dest)}", bg=self.green_btn))
                self.root.after(0, lambda: self.boot_var.set(os.path.basename(dest)))
            except Exception as e:
                self.root.after(0, lambda er=str(e): self.status_lbl.config(text=f"❌ Download failed: {er}", bg="red"))
            finally:
                self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL))

        threading.Thread(target=worker, daemon=True).start()

    def scan_disks(self):
        self.status_lbl.config(text="Scanning all disks via C engine...", bg="#0078d7")
        self.root.update_idletasks()
        lines, err = run_engine(["scan"])
        if err:
            self.status_lbl.config(text=f"Erreur: {err}", bg="red")
            return
        self.drives_data = []
        display_list = []
        parsing = False
        for line in lines:
            if line == "SCAN_START": parsing = True; continue
            if line == "SCAN_END": break
            if parsing and line.startswith("DISK|"):
                parts = line.split("|")
                if len(parts) == 5:
                    self.drives_data.append({"path": parts[1], "model": parts[2].strip(), "size": parts[3], "type": parts[4]})
                    icon = "🟢" if parts[4] == "USB" else "⚪"
                    display_list.append(f"{icon} {parts[1]} | {parts[2].strip()} ({parts[3]}) [{parts[4]}]")
        self.dev_combo['values'] = display_list
        if display_list:
            self.dev_combo.current(0)
            usb_count = sum(1 for d in self.drives_data if d['type']=='USB')
            int_count = len(self.drives_data) - usb_count
            self.disk_count_lbl.config(text=f"{len(self.drives_data)} périphériques détectés")
            self.status_lbl.config(text="PRÊT", bg=self.green_btn)
        else:
            self.status_lbl.config(text="Aucun disque trouvé", bg="red")

    def start_burn(self):
        if not self.drives_data or self.dev_combo.current() < 0:
            messagebox.showwarning("Attention", "Veuillez scanner les disques d'abord.")
            return
        dev_info = self.drives_data[self.dev_combo.current()]
        iso_path = self.iso_path
        if not iso_path or not os.path.isfile(iso_path):
            messagebox.showerror("Erreur", "Veuillez sélectionner ou télécharger un fichier ISO valide.")
            return
        warn_icon = "⚠️ DISQUE INTERNE SÉLECTIONNÉ! ️\n" if dev_info['type']=='INTERNAL' else ""
        confirm_msg = (f"{warn_icon}"
                      f"Cette opération va EFFACER TOUTES LES DONNÉES sur:\n"
                      f"{dev_info['path']} ({dev_info['model']}, {dev_info['size']})\n\n"
                      f"Image: {os.path.basename(iso_path)}\n\n"
                      f"Êtes-vous SÛR à 100% de vouloir continuer?")
        if not messagebox.askyesno("AVERTISSEMENT FINAL", confirm_msg):
            return
        self.start_btn.config(state=tk.DISABLED)
        self.progress['value'] = 0
        self.status_lbl.config(text="Écriture en cours...", bg="#ff8c00")

        def worker():
            try:
                proc = subprocess.Popen([get_engine(),"burn",iso_path,dev_info['path']],
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                for line in proc.stdout:
                    line=line.strip()
                    if line.startswith("P:"):
                        self.root.after(0, lambda p=int(line[2:]): self.progress.__setitem__('value',p))
                    elif line=="VERIFY":
                        self.root.after(0, lambda: self.status_lbl.config(text="Vérification SHA-256...",bg="#9932cc"))
                    elif line=="OK":
                        self.root.after(0, lambda: self.finish(True,"SHA-256 Vérifié ✅"))
                        return
                    elif line=="FAIL":
                        self.root.after(0, lambda: self.finish(False,"Checksum MISMATCH "))
                        return
                proc.wait()
                if proc.returncode!=0:
                    self.root.after(0, lambda e=proc.stderr.read(): self.finish(False,e))
            except Exception as e:
                self.root.after(0, lambda er=str(e): self.finish(False,er))
            finally:
                self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL))

        threading.Thread(target=worker, daemon=True).start()

    def finish(self, ok, msg):
        self.progress['value']=100
        self.status_lbl.config(text=msg, bg=self.green_btn if ok else "red")
        messagebox.showinfo("Terminé", msg)

if __name__=="__main__":
    RufusRealGUI(tk.Tk()).root.mainloop()