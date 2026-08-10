#!/usr/bin/env python3
"""
imginfo_worker.py — análise determinística de imagem de produto.
Lê bytes no stdin, escreve JSON no stdout.

Analisa: dimensões, proporção, fundo (bordas), nitidez, tamanho de arquivo.

Uso: python imginfo_worker.py < imagem.* > saida.json
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
        from PIL import Image, ImageStat

        img = Image.open(BytesIO(data)).convert("RGB")
        w, h = img.size
        small = img.resize((64, 64), Image.LANCZOS)
        stat = ImageStat.Stat(small)

        # Média e desvio por canal — útil para detectar fundo uniforme
        means = [round(v, 1) for v in stat.mean]
        stds = [round(v, 1) for v in stat.stddev]

        # Bordas (16px) — se quase uniformes, há fundo definido
        border_px = 24
        box = img.crop((0, 0, w, border_px))
        bstat = ImageStat.Stat(box)
        border_std = round(max(bstat.stddev), 1)
        sample = img.resize((64, 64), Image.LANCZOS)
        means_now = [round(v, 1) for v in ImageStat.Stat(sample).mean]

        # Nitidez aproximada: variância do Laplaciano (via filtro)
        from PIL import ImageFilter
        lap = sample.convert("L").filter(ImageFilter.FIND_EDGES)
        lap_stat = ImageStat.Stat(lap)
        sharpness = round(lap_stat.mean[0], 2)

        result = {
            "width": w,
            "height": h,
            "aspect_ratio": round(w / h, 3) if h else None,
            "format": (img.format or "").lower(),
            "size_bytes": len(data),
            "background": "uniform" if border_std < 12 else "noisy",
            "border_stddev": border_std,
            "mean_rgb": means_now,
            "sharpness": sharpness,
        }
        # Heurísticas de prontidão
        issues = []
        if w < 700 or h < 700:
            issues.append("resolução baixa (<700px) — ideal mínimo 1000px p/ zoom")
        if not (0.9 <= result["aspect_ratio"] <= 1.5):
            issues.append("proporção fora do padrão de produto (0.9–1.5)")
        if result["background"] == "noisy":
            issues.append("fundo não-uniforme — rembg p/ fundo branco recomendado")
        if sharpness < 8:
            issues.append("nitidez baixa — possível imagem desfocada")
        if len(data) < 20_000:
            issues.append("arquivo pequeno — possível compressão excessiva")
        result["ready_for_store"] = len(issues) == 0
        result["issues"] = issues

        sys.stdout.write(json.dumps(result, ensure_ascii=False))
        sys.exit(0)
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(f"imginfo erro: {exc}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()