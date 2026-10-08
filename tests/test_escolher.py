"""Seleção das melhores ofertas: ordenação, alternância de plataformas, dedupe de variações."""
from ofertas import pipeline


class TestOrdenacao:
    def test_padrao_ordena_por_desconto(self, cfg, nova_oferta):
        a = nova_oferta(id_produto="a", titulo="Produto A", desconto_pct=30, preco=700.0, preco_original=1000.0)
        b = nova_oferta(id_produto="b", titulo="Produto B", desconto_pct=40, preco=15.0, preco_original=25.0, plataforma="shopee")
        assert [o.id_produto for o in pipeline.escolher([a, b], 2)] == ["b", "a"]

    def test_poupanca_ordena_por_economia(self, cfg, nova_oferta):
        cfg.ordenar_por = "poupanca"
        a = nova_oferta(id_produto="a", titulo="Produto A", desconto_pct=30, preco=700.0, preco_original=1000.0)  # poupança 300
        b = nova_oferta(id_produto="b", titulo="Produto B", desconto_pct=40, preco=15.0, preco_original=25.0, plataforma="shopee")  # poupança 10
        assert [o.id_produto for o in pipeline.escolher([a, b], 2)] == ["a", "b"]


class TestAlternanciaPlataformas:
    def test_alterna_plataformas(self, cfg, nova_oferta):
        ml = [nova_oferta(id_produto=str(i), titulo=f"Produto {i}", desconto_pct=50) for i in range(3)]
        sh = [nova_oferta(id_produto=str(i), titulo=f"Item {i}", desconto_pct=40, plataforma="shopee") for i in range(3)]
        escolhidas = pipeline.escolher(ml + sh, 2)
        assert [o.plataforma for o in escolhidas] == ["mercadolivre", "shopee"]


class TestPulaVariacoes:
    def test_pula_variacoes_do_mesmo_produto(self, cfg, nova_oferta):
        a = nova_oferta(id_produto="1", titulo="Fone Bluetooth X Sem Fio", desconto_pct=50)
        b = nova_oferta(id_produto="2", titulo="Fone Bluetooth X Sem Fio Branco", desconto_pct=45)
        c = nova_oferta(id_produto="3", titulo="Cadeira Gamer", desconto_pct=30)
        escolhidas = pipeline.escolher([a, b, c], 3)
        assert [o.id_produto for o in escolhidas] == ["1", "3"]