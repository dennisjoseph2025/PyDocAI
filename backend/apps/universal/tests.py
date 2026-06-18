from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.projects.models import Project, ProjectFile
from apps.universal.tasks import (
    _file_priority, _build_file_tree, _format_tree,
    _detect_req_files, _validate_and_fix_output,
)
from apps.universal.prompts import get_prompt, MAX_SOURCE_CHARS

User = get_user_model()


# ── Pure function tests (no DB) ───────────────────────────────

class TestFilePriority:
    def test_urls_highest_priority(self):
        assert _file_priority("myapp/urls.py") == 10

    def test_views_high_priority(self):
        assert _file_priority("myapp/views.py") == 8

    def test_models_priority(self):
        assert _file_priority("myapp/models.py") == 7

    def test_config_priority(self):
        assert _file_priority("settings/base.py") == 6
        assert _file_priority("myapp/Dockerfile") == 6
        assert _file_priority("package.json") == 6

    def test_services_priority(self):
        assert _file_priority("myapp/services.py") == 5
        assert _file_priority("myapp/auth.py") == 5

    def test_admin_priority(self):
        assert _file_priority("myapp/admin.py") == 4
        assert _file_priority("myapp/tasks.py") == 4

    def test_utils_priority(self):
        assert _file_priority("myapp/utils.py") == 3
        assert _file_priority("myapp/constants.py") == 3

    def test_css_priority(self):
        assert _file_priority("styles/app.css") == 2
        assert _file_priority("assets/logo.svg") == 2

    def test_unknown_lowest_priority(self):
        assert _file_priority("README.md") == 1
        assert _file_priority("data/somefile.txt") == 1

    def test_case_insensitive(self):
        assert _file_priority("MYAPP/URLs.py") == 10
        assert _file_priority("MYAPP/MODELS.py") == 7


class TestBuildFileTree:
    def test_empty_list(self):
        assert _build_file_tree([]) == {}

    def test_single_file(self):
        result = _build_file_tree(["main.py"])
        assert result == {"main.py": {}}

    def test_nested_paths(self):
        files = ["src/app/main.py", "src/app/utils.py", "README.md"]
        tree = _build_file_tree(files)
        assert "src" in tree
        assert "app" in tree["src"]
        assert "main.py" in tree["src"]["app"]
        assert "utils.py" in tree["src"]["app"]
        assert "README.md" in tree

    def test_backslash_normalized(self):
        tree = _build_file_tree(["src\\app\\main.py"])
        assert "src" in tree and "app" in tree["src"] and "main.py" in tree["src"]["app"]


class TestFormatTree:
    def test_single_file(self):
        tree = _build_file_tree(["main.py"])
        lines = _format_tree(tree)
        assert lines == ["└── main.py"]

    def test_nested_tree(self):
        files = ["src/main.py", "src/utils.py", "README.md"]
        tree = _build_file_tree(files)
        lines = _format_tree(tree)
        result = "\n".join(lines)
        assert "README.md" in result
        assert "src/" in result
        assert "main.py" in result
        assert "utils.py" in result

    def test_directories_have_slash(self):
        tree = _build_file_tree(["src/main.py"])
        lines = _format_tree(tree)
        assert "src/" in lines[0]


class TestDetectReqFiles:
    def test_detects_requirements(self):
        files = ["README.md", "requirements.txt", "src/main.py"]
        assert _detect_req_files(files) == ["requirements.txt"]

    def test_detects_pyproject(self):
        files = ["pyproject.toml", "src/main.py"]
        assert _detect_req_files(files) == ["pyproject.toml"]

    def test_detects_package_json(self):
        files = ["package.json", "index.js"]
        assert _detect_req_files(files) == ["package.json"]

    def test_multiple_detected(self):
        files = ["requirements.txt", "pyproject.toml", "Pipfile", "README.md"]
        result = _detect_req_files(files)
        assert "requirements.txt" in result
        assert "pyproject.toml" in result
        assert "Pipfile" in result

    def test_case_insensitive(self):
        files = ["REQUIREMENTS.TXT"]
        assert _detect_req_files(files) == ["REQUIREMENTS.TXT"]

    def test_no_req_files(self):
        files = ["src/main.py", "README.md"]
        assert _detect_req_files(files) == []


class TestValidateAndFixOutput:
    def test_correct_cd_passes_through(self):
        output = "```bash\ngit clone https://github.com/user/myproject.git\ncd myproject\n```"
        tree = _build_file_tree(["main.py"])
        tree_text = "\n".join(_format_tree(tree))
        result = _validate_and_fix_output(
            output, "https://github.com/user/myproject.git",
            "myproject", tree_text, ["main.py"]
        )
        assert result == output

    @patch("apps.universal.tasks._call_groq")
    def test_wrong_cd_triggers_fix(self, mock_groq):
        mock_groq.return_value = "```bash\ngit clone https://github.com/user/myproject.git\ncd correct_dir\n```"
        output = "```bash\ngit clone https://github.com/user/myproject.git\ncd wrong_dir\n```"
        tree = _build_file_tree(["main.py"])
        tree_text = "\n".join(_format_tree(tree))
        result = _validate_and_fix_output(
            output, "https://github.com/user/myproject.git",
            "myproject", tree_text, ["main.py"]
        )
        mock_groq.assert_called_once()
        assert "correct_dir" in result


