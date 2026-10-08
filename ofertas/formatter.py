from html import escape

from .config import config
from .models import Oferta

_AVISO_AFILIADO = ("<i>📌 Link de afiliado — pode gerar comissão pela indicação, "
                   "sem custo extra pra você.</i>")

_PLATAFORMA = {
    "mercadolivre": "💛 Mercado Livre",
    "shopee": "🧡 Shopee",
    "amazon": "📦 Amazon",
}


def preco_br(valor: float) -> str:
    return "R$ " + f"{valor:,.2f}".replace(",", " ").replace(".", ",").replace(" ", ".")


def montar_caption(o: Oferta) -> str:
    linhas = [f"🔥 <b>{escape(o.titulo[:180])}</b>", ""]

    if o.preco and o.preco_original and o.preco_original > o.preco:
        linhas.append(f"❌ De: <s>{preco_br(o.preco_original)}</s>")
        selo = f"  🔻 <b>-{o.desconto}%</b>" if o.desconto else ""
        linhas.append(f"✅ Por: <b>{preco_br(o.preco)}</b>{selo}")
    elif o.preco:
        selo = f"  🔻 <b>-{o.desconto}%</b>" if o.desconto else ""
        linhas.append(f"✅ <b>{preco_br(o.preco)}</b>{selo}")

    if o.extra:
        linhas.append(escape(o.extra))

    linhas += ["", _PLATAFORMA.get(o.plataforma, o.plataforma)]
    if config.divulgar_afiliado:
        linhas += ["", _AVISO_AFILIADO]
    return "\n".join(linhas)
