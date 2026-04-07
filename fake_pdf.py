"""
Namuna PDF yaratadi: fake_zayavka.pdf
Ishga tushirish: python fake_pdf.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from services.pdf import build_fake_pdf


def main() -> None:
    path = os.path.join(ROOT, "fake_zayavka.pdf")
    build_fake_pdf(out_path=path)
    print(f"Tayyor: {path}")


if __name__ == "__main__":
    main()
