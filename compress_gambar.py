import os
from PIL import Image, ImageOps

# ==============================================================================
# PAWANG GAME STORE - KOMPRES GAMBAR IN-PLACE (TIDAK PINDAH FOLDER / TIDAK UBAH NAMA)
# Cara pakai:
# 1. Taruh file ini di dalam folder repo lokal (sejajar dengan folder "Marketplace").
# 2. Pastikan Pillow terpasang: pip install pillow
# 3. Jalankan: python compress_gambar.py
# ==============================================================================

TARGET_DIR = "Marketplace"   # Ganti jika ingin scan folder lain (atau "." untuk folder saat ini)
MAX_COVER_PX = 500           # Ukuran maksimal sisi terpanjang untuk file cover
MAX_PREVIEW_PX = 1280        # Ukuran maksimal sisi terpanjang untuk file preview
JPEG_QUALITY = 82            # Kualitas JPG (80-85 tetap sangat tajam tapi ukuran jauh lebih kecil)


def format_mb(num_bytes):
    return f"{num_bytes / (1024 * 1024):.2f} MB"


def compress_in_place(root_dir):
    if not os.path.exists(root_dir):
        print(f"Error: Folder '{root_dir}' tidak ditemukan!")
        return

    total_files = 0
    total_before = 0
    total_after = 0
    compressed_count = 0

    for root, _, files in os.walk(root_dir):
        for fn in files:
            low = fn.lower()
            if not low.endswith((".jpg", ".jpeg", ".png")):
                continue

            path = os.path.join(root, fn)
            total_files += 1
            before = os.path.getsize(path)
            total_before += before

            max_px = MAX_COVER_PX if "cover" in low else MAX_PREVIEW_PX

            try:
                with Image.open(path) as im:
                    im = ImageOps.exif_transpose(im)
                    w, h = im.size
                    need_resize = max(w, h) > max_px
                    if need_resize:
                        im.thumbnail((max_px, max_px), Image.Resampling.LANCZOS)

                    tmp_path = path + ".tmp_opt"
                    if low.endswith(".png"):
                        # Simpan PNG teroptimasi; jika tanpa transparansi, gunakan P-mode adaptif agar jauh lebih ringan
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
                # Hanya timpa jika hasilnya lebih kecil daripada file asli
                if after_tmp < before:
                    os.replace(tmp_path, path)
                    total_after += after_tmp
                    compressed_count += 1
                    hemat = (1 - after_tmp / before) * 100
                    print(f"✓ {path} : {before // 1024} KB -> {after_tmp // 1024} KB (-{hemat:.0f}%)")
                else:
                    os.remove(tmp_path)
                    total_after += before
            except Exception as e:
                if os.path.exists(path + ".tmp_opt"):
                    os.remove(path + ".tmp_opt")
                total_after += before
                print(f"✗ Lewati {path} ({e})")

    saved = total_before - total_after
    pct = (saved / total_before * 100) if total_before else 0
    print("\n" + "=" * 50)
    print(f"Selesai! Total gambar dicek : {total_files}")
    print(f"Berhasil dikompres          : {compressed_count} file")
    print(f"Ukuran sebelum              : {format_mb(total_before)}")
    print(f"Ukuran sesudah              : {format_mb(total_after)}")
    print(f"Total hemat ruang           : {format_mb(saved)} ({pct:.1f}%)")
    print("Sekarang tinggal buka GitHub Desktop dan Push origin.")


if __name__ == "__main__":
    compress_in_place(TARGET_DIR)