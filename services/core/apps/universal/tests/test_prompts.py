import re

from apps.universal.prompts import MAX_SOURCE_CHARS, get_prompt


class TestGetPrompt:
    def test_basic_prompt(self):
        prompt = get_prompt(
            mode='universal',
            source_code='print("hello")',
            project_name='Test Project',
            file_list=['main.py'],
            github_url='https://github.com/owner/repo',
            file_tree='main.py',
            req_files=['requirements.txt'],
        )
        assert 'Test Project' in prompt
        assert 'print("hello")' in prompt
        assert 'https://github.com/owner/repo' in prompt
        assert 'requirements.txt' in prompt
        assert 'main.py' in prompt

    def test_truncates_large_source(self):
        large_source = 'x' * (MAX_SOURCE_CHARS + 1000)
        prompt = get_prompt(
            mode='universal',
            source_code=large_source,
            project_name='Test',
            file_list=['main.py'],
        )
        assert '[truncated]' in prompt
        assert len(prompt) < MAX_SOURCE_CHARS + 10000

    def test_escapes_code_blocks(self):
        prompt = get_prompt(
            mode='universal',
            source_code='```dangerous```',
            project_name='Test',
        )
        match = re.search(r'Source code to document:\n```\n(.+?)\n```', prompt, re.DOTALL)
        assert match is not None
        assert '```' not in match.group(1)

    def test_max_chars_param(self):
        prompt = get_prompt(
            mode='universal',
            source_code='test code',
            project_name='Test',
            max_chars=10,
        )
        assert 'test code' in prompt
