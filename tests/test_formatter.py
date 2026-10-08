"""Formatação do post: preços, desconto, escape HTML e divulgação de afiliado."""
from html import escape

from ofertas.formatter import montar_caption, preco_br


def test_preco_br():
    assert preco_br(1234.5) == "R$ 1.234,50"
    assert preco_br(9.99) == "R$ 9,99"


def test_caption_com_de_por(cfg, nova_oferta):
    o = nova_oferta(titulo='Cafeteira "Expresso"', preco=100.0, preco_original=200.0, desconto_pct=50)
    cap = montar_caption(o)
    assert "❌ De: <s>R$ 200,00</s>" in cap
    assert "✅ Por: <b>R$ 100,00</b>" in cap
    assert "🔻 <b>-50%</b>" in cap
    assert escape(o.titulo) in cap  # título com aspas escapadas para HTML


def test_caption_com_plataforma(cfg, nova_oferta):
    cap = montar_caption(nova_oferta(preco=10.0))
    assert "💛 Mercado Livre" in cap


def test_divulgacao_afiliado(cfg, nova_oferta):
    cap = montar_caption(nova_oferta(preco=10.0))
    assert "Link de afiliado" in cap


def test_divulgacao_desligada(cfg, nova_oferta):
    cfg.divulgar_afiliado = False
    cap = montar_caption(nova_oferta(preco=10.0))
    assert "Link de afiliado" not in cap