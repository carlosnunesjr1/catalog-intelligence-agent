#!/usr/bin/env python3
"""
rembg_worker.py — remove fundo e devolve PNG com fundo branco.
Lê imagem binária do stdin, escreve PNG no stdout.

Uso (chamado pelo módulo Node): python rembg_worker.py < imagem.jpg > imagem.png
Sai com código 0 = sucesso; !=0 = erro (stderr tem detalhe).
"""

import sys

def main() -> None:
    data = sys.stdin.buffer.read()
    if not data:
        sys.stderr.write("stdin vazio\n")
        sys.exit(2)

    try:
        from rembg import remove
        from PIL import Image, ImageOps
        import io

        # Remove fundo (u2net). post_process_mask limpa bordas.
        removed = remove(data, post_process_mask=True)

        # Compõe sobre branco (produto com fundo branco = compliance storefront)
        img = Image.open(io.BytesIO(removed)).convert("RGBA")
        white = Image.new("RGBA", img.size, (255, 255, 255, 255))
        composited = Image.alpha_composite(white, img)

        # Padding nítido (borda branca mínima) para cair bem na vitrine
        canvas = ImageOps.expand(composited, border=8, fill=(255, 255, 255, 255))

        out = io.BytesIO()
        canvas.convert("RGB").save(out, format="PNG")
        sys.stdout.buffer.write(out.getvalue())
        sys.exit(0)
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(f"rembg worker erro: {exc}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()