"""
Test configuration and fixtures
"""

import pytest
from pathlib import Path


@pytest.fixture
def temp_project_dir(tmp_path):
    """Create a temporary project directory for testing"""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    return project_dir


@pytest.fixture
def sample_code_file(temp_project_dir):
    """Create a sample Python file for testing"""
    code_file = temp_project_dir / "sample.py"
    code_file.write_text("""
def hello_world():
    '''Say hello'''
    return "Hello, World!"

class MyClass:
    '''Sample class'''
    def __init__(self, name):
        self.name = name
    
    def greet(self):
        return f"Hello, {self.name}!"
""")
    return code_file
