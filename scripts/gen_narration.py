#!/usr/bin/env python3
"""Gera narração pt-BR completa (~4 min) cobrindo todas as 8 cenas."""
import asyncio, subprocess

ROTEIRO = """Imagine o catálogo da sua loja. Dezenas, centenas, milhares de produtos. Cada um precisa de foto boa, título com SEO, descrição que vende, atributos corretos. Fazer isso na mão leva horas. Muitas horas.

Este é o Catalog Enricher: um agente de inteligência artificial que pega o dado cru, aquele cadastro simples do seu sistema, e transforma em um produto pronto para publicar na sua loja. Tudo conectado pelo protocolo MCP, dentro do Deco Studio.

Vamos ver como ele funciona na prática, com um produto real. Aqui está um terno slim marrom, com calça de regulagem, de uma loja brasileira. O lojista recebe o link do produto e cola aqui no agente.

Primeira funcionalidade: análise de URL. O agente acessa a página da loja e extrai sozinho o título, o preço, a marca, o código do produto e as imagens. Ele entende o que já existe, para não precisar inventar nada.

Segunda funcionalidade: busca de imagem. Para produtos novos, que ainda não têm foto, o agente busca a imagem em alta resolução usando o título ou o código de barras do produto.

Terceira funcionalidade: análise de imagem. O agente não apenas encontra a foto: ele olha para ela. Ele entende a cor do tecido, a proporção, o fundo, a qualidade. Assim a descrição descreve exatamente o que o cliente vai receber.

Quarta funcionalidade: enriquecimento do produto. Aqui a inteligência artificial cria o conteúdo de venda: título otimizado para busca, bullets de benefícios, descrição em HTML pensada para celular, meta tags e palavras-chave. Tudo em português.

Quinta funcionalidade: validação. E aqui vem uma parte muito importante. Se o lojista não tem a informação completa, o agente não inventa. Ele devolve uma pontuação baixa, e aponta exatamente o que está faltando: descrição, imagem, bullets, código de barras. Ele pede a informação ao lojista, como um bom assistente faria. Isso é essencial: a loja nunca publica um produto com dados falsos, que depois geram devolução e reclamação.

Depois que o produto é enriquecido, a mesma validação mostra o resultado: pontuação alta, SEO na página, dados estruturados, imagem, marca e código de barras completos. Tudo pronto para publicar.

Sexta funcionalidade: publicação. Com tudo pronto, o agente gera o pacote de dados para publicar direto na sua loja, sem copiar e colar. O ciclo está fechado: do cadastro cru ao produto no ar.

E o agente faz isso para muitos produtos ao mesmo tempo, em lote. O lojista sobe a planilha do fornecedor, e o Catalog Enricher processa cada linha: analisa, busca imagem, enriquece, valida e prepara para publicação. Com o protocolo MCP, ele se conecta ao Deco Studio, ao Shopify, à sua loja, sem precisar de integração manual.

Com o Catalog Enricher, uma equipe que gastava duzentas horas por mês cadastrando produtos passa a gastar minutos. É mais receita, menos custo, e a sua loja sempre com o catálogo completo e bonito.

Este é o Catalog Enricher, pelo protocolo MCP, integrado ao Deco Studio. Teste na sua loja."""

async def main():
    chunks = []
    current = ""
    for para in ROTEIRO.split("\n\n"):
        for sent in para.replace("\n", " ").split(". "):
            piece = sent.strip() + ("." if sent.strip() else "")
            if len(current) + len(piece) > 380:
                if current: chunks.append(current)
                current = piece
            else:
                current = (current + " " + piece).strip()
        if current: chunks.append(current); current = ""
    if current: chunks.append(current)

    print(f"chunks: {len(chunks)}")
    files = []
    for i, chunk in enumerate(chunks):
        out = f"/tmp/narr2_chunk_{i:02d}.mp3"
        cmd = ["edge-tts", "--voice", "pt-BR-AntonioNeural", "--text", chunk, "--write-media", out]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            print(f"chunk {i} FAIL: {r.stderr[-200:]}")
            continue
        files.append(out)
        print(f"chunk {i}: {len(chunk)} chars ok")

    if files:
        listf = "/tmp/narr2_list.txt"
        with open(listf, "w") as f:
            for fp in files:
                f.write(f"file '{fp}'\n")
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listf,
                        "-c", "copy", "/tmp/narracao_completa.mp3"], capture_output=True)
        print("concat ok")

asyncio.run(main())
