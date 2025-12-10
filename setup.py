# setup.py
import importlib
import subprocess
import sys

# YALNIZCA pip ile sorunsuz kurulabilecek paketler
packages = [
    "opencv-contrib-python",
    "numpy",
    "pandas",
    "openpyxl",
    "PyQt5",
]

def install_missing_packages():
    for pkg in packages:
        try:
            importlib.import_module(pkg.split("==")[0])
            print(f"[OK] {pkg} zaten yüklü.")
        except ImportError:
            print(f"[YÜKLENİYOR] {pkg} kuruluyor...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
            print(f"[BAŞARILI] {pkg} kuruldu.\n")

if __name__ == "__main__":
    install_missing_packages()
