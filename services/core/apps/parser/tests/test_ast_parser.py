from apps.parser.ast_parser import parse_python_file


class TestParsePythonFile:
    def test_empty_file(self):
        result = parse_python_file('')
        assert result['error'] is False
        assert result['imports'] == []
        assert result['functions'] == []
        assert result['classes'] == []
        assert result['ordered_items'] == []

    def test_syntax_error(self):
        result = parse_python_file('def foo(:')
        assert result['error'] is True
        assert 'SyntaxError' in result['error_message']

    def test_simple_function(self):
        code = '''
def greet(name):
    """Say hello."""
    return f"Hello {name}"
'''
        result = parse_python_file(code)
        assert result['error'] is False
        assert len(result['functions']) == 1
        assert result['functions'][0]['name'] == 'greet'
        assert result['functions'][0]['docstring'] == 'Say hello.'
        assert result['functions'][0]['args'][0]['name'] == 'name'
        assert result['functions'][0]['returns'] is None

    def test_class_with_methods(self):
        code = '''
class Calculator:
    """A simple calculator."""

    def add(self, a, b):
        return a + b

    def subtract(self, a, b):
        return a - b
'''
        result = parse_python_file(code)
        assert result['error'] is False
        assert len(result['classes']) == 1
        cls = result['classes'][0]
        assert cls['name'] == 'Calculator'
        assert cls['docstring'] == 'A simple calculator.'
        assert len(cls['methods']) == 2
        assert cls['methods'][0]['name'] == 'add'
        assert cls['methods'][1]['name'] == 'subtract'

    def test_imports(self):
        code = '''
import os
import sys
from datetime import datetime, timedelta
'''
        result = parse_python_file(code)
        assert len(result['imports']) == 3

    def test_module_docstring(self):
        code = '''"""This module does things."""
def foo():
    pass
'''
        result = parse_python_file(code)
        assert result['module_docstring'] == 'This module does things.'

    def test_async_function(self):
        code = '''
async def fetch_data(url):
    """Fetch data from URL."""
    return await request(url)
'''
        result = parse_python_file(code)
        assert len(result['functions']) == 1
        assert result['functions'][0]['is_async'] is True

    def test_connections(self):
        code = '''
def helper():
    pass

def caller():
    return helper()
'''
        result = parse_python_file(code)
        assert 'helper' in result['functions'][1]['connections']

    def test_decorators(self):
        code = '''
@staticmethod
@log
def method():
    pass
'''
        result = parse_python_file(code)
        assert len(result['functions'][0]['decorators']) == 2
        assert 'staticmethod' in result['functions'][0]['decorators'][0]
