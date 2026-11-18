import os
import json
import re

# ==========================================
# PENGATURAN TOKO (Bisa diedit kapan saja)
# ==========================================
HARGA_SATUAN = 10000
LINK_SHOPEE = "https://shopee.co.id/link-produk-satuan-pawang-game"
NOMOR_WA = "6281234567890"

# Folder tempat kamu menyimpan susunan game
MARKETPLACE_DIR = "Marketplace"
OUTPUT_FILE = "katalog.json"

def generate_id(category, title):
    # Membuat ID unik otomatis tanpa spasi (misal: ps1_harvest_moon_btn)
    raw = f"{category}_{title}".lower()
    return re.sub(r'[^a-z0-9]', '_', raw)

def scan_katalog():
    if not os.path.exists(MARKETPLACE_DIR):
        print(f"Error: Folder '{MARKETPLACE_DIR}' tidak ditemukan!")
        print("Pastikan script ini berada sejajar dengan folder Marketplace.")
        return

    games_data = []

    print("Memulai proses scan folder Marketplace...\n")
    
    # 1. Scan Kategori (PS1, PS2, PC Game)
    for category in os.listdir(MARKETPLACE_DIR):
        category_path = os.path.join(MARKETPLACE_DIR, category)
        
        # Pastikan yang dibaca hanya folder, bukan file nyasar
        if os.path.isdir(category_path):
            
            # 2. Scan Judul Game di dalam Kategori tersebut
            for game_title in os.listdir(category_path):
                game_path = os.path.join(category_path, game_title)
                
                if os.path.isdir(game_path):
                    files = os.listdir(game_path)
                    
                    cover_path = ""
                    previews = []
                    
                    # 3. Pisahkan mana yang cover, mana yang preview
                    for file in files:
                        file_lower = file.lower()
                        # Cek apakah ini file gambar
                        if file_lower.endswith(('.png', '.jpg', '.jpeg')):
                            # Gunakan '/' agar format jalurnya valid untuk link Internet (URL)
                            rel_path = f"{MARKETPLACE_DIR}/{category}/{game_title}/{file}"
                            
                            # Kalau nama filenya mengandung kata "cover"
                            if "cover" in file_lower:
                                cover_path = rel_path
                            else:
                                previews.append(rel_path)
                    
                    # Urutkan nama preview (preview1, preview2, dst)
                    previews.sort()

                    # Tambahkan ke daftar game yang siap di-JSON-kan
                    games_data.append({
                        "id": generate_id(category, game_title),
                        "title": game_title,
                        "category": category,
                        "cover": cover_path,
                        "previews": previews
                    })
                    print(f"✓ Terdeteksi: [{category}] {game_title} ({len(previews)} preview)")

    # 4. Bungkus semua data dengan pengaturan toko
    katalog_akhir = {
        "harga_satuan": HARGA_SATUAN,
        "link_shopee_satuan": LINK_SHOPEE,
        "nomor_wa": NOMOR_WA,
        "games": games_data
    }

    # 5. Cetak (Export) menjadi file katalog.json
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(katalog_akhir, f, indent=4, ensure_ascii=False)
    
    print(f"\nSelesai! {len(games_data)} game telah berhasil dibungkus ke dalam '{OUTPUT_FILE}'.")
    print("Sekarang kamu tinggal buka GitHub Desktop dan tekan tombol 'Push origin'.")

if __name__ == "__main__":
    scan_katalog()