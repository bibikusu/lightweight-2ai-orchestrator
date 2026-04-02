import pytest
from unittest.mock import patch
from typing import List

# Git command mock registry with default responses
GIT_COMMAND_REGISTRY = {
    'status': {'returncode': 0, 'stdout': 'On branch main\nnothing to commit, working tree clean\n', 'stderr': ''},
    'branch': {'returncode': 0, 'stdout': '* main\n', 'stderr': ''},
    'log': {'returncode': 0, 'stdout': 'commit abc123\nAuthor: Test User\n\n    Initial commit\n', 'stderr': ''},
    'diff': {'returncode': 0, 'stdout': '', 'stderr': ''},
    'add': {'returncode': 0, 'stdout': '', 'stderr': ''},
    'commit': {'returncode': 0, 'stdout': '[main abc123] Test commit\n', 'stderr': ''},
    'push': {'returncode': 0, 'stdout': 'Everything up-to-date\n', 'stderr': ''},
    'pull': {'returncode': 0, 'stdout': 'Already up to date.\n', 'stderr': ''},
    'clone': {'returncode': 0, 'stdout': 'Cloning into repository...\n', 'stderr': ''},
    'fetch': {'returncode': 0, 'stdout': '', 'stderr': ''},
    'merge': {'returncode': 0, 'stdout': 'Already up to date.\n', 'stderr': ''},
    'checkout': {'returncode': 0, 'stdout': 'Switched to branch\n', 'stderr': ''},
    'remote': {'returncode': 0, 'stdout': 'origin\n', 'stderr': ''},
    'config': {'returncode': 0, 'stdout': '', 'stderr': ''},
    'init': {'returncode': 0, 'stdout': 'Initialized empty Git repository\n', 'stderr': ''},
    'tag': {'returncode': 0, 'stdout': '', 'stderr': ''},
    'show': {'returncode': 0, 'stdout': 'commit abc123\n', 'stderr': ''},
    'reset': {'returncode': 0, 'stdout': '', 'stderr': ''},
    'rebase': {'returncode': 0, 'stdout': 'Successfully rebased\n', 'stderr': ''},
    'stash': {'returncode': 0, 'stdout': '', 'stderr': ''}
}

# Default response for unknown git commands
DEFAULT_GIT_RESPONSE = {
    'returncode': 0,
    'stdout': '',
    'stderr': ''
}

class MockGitResult:
    """Mock object that mimics subprocess.CompletedProcess for git commands."""
    def __init__(self, returncode: int = 0, stdout: str = '', stderr: str = ''):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.args = []

def parse_git_command(cmd_args: List[str]) -> str:
    """Extract the git subcommand from command arguments."""
    if not cmd_args or len(cmd_args) < 2:
        return 'unknown'
    
    # Handle 'git' as first argument
    if cmd_args[0] == 'git':
        return cmd_args[1] if len(cmd_args) > 1 else 'unknown'
    
    # Handle direct subcommand
    return cmd_args[0]

def mock_git_subprocess_run(cmd_args: List[str], **kwargs) -> MockGitResult:
    """Mock subprocess.run for git commands with registry-based responses."""
    git_cmd = parse_git_command(cmd_args)
    
    # Get response from registry or use default
    response = GIT_COMMAND_REGISTRY.get(git_cmd, DEFAULT_GIT_RESPONSE)
    
    return MockGitResult(
        returncode=response['returncode'],
        stdout=response['stdout'],
        stderr=response['stderr']
    )

@pytest.fixture
def mock_git_command():
    """Shared fixture for mocking git commands with resilient defaults.
    
    This fixture provides a foundation for git command mocking that:
    - Returns sensible defaults for known git commands
    - Gracefully handles unknown commands without breaking tests
    - Can be extended by individual tests as needed
    
    Usage:
        def test_something(mock_git_command):
            # Git commands are automatically mocked
            result = subprocess.run(['git', 'status'], capture_output=True, text=True)
            assert result.returncode == 0
    """
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = mock_git_subprocess_run
        yield mock_run

@pytest.fixture
def git_mock_registry():
    """Fixture providing access to git command registry for test customization."""
    return GIT_COMMAND_REGISTRY.copy()