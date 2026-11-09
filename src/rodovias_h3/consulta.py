"""Consulta offline do código H3 de rodovias federais (BR + UF + km).

Os dados de referência ficam em `dados/snv<ano>_res<resolucao>.csv.gz`, gerados a
partir do traçado do SNV. Cada linha é uma faixa de km de um trecho que cai numa
célula H3. Ao carregar, os índices são montados em memória e as consultas são
feitas por busca binária.
"""

import bisect
import csv
import gzip
import io
import re
from functools import lru_cache
from importlib.resources import files
from typing import Iterable, NamedTuple

import h3

from .erros import KmForaDaRodovia, ReferenciaIndisponivel

_ARQUIVO = re.compile(r"^snv(\d{4})_res(\d{1,2})\.csv\.gz$")


class Faixa(NamedTuple):
    """Faixa de km de uma rodovia dentro de uma célula H3."""

    br: int
    uf: str
    km_ini: float
    km_fim: float
    h3: str
    principal: bool


def _pasta_dados():
    return files(__package__).joinpath("dados")


def disponiveis() -> list[tuple[int, int]]:
    """Pares (ano do SNV, resolução H3) incluídos no pacote."""
    return sorted(
        (int(m[1]), int(m[2]))
        for arquivo in _pasta_dados().iterdir()
        if (m := _ARQUIVO.match(arquivo.name))
    )


def _ano_padrao(resolucao: int, ano: int | None) -> int:
    anos = [a for a, r in disponiveis() if r == resolucao]
    if ano is None and anos:
        return max(anos)
    if ano not in anos:
        raise ReferenciaIndisponivel(
            f"Sem dados para ano={ano}, resolução={resolucao}. Disponíveis: {disponiveis()}"
        )
    return ano


def _sem_sobreposicao(faixas: list[Faixa]) -> list[tuple[float, float, str]]:
    """Resolve sobreposições de uma rodovia: o eixo principal vem primeiro e,
    em seguida, as demais faixas só preenchem os kms ainda não cobertos.
    Intervalos semiabertos [km_ini, km_fim): na divisa vale a faixa que começa no km.
    """
    cobertos: list[tuple[float, float]] = []  # ordenados, disjuntos e unidos
    resultado = []
    for f in sorted(faixas, key=lambda f: (not f.principal, f.km_ini)):
        # Partes de [km_ini, km_fim) ainda não cobertas
        atual = f.km_ini
        for ini, fim in cobertos:
            if fim <= atual:
                continue
            if ini >= f.km_fim:
                break
            if ini > atual:
                resultado.append((atual, ini, f.h3))
            atual = max(atual, fim)
        if atual < f.km_fim:
            resultado.append((atual, f.km_fim, f.h3))

        # Une a faixa aos kms cobertos (o eixo principal contínuo vira poucos intervalos)
        ini, fim = f.km_ini, f.km_fim
        restantes = []
        for a, b in cobertos:
            if b < ini or a > fim:
                restantes.append((a, b))
            else:
                ini, fim = min(a, ini), max(b, fim)
        cobertos = sorted(restantes + [(ini, fim)])
    return sorted(resultado)


class Referencia:
    """Dados de referência de um ano do SNV numa resolução H3, indexados em memória."""

    def __init__(self, ano: int, resolucao: int):
        self.ano = ano
        self.resolucao = resolucao
        nome = f"snv{ano}_res{resolucao}.csv.gz"
        with gzip.open(io.BytesIO(_pasta_dados().joinpath(nome).read_bytes()), "rt", encoding="utf-8") as arq:
            self.faixas = [
                Faixa(int(l["br"]), l["uf"], float(l["km_ini"]), float(l["km_fim"]), l["h3"], l["principal"] == "1")
                for l in csv.DictReader(arq)
            ]

        por_rodovia: dict[tuple[int, str], list[Faixa]] = {}
        self._por_h3: dict[str, list[Faixa]] = {}
        for f in self.faixas:
            por_rodovia.setdefault((f.br, f.uf), []).append(f)
            self._por_h3.setdefault(f.h3, []).append(f)

        # Índice para km -> H3: listas paralelas (km_ini, km_fim, h3) ordenadas por km
        self._indice: dict[tuple[int, str], tuple[list, list, list]] = {
            chave: tuple(map(list, zip(*_sem_sobreposicao(faixas))))
            for chave, faixas in por_rodovia.items()
        }

    def h3_do_km(self, br: int, uf: str, km: float) -> str:
        """Célula H3 do km da BR/UF. Lança KmForaDaRodovia se não houver."""
        km = float(km)  # tipos numpy (vindos do pandas) deixam a busca binária ~50x mais lenta
        indice = self._indice.get((int(br), str(uf).upper()))
        if indice is not None:
            inis, fins, celulas = indice
            i = bisect.bisect_right(inis, km) - 1
            if i >= 0 and km <= fins[i]:
                return celulas[i]
        raise KmForaDaRodovia(f"BR-{br}/{uf.upper()} km {km} não encontrado (SNV {self.ano})")

    def km_do_h3(self, celula: str) -> list[Faixa]:
        """Faixas de km (de todas as BRs/UFs e trechos) que passam na célula."""
        return list(self._por_h3.get(celula, []))


@lru_cache(maxsize=None)
def referencia(resolucao: int = 8, ano: int | None = None) -> Referencia:
    """Carrega (uma única vez) os dados de referência. ano=None usa o mais recente."""
    return Referencia(_ano_padrao(resolucao, ano), resolucao)


def h3_do_km(br: int, uf: str, km: float, resolucao: int = 8, ano: int | None = None) -> str:
    """Código H3 do km de uma BR/UF.

    >>> h3_do_km(101, "PE", 45.3)
    '8881838831fffff'
    """
    return referencia(resolucao, ano).h3_do_km(br, uf, km)


def h3_do_km_lote(
    itens: Iterable[tuple[int, str, float]], resolucao: int = 8, ano: int | None = None
) -> list[str | None]:
    """Códigos H3 de vários (br, uf, km). Kms não encontrados retornam None."""
    ref = referencia(resolucao, ano)
    resultado = []
    for br, uf, km in itens:
        try:
            resultado.append(ref.h3_do_km(br, uf, km))
        except KmForaDaRodovia:
            resultado.append(None)
    return resultado


def h3_da_coordenada(lat: float, lon: float, resolucao: int = 8) -> str:
    """Código H3 de uma coordenada WGS84 (latitude, longitude)."""
    return h3.latlng_to_cell(lat, lon, resolucao)


def km_do_h3(celula: str, ano: int | None = None) -> list[Faixa]:
    """BRs, UFs e faixas de km que passam na célula (a resolução vem do próprio código)."""
    if not h3.is_valid_cell(celula):
        raise ValueError(f"Código H3 inválido: {celula!r}")
    return referencia(h3.get_resolution(celula), ano).km_do_h3(celula)