# ── Prompt tests ──────────────────────────────────────────────

class TestGetPrompt:
    def test_includes_project_name(self):
        prompt = get_prompt("universal", "print('hello')", "MyProject")
        assert "MyProject" in prompt

    def test_includes_source_code(self):
        prompt = get_prompt("universal", "def foo(): pass", "Proj")
        assert "def foo(): pass" in prompt

    def test_truncates_long_source(self):
        long_code = "x = 1\n" * (MAX_SOURCE_CHARS // 4 + 100)
        prompt = get_prompt("universal", long_code, "Proj")
        assert len(prompt) < len(long_code) + 5000
        assert "[truncated]" in prompt

    def test_escapes_triple_backticks(self):
        malicious = "```\nmalicious code\n```"
        prompt = get_prompt("universal", malicious, "Proj")
        assert "```" not in prompt[prompt.index("Source code"):prompt.index("```", prompt.index("Source code"))]

    def test_includes_repo_dir_from_github_url(self):
        prompt = get_prompt("universal", "code", "Proj", github_url="https://github.com/user/my-repo.git")
        assert "my-repo" in prompt

    def test_falls_back_to_project_name_for_repo_dir(self):
        prompt = get_prompt("universal", "code", "MyProject")
        assert "MyProject" in prompt

    def test_includes_file_tree_when_provided(self):
        prompt = get_prompt("universal", "code", "Proj", file_tree="└── main.py")
        assert "└── main.py" in prompt

    def test_includes_req_files_when_provided(self):
        prompt = get_prompt("universal", "code", "Proj", req_files=["requirements.txt"])
        assert "requirements.txt" in prompt


# ── Celery task tests (need DB) ───────────────────────────────

class GenerateUniversalDocsTaskTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="universal@test.com", name="Universal", password="pwd"
        )
        self.project = Project.objects.create(
            user=self.user, name="TestProj",
            source_type=Project.SourceType.FILE,
            status=Project.Status.PENDING,
        )
        ProjectFile.objects.create(
            project=self.project,
            file_name="main.py",
            file_path="main.py",
            content="def foo(): pass\n",
        )

    @patch("apps.universal.tasks._call_groq")
    def test_task_completes_successfully(self, mock_groq):
        from apps.universal.tasks import generate_universal_docs_task
        mock_groq.return_value = "# Documentation\n\nSome content"
        result = generate_universal_docs_task(str(self.project.id), "universal")
        self.project.refresh_from_db()
        assert self.project.status == Project.Status.DONE
        assert self.project.generated_docs == "# Documentation\n\nSome content"
        assert result["project_id"] == str(self.project.id)

    @patch("apps.universal.tasks._call_groq")
    def test_rejection_sets_failed_status(self, mock_groq):
        from apps.universal.tasks import generate_universal_docs_task
        mock_groq.return_value = "REJECT: Project is not a valid codebase"
        generate_universal_docs_task(str(self.project.id), "universal")
        self.project.refresh_from_db()
        assert self.project.status == Project.Status.FAILED
        assert "REJECT" in self.project.error_message

    @patch("apps.universal.tasks._call_groq")
    def test_groq_failure_sets_failed_status(self, mock_groq):
        from apps.universal.tasks import generate_universal_docs_task
        mock_groq.side_effect = Exception("API timeout")
        generate_universal_docs_task(str(self.project.id), "universal")
        self.project.refresh_from_db()
        assert self.project.status == Project.Status.FAILED

    def test_unknown_project_returns_error(self):
        from apps.universal.tasks import generate_universal_docs_task
        result = generate_universal_docs_task("00000000-0000-0000-0000-000000000000", "universal")
        assert "error" in result


class ImportUniversalGithubTaskTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="github@test.com", name="GitHub", password="pwd"
        )
        self.project = Project.objects.create(
            user=self.user, name="GitProj",
            source_type=Project.SourceType.GITHUB,
            github_url="https://github.com/user/repo",
            status=Project.Status.PENDING,
        )

    @patch("apps.universal.tasks._download_github_zipball")
    @patch("apps.universal.tasks._fetch_public_repo_api")
    @patch("apps.universal.tasks.generate_universal_docs_task.delay")
    def test_import_creates_files_and_delegates(self, mock_delay, mock_fetch, mock_download):
        from apps.universal.tasks import import_universal_github_task
        mock_download.return_value = [
            {"file_path": "src/main.py", "content": "print('hello')"},
        ]
        import_universal_github_task(
            str(self.project.id), "universal", "user/repo", "", "main"
        )
        assert ProjectFile.objects.filter(project=self.project).count() == 1
        mock_delay.assert_called_once_with(str(self.project.id), "universal")

    @patch("apps.universal.tasks._download_github_zipball")
    def test_no_files_sets_failed(self, mock_download):
        from apps.universal.tasks import import_universal_github_task
        mock_download.return_value = []
        import_universal_github_task(
            str(self.project.id), "universal", "user/repo", "", "main"
        )
        self.project.refresh_from_db()
        assert self.project.status == Project.Status.FAILED
