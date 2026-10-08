"""Banco anti-repetição: registro, expiração, chave de título, contagem diária e migração."""
import datetime as dt
import sqlite3

from ofertas import db
from ofertas.utils import chave_similar


def test_registrar_e_ja_postada(banco, nova_oferta):
    o = nova_oferta(id_produto="1", titulo="Fone X")
    assert not banco.ja_postada(o.uid, 7)
    banco.registrar(o)
    assert banco.ja_postada(o.uid, 7)
    assert not banco.ja_postada("mercadolivre:2", 7)


def test_ja_postada_expira(banco, nova_oferta):
    banco.registrar(nova_oferta(id_produto="1"))
    with banco._conn() as c:
        c.execute(
            "UPDATE postadas SET postada_em = ? WHERE uid = ?",
            ((dt.datetime.now() - dt.timedelta(days=10)).isoformat(timespec="seconds"),
             "mercadolivre:1"),
        )
    assert not banco.ja_postada("mercadolivre:1", 7)
    assert banco.ja_postada("mercadolivre:1", 15)


def test_chave_recente(banco, nova_oferta):
    banco.registrar(nova_oferta(id_produto="1", titulo="Fone Bluetooth X Sem Fio"))
    assert banco.chave_recente("fone bluetooth x sem fio", 3)
    assert not banco.chave_recente("panela de pressao digital", 3)
    assert not banco.chave_recente("", 3)


def test_chave_recente_expira(banco, nova_oferta):
    banco.registrar(nova_oferta(id_produto="1", titulo="Fone X"))
    with banco._conn() as c:
        c.execute(
            "UPDATE postadas SET postada_em = ? WHERE uid = ?",
            ((dt.datetime.now() - dt.timedelta(days=5)).isoformat(timespec="seconds"),
             "mercadolivre:1"),
        )
    assert not banco.chave_recente(chave_similar("Fone X"), 3)
    assert banco.chave_recente(chave_similar("Fone X"), 7)


def test_postadas_hoje(banco, nova_oferta):
    banco.registrar(nova_oferta(id_produto="1"))
    banco.registrar(nova_oferta(id_produto="2", plataforma="shopee"))
    with banco._conn() as c:
        c.execute("UPDATE postadas SET postada_em = ? WHERE uid = ?",
                  ("2020-01-01T10:00:00", "mercadolivre:1"))
    assert banco.postadas_hoje() == 1
    assert banco.total_postadas() == 2


def test_migracao_banco_antigo(tmp_path, monkeypatch, nova_oferta):
    # simula um banco criado antes da coluna `chave` existir
    arq = tmp_path / "velho.db"
    con = sqlite3.connect(arq)
    con.execute(
        "CREATE TABLE postadas (uid TEXT PRIMARY KEY, plataforma TEXT,"
        " titulo TEXT, preco REAL, postada_em TEXT)"
    )
    con.execute("INSERT INTO postadas VALUES"
                " ('mercadolivre:1','mercadolivre','Antigo',10.0,'2026-01-01T00:00:00')")
    con.commit()
    con.close()
    monkeypatch.setattr(db, "_DB", arq)

    db.registrar(nova_oferta(id_produto="2", titulo="Novo"))  # não explode
    con = sqlite3.connect(arq)
    colunas = {linha[1] for linha in con.execute("PRAGMA table_info(postadas)")}
    con.close()
    assert "chave" in colunas
    assert not db.ja_postada("mercadolivre:1", 7)  # post antigo, expirado
    assert db.ja_postada("mercadolivre:2", 7)
    assert db.chave_recente("novo", 3)