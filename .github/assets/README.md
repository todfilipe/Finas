# Assets do README

Os SVG têm versões `light` e `dark`, usadas por `<picture>` no README. Os fundos são branco puro ou preto puro; o acento de marca é `#96650F`. A tipografia usa Arial, Helvetica e sans-serif, sem pedidos a fontes externas.

| Ficheiros | Origem |
|---|---|
| `abertura-*.svg` | Título e pílulas com versões verificadas no projeto. |
| `passos-*.svg` | Três cartões sobre registo, interpretação e consulta. |
| `arquitetura-*.svg` | Ligações dos serviços no deploy de produção. |
| `divisor-*.svg` | Separadores tipográficos entre momentos da página. |
| `simbolo-*.svg` | O PNG original de `landing/img/logo-simbolo.png`, incorporado numa moldura circular. |
| `dashboard-resumo-*.svg` | O WebP original de `landing/img/dashboard-resumo.webp`, incorporado numa moldura de janela. |
| `dashboard-transacoes-*.svg` | O WebP original de `landing/img/dashboard-transacoes.webp`, incorporado numa moldura de janela. |
| `conversa-*.webp` | Ilustração criada com a ferramenta integrada de geração de imagem, exportada a 384 × 384 px. |

As imagens originais incorporadas nos SVG mantêm os mesmos bytes dos ficheiros em `landing/img/`. O README liga também aos screenshots originais para os abrir em tamanho completo. Se os screenshots mudarem, atualiza as duas molduras correspondentes.

A ilustração é uma peça editorial abstrata. Não representa um ecrã da aplicação. Os únicos screenshots do produto são os existentes na landing.

## Prompts da ilustração

Ferramenta usada: geração de imagem integrada. A variante escura foi gerada como edição da variante clara. A exportação WebP redimensiona e comprime os resultados, sem redesenhar a ilustração.

### Variante clara

```text
Create a refined minimalist editorial illustration for Finas, a personal expenses Telegram bot. A flowing folded strip of blank receipt paper curls into a rounded conversation bubble shape, with one tiny flat ochre gold circular accent (#96650F), conveying writing becoming organised accounts. Flat graphic paper-cut illustration, extremely simple, sharp clean contours, black and pure white only plus the single small gold accent. No shadows, no grey backgrounds, no gradients, no letters, no text, no currency symbols, no logos, no UI or screenshots. Composition centred with generous empty space, compact square image. Pure white (#FFFFFF) canvas, the paper form outlined strongly in black, gold accent small. Intended to sit as a small illustration near a large typographic SVG README banner. This is an abstract illustration, not a product screenshot.
```

### Variante escura

```text
Create the matching dark-theme variant of this exact illustration. Preserve the exact composition, contours, silhouette, folded blank receipt forming a conversation bubble, small gold dot and spacious square framing. Swap black and white: canvas must be perfectly pure black #000000, main shape black inside, every previously black stroke becomes white. Keep the small gold dot #96650F. Flat solid fills, absolutely no texture, gradients or shadows. No text. Same shape and position as reference. This is the dark variant for the same README illustration.
```
