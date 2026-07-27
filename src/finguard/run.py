import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="finguard",
        description="FinGuard — Escudo de Compliance e Risco Regulatório (Future Minds 3 / Zup)",
    )
    parser.add_argument(
        "--input",
        default="docs/dataset_finguard_desafio_3 (3).csv",
        help="Caminho do CSV de reclamações a processar",
    )
    parser.add_argument(
        "--output",
        default="output",
        help="Diretório de saída para relatório e logs",
    )
    return parser


def main() -> None:
    parser = build_parser()
    parser.parse_args()
    raise NotImplementedError("pipeline ainda não implementado — próximas tarefas do backlog")


if __name__ == "__main__":
    main()
