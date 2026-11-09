import pytest

import rodovias_h3 as rh3


def test_disponiveis():
    for resolucao in (5, 6, 7, 8):
        assert (2023, resolucao) in rh3.disponiveis()


@pytest.mark.parametrize(
    "br, uf, km, resolucao, esperado",
    [
        (101, "PE", 45.3, 8, "8881838831fffff"),
        (101, "pe", 45.3, 8, "8881838831fffff"),
        (101, "PE", 45.3, 5, "8581838bfffffff"),
        (101, "PE", 45.3, 6, "868183887ffffff"),
        (101, "PE", 45.3, 7, "878183883ffffff"),
        (101, "PE", 41.4, 8, "88818388a5fffff"),  # divisa entre trechos: vale o que começa no km
        (101, "PE", 0, 8, "8881830549fffff"),
    ],
)
def test_h3_do_km(br, uf, km, resolucao, esperado):
    assert rh3.h3_do_km(br, uf, km, resolucao=resolucao) == esperado


def test_km_fora_da_rodovia():
    with pytest.raises(rh3.KmForaDaRodovia):
        rh3.h3_do_km(101, "PE", 9999)
    with pytest.raises(rh3.KmForaDaRodovia):
        rh3.h3_do_km(9999, "PE", 1)


def test_referencia_indisponivel():
    with pytest.raises(rh3.ReferenciaIndisponivel):
        rh3.h3_do_km(101, "PE", 45.3, resolucao=12)
    with pytest.raises(rh3.ReferenciaIndisponivel):
        rh3.h3_do_km(101, "PE", 45.3, ano=1990)


def test_h3_do_km_lote():
    assert rh3.h3_do_km_lote([(101, "PE", 45.3), (101, "PE", 9999)]) == ["8881838831fffff", None]


def test_h3_da_coordenada():
    assert rh3.h3_da_coordenada(-7.5000614899999505, -34.98503513999998) == "8881830549fffff"


def test_km_do_h3():
    faixas = rh3.km_do_h3("8881838831fffff")
    assert any(f.br == 101 and f.uf == "PE" and f.km_ini <= 45.3 <= f.km_fim for f in faixas)
    with pytest.raises(ValueError):
        rh3.km_do_h3("invalido")


def test_ida_e_volta():
    """O H3 de um km sempre contém esse km na consulta inversa."""
    for km in (0.5, 50, 100.25, 200):
        celula = rh3.h3_do_km(101, "PE", km)
        assert any(f.km_ini <= km <= f.km_fim for f in rh3.km_do_h3(celula) if f.br == 101 and f.uf == "PE")
