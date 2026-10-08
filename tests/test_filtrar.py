"""Filtros do pipeline: desconto, economia em R$, dedupe e palavras bloqueadas."""
from ofertas import pipeline


class TestFiltroDesconto:
    def test_abaixo_do_minimo_e_descartada(self, cfg, banco, nova_oferta):
        o = nova_oferta(desconto_pct=10)
        assert pipeline.filtrar([o]) == []

    def test_no_minimo_passa(self, cfg, banco, nova_oferta):
        o = nova_oferta(desconto_pct=25)
        assert pipeline.filtrar([o]) == [o]


class TestFiltroEconomia:
    def test_economia_em_reais_abaixo_e_descartada(self, cfg, banco, nova_oferta):
        cfg.desconto_minimo_reais = 30.0
        o = nova_oferta(desconto_pct=50, preco=10.0, preco_original=15.0)  # economiza R$5
        assert pipeline.filtrar([o]) == []

    def test_economia_em_reais_acima_passa(self, cfg, banco, nova_oferta):
        cfg.desconto_minimo_reais = 30.0
        o = nova_oferta(desconto_pct=30, preco=70.0, preco_original=100.0)  # economiza R$30
        assert o in pipeline.filtrar([o])

    def test_sem_preco_original_nao_e_bloqueada(self, cfg, banco, nova_oferta):
        cfg.desconto_minimo_reais = 30.0
        o = nova_oferta(desconto_pct=40, preco=50.0)
        assert o in pipeline.filtrar([o])


class TestDedupe:
    def test_uid_ja_postada_e_descartada(self, cfg, banco, nova_oferta):
        banco.registrar(nova_oferta(id_produto="9"))
        o = nova_oferta(id_produto="9", desconto_pct=40)
        assert pipeline.filtrar([o]) == []

    def test_titulo_parecido_e_descartado(self, cfg, banco, nova_oferta):
        banco.registrar(nova_oferta(id_produto="1", titulo="Fone Bluetooth X Sem Fio"))
        o = nova_oferta(id_produto="2", titulo="Fone Bluetooth X Sem Fio Branco", desconto_pct=40)
        assert pipeline.filtrar([o]) == []

    def test_titulo_diferente_passa(self, cfg, banco, nova_oferta):
        banco.registrar(nova_oferta(id_produto="1", titulo="Panela de Pressão 4L"))
        o = nova_oferta(id_produto="2", titulo="Fone Bluetooth X", desconto_pct=40)
        assert pipeline.filtrar([o]) == [o]

    def test_dedupe_desligado_deixa_passar(self, cfg, banco, nova_oferta):
        cfg.dedupe_titulos = False
        banco.registrar(nova_oferta(id_produto="1", titulo="Fone Bluetooth X Sem Fio"))
        o = nova_oferta(id_produto="2", titulo="Fone Bluetooth X Sem Fio Branco", desconto_pct=40)
        assert pipeline.filtrar([o]) == [o]


class TestPalavrasBloqueadas:
    def test_palavra_bloqueada_descarta(self, cfg, banco, nova_oferta):
        cfg.palavras_bloqueadas = ["capinha"]
        o = nova_oferta(titulo="Capinha de Celular Premium", desconto_pct=40)
        assert pipeline.filtrar([o]) == []


class TestSemTitulo:
    def test_sem_titulo_descartada(self, cfg, banco, nova_oferta):
        o = nova_oferta(titulo="", desconto_pct=40)
        assert pipeline.filtrar([o]) == []


class TestPrecoLimites:
    def test_preco_maximo(self, cfg, banco, nova_oferta):
        cfg.preco_maximo = 100.0
        o = nova_oferta(preco=150.0, desconto_pct=40)
        assert pipeline.filtrar([o]) == []

    def test_preco_minimo(self, cfg, banco, nova_oferta):
        cfg.preco_minimo = 50.0
        o = nova_oferta(preco=10.0, desconto_pct=40)
        assert pipeline.filtrar([o]) == []