# rodovias-h3

Consulta **offline** do código [H3](https://h3geo.org/) de rodovias federais brasileiras a partir de **BR + UF + km**.

A única dependência é a biblioteca [`h3`](https://pypi.org/project/h3/). Os dados de referência já vêm dentro do pacote, sem banco de dados ou acesso à internet.

## Instalação

Requer Python 3.10 ou mais recente.

```bash
pip install "git+https://github.com/juliotaveira/rodovias-h3.git@v0.2.0"
```

Com Poetry:

```bash
poetry add git+https://github.com/juliotaveira/rodovias-h3.git#v0.2.0
```

## Uso

```python
import rodovias_h3 as rh3

rh3.h3_do_km(101, "PE", 45.3)            # '8881838831fffff'
rh3.km_do_h3("8881838831fffff")          # faixas de km que passam na célula
rh3.h3_da_coordenada(-7.50006, -34.98503)  # '8881830549fffff'
rh3.disponiveis()                        # [(2023, 5), (2023, 6), (2023, 7), (2023, 8)]
```

A API completa, as regras de negócio e o formato dos dados estão em [docs/referencia.md](docs/referencia.md).

## Fonte dos dados

Os dados incluídos são derivados do traçado do **Sistema Nacional de Viação (SNV)**, do **DNIT**, ano-base 2023, nas resoluções H3 5, 6, 7 e 8. Este projeto não é oficial nem tem vínculo com o DNIT.

## Desenvolvimento

```bash
poetry install
poetry run pytest
poetry build
```

## Licença

O código é distribuído sob a licença [MIT](LICENSE). Os dados derivados do SNV seguem as condições de uso da fonte original.
