# Landing Page — Kauana Liesenfeld

Landing page da **Kauana Liesenfeld**, massoterapeuta e esteticista em Gramado/RS.

Projeto importado do Claude Design
([`f2fd1ca8`](https://claude.ai/design/p/f2fd1ca8-4c99-4126-b9d0-00140c702d35)) e compilado
para HTML estático pronto para deploy.

## Estrutura

| Arquivo | O que é |
| --- | --- |
| `index.html` | **A página que vai pro ar.** HTML estático, sem build step, sem dependências externas além do Google Fonts. |
| `Landing Kauana Liesenfeld.dc.html` | Fonte original do Claude Design. É a partir dele que o `index.html` é gerado. |
| `build.py` | Compila o `.dc.html` em `index.html`. |
| `support.js`, `image-slot.js` | Runtime do Claude Design. Usados só pelo `.dc.html`, não pelo `index.html`. |
| `.image-slots.state.json` | Enquadramento e conteúdo dos `<image-slot>` do editor. |
| `assets/` | Fotos, prints das avaliações do Google e imagens dos slots. |
| `favicon.svg` | Monograma "K" dourado sobre o verde da marca. Fonte dos ícones. |
| `favicon-32.png`, `apple-touch-icon.png` | Fallbacks rasterizados a partir do `favicon.svg`. |

## Rebuild

Depois de editar o `.dc.html` (no Claude Design ou à mão):

```bash
python3 build.py
```

O script resolve o que o runtime do Claude Design faria em tempo de execução:

- `<helmet>` → conteúdo do `<head>`
- `<sc-if>` → expandido com o valor default da prop (`showGoogleBadge: true`)
- `<image-slot>` → `<img>` apontando para o arquivo extraído de `.image-slots.state.json`
- `style-hover="..."` → regra CSS `:hover` de verdade (com `!important`, já que
  o `style` inline sempre vence uma classe)
- `<script type="text/x-dc">` → JS puro: revelação no scroll (IntersectionObserver)
  e tilt nos cards de serviço

O `applyPhone()` do runtime original não é portado: o número já está embutido em
todos os links `wa.me`.

## Deploy

Site estático — basta servir a raiz do repositório. Na Vercel, importar o repo
sem framework preset (Output Directory: `.`) já funciona.

## Manutenção

**Trocar o WhatsApp:** o número aparece nos links `wa.me/5554999689471` e no texto
do rodapé. Buscar e substituir em `Landing Kauana Liesenfeld.dc.html`, depois rodar
o `build.py`.

**Trocar uma foto de serviço:** substituir o arquivo em `assets/` e ajustar o `src`
correspondente. Para os quatro cards que usam `<image-slot>` (terapêutica, drenagem,
depilação, limpeza de pele), o mapeamento imagem → enquadramento está em `SLOT_IMG`,
no `build.py`.

**Regerar os ícones:** editar o `favicon.svg` e rasterizar os PNGs a partir dele
(32×32 e 180×180). O `apple-touch-icon.png` vai sem cantos arredondados — o iOS
aplica a própria máscara.
