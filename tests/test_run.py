from unittest.mock import patch

from finguard.run import build_parser, main


def test_build_parser_defaults():
    args = build_parser().parse_args([])
    assert args.input == 'docs/dataset_finguard_desafio_3 (3).csv'
    assert args.output == "output"
    assert args.limit is None


def test_build_parser_accepts_overrides():
    args = build_parser().parse_args(["--input", "x.csv", "--output", "out2", "--limit", "3"])
    assert args.input == "x.csv"
    assert args.output == "out2"
    assert args.limit == 3


def test_main_calls_pipeline_with_parsed_args(monkeypatch):
    monkeypatch.setattr("sys.argv", ["finguard", "--input", "x.csv", "--output", "out2", "--limit", "2"])
    with patch("finguard.run.load_dotenv") as mock_load_dotenv, patch(
        "finguard.run.processar_triagem"
    ) as mock_processar:
        main()

    mock_load_dotenv.assert_called_once()
    mock_processar.assert_called_once_with("x.csv", "out2", limit=2)
