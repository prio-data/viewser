import pytest
from click.testing import CliRunner
from viewser.commands.config import cli
from viewser.commands.documentation import features_cli, transforms_cli, transform_cli


@pytest.fixture(scope="module")
def runner():
    return CliRunner()


def test_config(runner):
#    runner = CliRunner()
    result = runner.invoke(cli, ['list'], catch_exceptions=False)
    assert result.exit_code == 0
    assert 'https' in result.output


def test_documentation(runner):
#    runner = CliRunner()
    result = runner.invoke(features_cli, ['list', 'cm'], catch_exceptions=False)
    assert result.exit_code == 0
    assert 'ged2_cm' in result.output

    result = runner.invoke(features_cli, ['list', 'pgm'], catch_exceptions=False)
    assert result.exit_code == 0
    assert 'ged2_pgm' in result.output

    result = runner.invoke(transforms_cli, ['list'], catch_exceptions=False)
    assert result.exit_code == 0
    assert 'treelag' in result.output

    result = runner.invoke(transforms_cli, ['at_loa', 'priogrid_month'], catch_exceptions=False)
    assert result.exit_code == 0
    assert 'treelag' in result.output

    result = runner.invoke(transform_cli, ['show', 'treelag'], catch_exceptions=False)
    assert result.exit_code == 0
    assert 'angle' in result.output


if __name__ == '__main__':
    test_documentation(runner)
    test_config(runner)
