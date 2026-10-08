"""Fixtures compartilhadas: objeto Oferta de teste, config determinística e banco temporário."""
import pytest

from ofertas import db
from ofertas.config import config
from ofertas.models import Oferta


@pytest.fixture
def nova_oferta():
    """Fábrica de Oferta: nova_oferta(**overrides) com defaults mínimos."""
    def fazer(**kw):
        padrao = dict(
            plataforma="mercadolivre",
            id_produto="1",
            titulo="Fone Bluetooth X",
            url_afiliado="https://meli.la/x",
        )
        padrao.update(kw)
        return Oferta(**padrao)
    return fazer


@pytest.fixture
def cfg(monkeypatch):
    """Config determinística para os testes (não depende do config.yaml/.env reais)."""
    valores = {
        "desconto_minimo": 25,
        "desconto_minimo_reais": 0.0,
        "ordenar_por": "desconto",
        "dedupe_titulos": True,
        "dedupe_titulos_dias": 3,
        "preco_minimo": 0.0,
        "preco_maximo": 0.0,
        "palavras_bloqueadas": [],
        "nao_repetir_dias": 7,
        "max_posts_por_ciclo": 3,
        "max_posts_por_dia": 0,
        "divulgar_afiliado": True,
    }
    for chave, valor in valores.items():
        monkeypatch.setattr(config, chave, valor)
    return config


@pytest.fixture
def banco(tmp_path, monkeypatch):
    """Aponta o banco para um SQLite temporário (nunca toca em data/ofertas.db)."""
    monkeypatch.setattr(db, "_DB", tmp_path / "ofertas_teste.db")
    return db