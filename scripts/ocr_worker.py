#!/usr/bin/env python3
"""
ocr_worker.py — OCR de print/imagem de página de produto (tesseract, pt-por).
Lê bytes de imagem no stdin, escreve JSON no stdout.

Uso: python ocr_worker.py < imagem.png > saida.json
Código 0 = sucesso; !=0 = erro.
"""

import json
import sys
from io import BytesIO

def main() -> None:
    data = sys.stdin.buffer.read()
    if not data:
        sys.stderr.write("stdin vazio\n")
        sys.exit(2)
    try:
        import pytesseract
        from PIL import Image

        img = Image.open(BytesIO(data)).convert("RGB")
        try:
            text = pytesseract.image_to_string(img, lang="por")
        except Exception:
            # fallback: inglês se idioma por indisponível
            text = pytesseract.image_to_string(img)

        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

        result = {
            "ok": True,
            "full_text": text[:4000],
            "lines": lines[:80],
            "word_count": len(text.split()),
        }
        sys.stdout.write(json.dumps(result, ensure_ascii=False))
        sys.exit(0)
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(f"ocr erro: {exc}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()