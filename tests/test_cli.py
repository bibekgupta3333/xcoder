"""
Tests for XCoder CLI
"""

import pytest
from typer.testing import CliRunner
from xcoder.cli import app

runner = CliRunner()


def test_version():
    """Test version command"""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "XCoder" in result.stdout
    assert "version" in result.stdout


def test_help():
    """Test help command"""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "XCoder" in result.stdout


def test_init_help():
    """Test init command help"""
    result = runner.invoke(app, ["init", "--help"])
    assert result.exit_code == 0
    assert "Initialize" in result.stdout


def test_ragify_help():
    """Test ragify command help"""
    result = runner.invoke(app, ["ragify", "--help"])
    assert result.exit_code == 0
    assert "Vectorize" in result.stdout or "ragify" in result.stdout.lower()


def test_agent_help():
    """Test agent command help"""
    result = runner.invoke(app, ["agent", "--help"])
    assert result.exit_code == 0
    assert "agent" in result.stdout.lower()


def test_memory_help():
    """Test memory command help"""
    result = runner.invoke(app, ["memory", "--help"])
    assert result.exit_code == 0
    assert "memory" in result.stdout.lower()
