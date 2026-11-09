"""rodovias_h3: consulta offline do código H3 de rodovias federais (BR + UF + km)."""

from .consulta import (
    Faixa,
    Referencia,
    disponiveis,
    h3_da_coordenada,
    h3_do_km,
    h3_do_km_lote,
    km_do_h3,
    referencia,
)
from .erros import KmForaDaRodovia, ReferenciaIndisponivel, RodoviasH3Erro

__version__ = "0.2.0"

__all__ = [
    "Faixa",
    "KmForaDaRodovia",
    "Referencia",
    "ReferenciaIndisponivel",
    "RodoviasH3Erro",
    "disponiveis",
    "h3_da_coordenada",
    "h3_do_km",
    "h3_do_km_lote",
    "km_do_h3",
    "referencia",
]
