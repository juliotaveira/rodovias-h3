# Referência do rodovias-h3

## Exemplos de uso

```python
import rodovias_h3 as rh3

# BR + UF + km → H3 (resolução 8 e SNV mais recente, por padrão)
rh3.h3_do_km(101, "PE", 45.3)                    # '8881838831fffff'
rh3.h3_do_km(101, "PE", 45.3, resolucao=7)       # '878183883ffffff'
rh3.h3_do_km(101, "PE", 45.3, resolucao=5)       # '8581838bfffffff'
rh3.h3_do_km(101, "PE", 45.3, ano=2023)

# Vários de uma vez (km não encontrado → None)
rh3.h3_do_km_lote([(101, "PE", 45.3), (232, "PE", 10), (101, "PE", 9999)])
# ['8881838831fffff', '8881839ad7fffff', None]

# Latitude/longitude → H3
rh3.h3_da_coordenada(-7.50006, -34.98503)        # '8881830549fffff'
rh3.h3_da_coordenada(-7.50006, -34.98503, 6)

# H3 → BRs, UFs e faixas de km que passam na célula
rh3.km_do_h3("8881838831fffff")
# [Faixa(br=101, uf='PE', km_ini=45.281, km_fim=46.127, h3='8881838831fffff', principal=True), ...]

# Dados incluídos no pacote: (ano do SNV, resolução)
rh3.disponiveis()                                # [(2023, 5), (2023, 6), (2023, 7), (2023, 8)]
```

Com DataFrame (o pandas é do seu projeto, não do pacote):

```python
df["h3"] = rh3.h3_do_km_lote(zip(df["br"], df["uf"], df["km"]), resolucao=8)
```

Cada consulta leva poucos microssegundos. O índice é carregado uma vez por ano/resolução: de ~0,05 s (res 5) a ~0,5 s (res 8).

## API

| Função | Retorno | Descrição |
|---|---|---|
| `h3_do_km(br, uf, km, resolucao=8, ano=None)` | `str` | Célula H3 do km. Lança `KmForaDaRodovia` se não houver. |
| `h3_do_km_lote(itens, resolucao=8, ano=None)` | `list[str \| None]` | Vários `(br, uf, km)`. Kms não encontrados retornam `None`. |
| `h3_da_coordenada(lat, lon, resolucao=8)` | `str` | Célula H3 de uma coordenada WGS84. Não depende dos dados. |
| `km_do_h3(celula, ano=None)` | `list[Faixa]` | Faixas de km que passam na célula. A resolução vem do próprio código. |
| `disponiveis()` | `list[tuple[int, int]]` | Pares `(ano, resolução)` incluídos. |
| `referencia(resolucao=8, ano=None)` | `Referencia` | Objeto com os índices carregados (`.h3_do_km`, `.km_do_h3`, `.faixas`). |

- `ano=None` usa o ano mais recente disponível para a resolução.
- `uf` aceita maiúsculas ou minúsculas.

### Exceções

Todas herdam de `RodoviasH3Erro`:

- `KmForaDaRodovia`: a BR/UF não existe ou o km está fora dela.
- `ReferenciaIndisponivel`: não há dados para o ano/resolução pedido.

## Regras de negócio

1. **O km é por UF.** Como no SNV, a quilometragem reinicia em cada UF, então a UF é obrigatória.
2. **Interpolação.** O ponto do km é interpolado proporcionalmente dentro do trecho do SNV (`km_inicial` a `km_final`), em metros (EPSG:5880), e depois convertido em H3.
3. **Trechos sobrepostos** (contornos, variantes, acessos com a mesma numeração de km):
   - `h3_do_km` retorna o **eixo principal** (trecho tipo `B`).
   - Os demais trechos só respondem nos kms que o eixo principal não cobre.
   - `km_do_h3` retorna **todas** as faixas da célula. O campo `principal` indica qual é do eixo principal.
4. **Divisa entre trechos ou células:** vale a faixa que **começa** no km.
5. **Precisão:**
   - Os limites das faixas foram calculados com amostras a cada 50 m.
   - Kms a menos de ~50 m de uma borda podem cair na célula vizinha.
   - Isso é menor que o erro do próprio km nominal do SNV, que é de centenas de metros.
6. **Resolução** (todas com os mesmos trechos e regras):

   | Res | Aresta | Rodovia por célula | Uso |
   |---|---|---|---|
   | 5 | ~9,9 km | ~20 km | visão estadual / mesorregião |
   | 6 | ~3,7 km | ~7 km | agregação regional |
   | 7 | ~1,4 km | ~3 km | trechos de rodovia |
   | 8 | ~530 m | ~1 km | **recomendada**: casa com a precisão do km |

## Dados

Os dados ficam em `src/rodovias_h3/dados/snv<ano>_res<resolucao>.csv.gz`:

| coluna | descrição |
|---|---|
| `br` | número da BR |
| `uf` | sigla da UF |
| `km_ini`, `km_fim` | faixa de km do trecho dentro da célula |
| `h3` | código da célula H3 |
| `principal` | `1` = eixo principal (tipo `B`), `0` = contorno/variante/acesso etc. |

Versão atual: **SNV 2023**, resoluções **5, 6, 7 e 8**, todos os trechos com traçado.

## Atualizar ou adicionar dados

Os arquivos são gerados fora deste pacote, a partir do traçado do SNV. O pacote não depende desse processo.

1. Gere um arquivo `snv<ano>_res<resolucao>.csv.gz` para cada resolução, com as colunas da seção **Dados**.
2. Coloque os arquivos em `src/rodovias_h3/dados/`.
3. Atualize a seção **Dados** desta referência.
4. Suba a versão em `pyproject.toml` e em `src/rodovias_h3/__init__.py` (ex.: `0.3.0` para um novo ano do SNV).
5. Rode os testes e gere o pacote.

## Desenvolvimento

```bash
poetry install          # cria .venv com h3 + pytest
poetry run pytest       # testes
poetry build            # gera dist/*.whl e dist/*.tar.gz (com os dados)
```
