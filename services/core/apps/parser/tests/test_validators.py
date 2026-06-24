from apps.parser.validators import should_exclude, validate_python_code


class TestValidatePythonCode:
    def test_valid_code(self):
        is_valid, error = validate_python_code('print("hello")')
        assert is_valid is True
        assert error is None

    def test_empty_code(self):
        is_valid, error = validate_python_code('')
        assert is_valid is False
        assert 'empty' in error

    def test_whitespace_only(self):
        is_valid, error = validate_python_code('   ')
        assert is_valid is False

    def test_syntax_error(self):
        is_valid, error = validate_python_code('def foo(:')
        assert is_valid is False
        assert 'SyntaxError' in error


class TestShouldExclude:
    def test_normal_file(self):
        assert should_exclude('myproject/utils/helpers.py') is False
        assert should_exclude('src/main.py') is False

    def test_venv(self):
        assert should_exclude('venv/lib/site.py') is True

    def test_node_modules(self):
        assert should_exclude('project/node_modules/react/index.js') is True

    def test_pycache(self):
        assert should_exclude('project/__pycache__/main.cpython-310.pyc') is True

    def test_git(self):
        assert should_exclude('.git/config') is True
        assert should_exclude('.github/workflows/build.yml') is True

    def test_egg_info(self):
        assert should_exclude('src/foo.egg-info/PKG-INFO') is True

    def test_build_dirs(self):
        assert should_exclude('build/output.o') is True
        assert should_exclude('dist/bundle.js') is True

    def test_migrations(self):
        assert should_exclude('app/migrations/0001_initial.py') is True

    def test_mixed_path(self):
        assert should_exclude('project/sub/venv/lib/file.py') is True
        assert should_exclude('project/sub/not-venv/lib/file.py') is False
