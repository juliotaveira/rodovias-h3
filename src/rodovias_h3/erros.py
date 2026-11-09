"""Exceções do pacote rodovias_h3."""


class RodoviasH3Erro(Exception):
    """Base de todas as exceções do pacote."""


class ReferenciaIndisponivel(RodoviasH3Erro, LookupError):
    """Não há dados de referência para o ano/resolução pedidos."""


class KmForaDaRodovia(RodoviasH3Erro, LookupError):
    """O km (ou a BR/UF) não existe nos dados de referência."""
