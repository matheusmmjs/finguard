import argparse

from dotenv import load_dotenv

from finguard.pipeline import processar_triagem


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="finguard",
        description="FinGuard — Escudo de Compliance e Risco Regulatório (Future Minds 3 / Zup)",
    )
    parser.add_argument(
        "--input",
        default='docs/dataset_finguard_desafio_3 (3).csv',
        help="Caminho do CSV de reclamações a processar",
    )
    parser.add_argument(
        "--output",
        default="output",
        help="Diretório de saída para relatório e logs",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Processa só as N primeiras linhas (útil pra testar sem gastar tokens à toa)",
    )
    return parser


def main() -> None:
    load_dotenv()
    parser = build_parser()
    args = parser.parse_args()
    processar_triagem(args.input, args.output, limit=args.limit)


if __name__ == "__main__":
    main()
