#!/usr/bin/env python3
"""Compila `Landing Kauana Liesenfeld.dc.html` (Claude Design) em `index.html` estático.

O arquivo .dc.html depende do runtime do Claude Design (support.js + image-slot.js).
Este script resolve essas dependências para que a página funcione em hospedagem
estática comum (Vercel, Netlify, GitHub Pages):

  <helmet>          -> conteúdo de <head>
  <sc-if>           -> expandido com o valor default da prop
  <image-slot>      -> <img> apontando para o arquivo extraído de .image-slots.state.json
  style-hover="..." -> regra CSS :hover de verdade
  <script text/x-dc> -> JS puro (reveal on scroll + tilt nos cards)
"""

import base64
import json
import os
import re

SRC = "Landing Kauana Liesenfeld.dc.html"
OUT = "index.html"
STATE = ".image-slots.state.json"

# Props do bloco data-dc-script. O número já está embutido nos links wa.me,
# então applyPhone() do runtime vira desnecessário na versão estática.
PROPS = {"showGoogleBadge": True, "tiltEnabled": True}

# Cada slot vira um <img>. object-position deriva do enquadramento (x/y) salvo
# no sidecar: só svc-terapeutica foi reposicionado (y = -9.09% => sobe a imagem).
SLOT_IMG = {
    "svc-terapeutica": ("assets/svc-terapeutica.webp", "Massagem terapêutica", "50% 61%"),
    "svc-drenagem": ("assets/svc-drenagem.webp", "Drenagem linfática", "50% 50%"),
    "svc-depilacao": ("assets/svc-depilacao.webp", "Depilação com cera", "50% 50%"),
    "svc-limpeza": ("assets/svc-limpeza.webp", "Limpeza de pele", "50% 50%"),
}

RUNTIME_JS = """
(function () {
  var reveal = function () {
    var nodes = Array.prototype.slice.call(document.querySelectorAll('[data-reveal]'));
    var show = function (el) { el.style.opacity = '1'; el.style.transform = 'none'; };
    if (!('IntersectionObserver' in window)) { nodes.forEach(show); return; }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { if (e.isIntersecting) { show(e.target); io.unobserve(e.target); } });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    nodes.forEach(function (n) { io.observe(n); });
    setTimeout(function () {
      nodes.forEach(function (n) {
        if (n.style.opacity !== '1' && n.getBoundingClientRect().top < window.innerHeight) show(n);
      });
    }, 1600);
  };

  var tilt = function () {
    if (window.matchMedia('(hover: none)').matches) return;
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    document.querySelectorAll('[data-tilt]').forEach(function (card) {
      card.addEventListener('mousemove', function (ev) {
        var r = card.getBoundingClientRect();
        var px = (ev.clientX - r.left) / r.width - 0.5;
        var py = (ev.clientY - r.top) / r.height - 0.5;
        card.style.transform = 'perspective(900px) rotateY(' + (px * 5).toFixed(2) +
          'deg) rotateX(' + (-py * 5).toFixed(2) + 'deg) translateY(-5px)';
        card.style.boxShadow = '0 18px 40px rgba(70,55,30,.14)';
      });
      card.addEventListener('mouseleave', function () {
        card.style.transform = 'none';
        card.style.boxShadow = 'none';
      });
    });
  };

  var init = function () { reveal(); if (TILT_ENABLED) tilt(); };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
"""


def extract_slot_images():
    """Grava os data: URIs do sidecar como arquivos reais em assets/."""
    if not os.path.exists(STATE):
        return
    state = json.load(open(STATE, encoding="utf-8"))
    for slot_id, view in state.items():
        m = re.match(r"data:image/(\w+);base64,(.*)", view.get("u", ""), re.S)
        if not m:
            continue
        path = f"assets/{slot_id}.{m.group(1)}"
        with open(path, "wb") as fh:
            fh.write(base64.b64decode(m.group(2)))


def strip_tag_keep_children(html, tag):
    """Remove <tag ...> e </tag> preservando o conteúdo interno."""
    html = re.sub(rf"<{tag}\b[^>]*>", "", html)
    return html.replace(f"</{tag}>", "")


def replace_image_slots(html):
    def sub(match):
        slot_id = match.group(1)
        src, alt, pos = SLOT_IMG[slot_id]
        return (
            f'<img src="{src}" alt="{alt}" loading="lazy" '
            f'style="width:100%;height:100%;object-fit:cover;object-position:{pos}">'
        )

    return re.sub(r'<image-slot\s+id="([^"]+)"[^>]*>\s*</image-slot>', sub, html)


def hoist_hover_styles(html):
    """style-hover="a:b" vira uma classe com regra :hover real.

    Precisa de !important: o style inline do elemento sempre vence uma regra
    de classe, independente de especificidade.
    """
    rules, classes = [], {}

    def sub(match):
        decls = match.group(1).strip().rstrip(";")
        if decls not in classes:
            name = f"hv{len(classes) + 1}"
            classes[decls] = name
            body = ";".join(
                f"{d.strip()} !important" for d in decls.split(";") if d.strip()
            )
            rules.append(f".{name}:hover{{{body}}}")
        return f'data-hover-class="{classes[decls]}"'

    html = re.sub(r'\s*style-hover="([^"]*)"', sub, html)

    # Move o marcador para um class= de verdade (nenhuma tag do design usa class).
    def to_class(match):
        tag = match.group(0)
        cls = re.search(r'data-hover-class="([^"]+)"', tag).group(1)
        tag = re.sub(r'\s*data-hover-class="[^"]+"', "", tag)
        return tag[:-1].rstrip() + f' class="{cls}">'

    html = re.sub(r"<[a-zA-Z][^>]*data-hover-class=\"[^\"]+\"[^>]*>", to_class, html)
    return html, rules


def main():
    extract_slot_images()
    src = open(SRC, encoding="utf-8").read()

    head = re.search(r"<helmet>(.*?)</helmet>", src, re.S).group(1)
    body = re.search(r"<x-dc>(.*?)</x-dc>", src, re.S).group(1)

    # O runtime do Claude Design não existe na página estática.
    head = re.sub(r'\s*<script src="\./(support|image-slot)\.js"></script>', "", head)

    body = re.sub(r"<helmet>.*?</helmet>", "", body, flags=re.S)
    body = replace_image_slots(body)

    # <sc-if value="{{ showGoogleBadge }}"> — mantém o bloco se a prop for true.
    if PROPS["showGoogleBadge"]:
        body = strip_tag_keep_children(body, "sc-if")
    else:
        body = re.sub(r"<sc-if\b.*?</sc-if>", "", body, flags=re.S)

    body, hover_rules = hoist_hover_styles(body)
    head, head_hover = hoist_hover_styles(head)
    hover_rules += head_hover

    hover_css = (
        "<style>\n  " + "\n  ".join(hover_rules) + "\n</style>" if hover_rules else ""
    )
    js = RUNTIME_JS.replace("TILT_ENABLED", "true" if PROPS["tiltEnabled"] else "false")

    out = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
{head.strip()}
{hover_css}
</head>
<body>
{body.strip()}
<script>{js}</script>
</body>
</html>
"""
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(out)
    print(f"{OUT}: {len(out)} bytes, {len(hover_rules)} regras :hover")


if __name__ == "__main__":
    main()
