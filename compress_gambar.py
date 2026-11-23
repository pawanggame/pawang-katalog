import os
import sys
import json
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageOps

# ==============================================================================
# PAWANG GAME STORE - GUI KOMPRES GAMBAR IN-PLACE
# Taruh di folder mana saja -> otomatis scan folder tempat file ini berada
# (beserta seluruh subfoldernya), tanpa pindah folder / ubah nama file.
# ==============================================================================

LOG_FILENAME = ".compressed_cache.json"
MAX_COVER_PX = 500
MAX_PREVIEW_PX = 1280
JPEG_QUALITY = 82


def get_app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def format_mb(num_bytes):
    return f"{num_bytes / (1024 * 1024):.2f} MB"


class ImageCompressorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Kompres Gambar Otomatis - Pawang Game")
        self.root.geometry("700x520")
        self.root.minsize(580, 440)
        self.root.configure(bg="#111827")

        self.target_dir = tk.StringVar(value=get_app_dir())
        self.status_var = tk.StringVar(value="Siap memindai folder saat ini.")
        self.is_running = False
        self.stop_flag = False

        self._build_ui()
        self._center_window()

    def _center_window(self):
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self):
        pad = {"padx": 16}

        # Header
        hdr = tk.Frame(self.root, bg="#1F2937", pady=12)
        hdr.pack(fill="x")
        tk.Label(
            hdr,
            text="KOMPRES GAMBAR IN-PLACE",
            font=("Segoe UI", 14, "bold"),
            fg="#FFFFFF",
            bg="#1F2937",
        ).pack(side="left", padx=16)
        tk.Label(
            hdr,
            text="Cover ≤ 500px  •  Preview ≤ 1280px",
            font=("Segoe UI", 9, "bold"),
            fg="#4ADE80",
            bg="#1F2937",
        ).pack(side="right", padx=16)

        # Folder Picker
        dir_frame = tk.Frame(self.root, bg="#111827")
        dir_frame.pack(fill="x", pady=(14, 8), **pad)

        tk.Label(
            dir_frame,
            text="Folder Target (Otomatis folder lokasi script ini):",
            font=("Segoe UI", 10, "bold"),
            fg="#D1D5DB",
            bg="#111827",
        ).pack(anchor="w", pady=(0, 5))

        row = tk.Frame(dir_frame, bg="#111827")
        row.pack(fill="x")

        self.entry_dir = tk.Entry(
            row,
            textvariable=self.target_dir,
            font=("Segoe UI", 10),
            bg="#1F2937",
            fg="#F9FAFB",
            insertbackground="#FFFFFF",
            relief="flat",
            bd=6,
        )
        self.entry_dir.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.btn_browse = tk.Button(
            row,
            text="Pilih Folder...",
            command=self.pick_folder,
            font=("Segoe UI", 9, "bold"),
            bg="#374151",
            fg="#FFFFFF",
            activebackground="#4B5563",
            activeforeground="#FFFFFF",
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
        )
        self.btn_browse.pack(side="right")

        # Action Buttons
        act_frame = tk.Frame(self.root, bg="#111827")
        act_frame.pack(fill="x", pady=6, **pad)

        self.btn_start = tk.Button(
            act_frame,
            text="▶ Mulai Kompres Gambar",
            command=self.start_compress,
            font=("Segoe UI", 10, "bold"),
            bg="#10B981",
            fg="#FFFFFF",
            activebackground="#059669",
            activeforeground="#FFFFFF",
            relief="flat",
            padx=16,
            pady=8,
            cursor="hand2",
        )
        self.btn_start.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.btn_stop = tk.Button(
            act_frame,
            text="⏹ Berhenti",
            command=self.request_stop,
            font=("Segoe UI", 10, "bold"),
            bg="#EF4444",
            fg="#FFFFFF",
            activebackground="#DC2626",
            activeforeground="#FFFFFF",
            relief="flat",
            padx=14,
            pady=8,
            state="disabled",
            cursor="hand2",
        )
        self.btn_stop.pack(side="right")

        # Progress Bar & Status
        prog_frame = tk.Frame(self.root, bg="#111827")
        prog_frame.pack(fill="x", pady=(6, 4), **pad)

        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Green.Horizontal.TProgressbar",
            troughcolor="#1F2937",
            background="#3B82F6",
            thickness=14,
        )
        self.progress = ttk.Progressbar(
            prog_frame,
            style="Green.Horizontal.TProgressbar",
            mode="determinate",
        )
        self.progress.pack(fill="x", pady=(0, 6))

        tk.Label(
            prog_frame,
            textvariable=self.status_var,
            font=("Segoe UI", 9, "bold"),
            fg="#93C5FD",
            bg="#111827",
            anchor="w",
        ).pack(fill="x")

        # Log Output
        log_frame = tk.Frame(self.root, bg="#111827")
        log_frame.pack(fill="both", expand=True, pady=(4, 14), **pad)

        self.log_text = tk.Text(
            log_frame,
            bg="#0B1120",
            fg="#E5E7EB",
            font=("Consolas", 9),
            relief="flat",
            bd=8,
            state="disabled",
            wrap="word",
        )
        scroll = tk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.log_text.pack(side="left", fill="both", expand=True)

    def pick_folder(self):
        if self.is_running:
            return
        chosen = filedialog.askdirectory(initialdir=self.target_dir.get() or get_app_dir())
        if chosen:
            self.target_dir.set(os.path.normpath(chosen))

    def append_log(self, msg):
        def _do():
            self.log_text.configure(state="normal")
            self.log_text.insert("end", msg + "\n")
            self.log_text.see("end")
            self.log_text.configure(state="disabled")
        self.root.after(0, _do)

    def set_status(self, msg):
        self.root.after(0, lambda: self.status_var.set(msg))

    def set_progress(self, val, maximum):
        def _do():
            self.progress["maximum"] = max(1, maximum)
            self.progress["value"] = val
        self.root.after(0, _do)

    def request_stop(self):
        self.stop_flag = True
        self.set_status("Menghentikan proses setelah file saat ini selesai...")

    def start_compress(self):
        folder = self.target_dir.get().strip()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Folder Tidak Valid", f"Folder tidak ditemukan:\n{folder}")
            return

        self.is_running = True
        self.stop_flag = False
        self.btn_start.configure(state="disabled")
        self.btn_browse.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

        threading.Thread(target=self._worker, args=(folder,), daemon=True).start()

    def _load_cache(self, cache_path):
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
            except Exception:
                pass
        return {}

    def _save_cache(self, cache_path, cache):
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache, f, indent=2)
        except Exception:
            pass

    def _worker(self, root_dir):
        cache_path = os.path.join(root_dir, LOG_FILENAME)
        cache = self._load_cache(cache_path)

        self.set_status("Menghitung daftar gambar...")
        targets = []
        for root, _, files in os.walk(root_dir):
            for fn in files:
                if fn.lower().endswith((".jpg", ".jpeg", ".png")):
                    targets.append(os.path.join(root, fn))

        total_files = len(targets)
        if total_files == 0:
            self.append_log("Tidak ada file gambar (.jpg/.jpeg/.png) di folder ini.")
            self.set_status("Selesai (0 gambar ditemukan).")
            self._finish_ui()
            return

        self.append_log(f"Folder : {root_dir}")
        self.append_log(f"Total gambar ditemukan : {total_files} file\n")

        total_before = 0
        total_after = 0
        compressed_count = 0
        skipped_cached = 0

        for idx, path in enumerate(targets, start=1):
            if self.stop_flag:
                self.append_log("\n⚠️ Proses dihentikan oleh pengguna.")
                break

            rel_key = os.path.relpath(path, root_dir).replace("\\", "/")
            low = os.path.basename(path).lower()
            before = os.path.getsize(path)
            mtime = int(os.path.getmtime(path))

            self.set_progress(idx, total_files)
            self.set_status(f"Memproses {idx}/{total_files}: {rel_key}")

            cached = cache.get(rel_key)
            if cached and cached.get("size") == before and cached.get("mtime") == mtime:
                skipped_cached += 1
                total_before += before
                total_after += before
                continue

            total_before += before
            max_px = MAX_COVER_PX if "cover" in low else MAX_PREVIEW_PX

            try:
                with Image.open(path) as im:
                    im = ImageOps.exif_transpose(im)
                    w, h = im.size
                    if max(w, h) > max_px:
                        im.thumbnail((max_px, max_px), Image.Resampling.LANCZOS)

                    tmp_path = path + ".tmp_opt"
                    if low.endswith(".png"):
                        if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
                            im.convert("RGBA").save(tmp_path, format="PNG", optimize=True)
                        else:
                            im.convert("RGB").quantize(colors=256, method=Image.Quantize.FASTOCTREE).save(
                                tmp_path, format="PNG", optimize=True
                            )
                    else:
                        if im.mode != "RGB":
                            im = im.convert("RGB")
                        im.save(
                            tmp_path,
                            format="JPEG",
                            quality=JPEG_QUALITY,
                            optimize=True,
                            progressive=True,
                        )

                after_tmp = os.path.getsize(tmp_path)
                if after_tmp < before:
                    os.replace(tmp_path, path)
                    final_size = after_tmp
                    compressed_count += 1
                    hemat = (1 - after_tmp / before) * 100
                    self.append_log(f"✓ {rel_key} : {before // 1024} KB -> {after_tmp // 1024} KB (-{hemat:.0f}%)")
                else:
                    os.remove(tmp_path)
                    final_size = before

                total_after += final_size
                cache[rel_key] = {
                    "size": final_size,
                    "mtime": int(os.path.getmtime(path)),
                }
            except Exception as e:
                if os.path.exists(path + ".tmp_opt"):
                    os.remove(path + ".tmp_opt")
                total_after += before
                self.append_log(f"✗ Lewati {rel_key} ({e})")

        self._save_cache(cache_path, cache)

        saved = total_before - total_after
        pct = (saved / total_before * 100) if total_before else 0
        self.append_log("\n" + "=" * 54)
        self.append_log(f"Total gambar dicek          : {total_files}")
        self.append_log(f"Sudah pernah dikompres (skip): {skipped_cached} file")
        self.append_log(f"Baru dikompres sekarang     : {compressed_count} file")
        self.append_log(f"Total hemat ruang           : {format_mb(saved)} ({pct:.1f}%)")
        self.set_status(f"Selesai! {compressed_count} dikompres, {skipped_cached} dilewati (hemat {format_mb(saved)}).")
        self._finish_ui()

    def _finish_ui(self):
        def _do():
            self.is_running = False
            self.btn_start.configure(state="normal")
            self.btn_browse.configure(state="normal")
            self.btn_stop.configure(state="disabled")
        self.root.after(0, _do)


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageCompressorApp(root)
    root.mainloop()