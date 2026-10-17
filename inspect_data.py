
from pathlib import Path

# CSV dosyasının yolunu belirliyoruz
file_path = Path(__file__).resolve().parent / "data" / "budapest.csv"

# Dosya mevcut mu kontrol ediyoruz
if not file_path.exists():
    print("ERROR: Budapest CSV file not found!")

else:
    print("CSV file found!")
    print("\nFirst 10 lines:\n")

    # CSV dosyasını açıyoruz
    with open(file_path, "r", encoding="utf-8-sig") as file:

        for i, line in enumerate(file):
            if i >= 10:
                break

            print(line.strip())
