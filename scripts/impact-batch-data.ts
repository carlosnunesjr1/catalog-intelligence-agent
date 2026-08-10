// Lote de teste REAL — simula export de ERP de fornecedor (dados sujos):
// títulos CAIXA ALTA, marca genérica, sem descrição, sem imagem, atributos mistos.
// Foco: MODA (o segmento que o Carlos descreveu) + itens genéricos.
export const IMPACT_BATCH = [
  {
    title: 'BLUSA FEMININA MOLETOM CANGURU MANGA LONGA C/ CAPUZ',
    brand: 'SEM MARCA',
    attributes: { cor: 'PRETA', tamanho: 'P', categoria: 'moda feminina' },
  },
  {
    title: 'CAMISA SOCIAL MASCULINA MANGA LONGA SLIM AZUL',
    brand: 'Marca X',
    attributes: { cor: 'AZUL', tamanho: 'M', composicao: '100% algodão', categoria: 'roupa masculina' },
  },
  {
    title: 'VESTIDO MIDI FLORAL COM CANO MÉDIO',
    brand: 'SEM MARCA',
    attributes: { cor: 'ESTAMPADO', tamanho: 'G', categoria: 'moda' },
  },
  {
    title: 'CALÇA JEANS FEMININA SKINNY CINTURA ALTA',
    brand: 'Denim Co',
    attributes: { cor: 'AZUL', tamanho: '38', categoria: 'calças' },
  },
  {
    title: 'JARDINEIRA ALFAIATARIA PRETA REGULÁVEL',
    brand: 'Atelier B',
    attributes: { cor: 'PRETA', tamanho: 'M', categoria: 'moda' },
  },
  {
    title: 'TERNO SLIM COMFORT MARROM APRICOT 02 PECAS',
    brand: 'SEM MARCA',
    attributes: { cor: 'MARROM', tamanho: '48', categoria: 'ternos' },
  },
  {
    title: 'FURADEIRA DE IMPACTO 750W 110V PROFISSIONAL',
    brand: 'FerraKit',
    attributes: { potencia: '750W', voltagem: '110V', categoria: 'ferramentas' },
  },
  {
    title: 'CHUVEIRO ELÉTRICO 5500W 127V DUCHO',
    brand: 'Lorenzetti',
    attributes: { potencia: '5500W', tipo: 'ducho', categoria: 'casa' },
  },
  {
    title: 'PANELA DE PRESSÃO 4,5L AÇO INOX',
    brand: 'CasaPlus',
    attributes: { capacidade: '4,5L', material: 'aço inox', categoria: 'utensílios' },
  },
  {
    title: 'TÊNIS CORRIDA MASCULINO PRETO COM AMORTECIMENTO',
    brand: 'SEM MARCA',
    attributes: { cor: 'PRETO', tamanho: '42', categoria: 'calçados' },
  },
] as const;