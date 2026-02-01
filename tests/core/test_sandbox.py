import pytest
from pathlib import Path
from src.core.sandbox import SandboxValidator, FORBIDDEN_PATTERNS

class TestSandboxValidator:
    @pytest.fixture
    def validator(self, tmp_path):
        return SandboxValidator(project_root=tmp_path)

    def test_init_resolves_project_root(self, tmp_path):
        validator = SandboxValidator(project_root=str(tmp_path) + "/./")
        assert validator.project_root == tmp_path.resolve()

    def test_resolve_path_absolute_inside(self, validator, tmp_path):
        target = tmp_path / "safe_file.txt"
        resolved = validator.resolve_path(target)
        assert resolved == target.resolve()

    def test_resolve_path_relative(self, validator, tmp_path):
        resolved = validator.resolve_path("safe_file.txt")
        assert resolved == (tmp_path / "safe_file.txt").resolve()

    def test_resolve_path_traversal(self, validator, tmp_path):
        # ../ traversal should be resolved
        target = tmp_path / "subdir" / ".." / "file.txt"
        resolved = validator.resolve_path(target)
        assert resolved == (tmp_path / "file.txt").resolve()

    def test_validate_path_safe(self, validator, tmp_path):
        assert validator.validate_path("safe_file.txt") is True
        assert validator.validate_path(tmp_path / "subdir/file.txt") is True

    def test_validate_path_outside_root(self, validator, tmp_path):
        # Parent directory
        outside = tmp_path.parent / "hacking.txt"
        assert validator.validate_path(outside) is False

        # /etc/passwd style
        assert validator.validate_path("/etc/passwd") is False

    def test_validate_path_forbidden_patterns(self, validator):
        # Check all forbidden patterns
        for pattern in FORBIDDEN_PATTERNS:
            if pattern.endswith("/"):
                # Directory pattern
                name = pattern.rstrip("/")
                assert validator.validate_path(f"{name}/secret.txt") is False
            elif pattern.endswith("*"):
                # Wildcard extension
                ext = pattern.replace("*", "test")
                assert validator.validate_path(f"file{ext}") is False
            else:
                # Exact match
                assert validator.validate_path(pattern) is False

    def test_validate_path_git_exception(self, validator):
        # .git/ is forbidden but .gitignore is allowed
        assert validator.validate_path(".git/config") is False
        assert validator.validate_path(".gitignore") is True

    def test_validate_path_symlink_attack(self, validator, tmp_path):
        # Setup a symlink pointing outside
        # Note: This test requires OS support for symlinks
        outside_target = tmp_path.parent / "target_outside.txt"
        outside_target.touch()
        
        symlink = tmp_path / "link_to_outside"
        try:
            symlink.symlink_to(outside_target)
        except OSError:
            pytest.skip("Symlinks not supported or insufficient privileges")

        # resolved path will be outside, so should return False
        assert validator.validate_path(symlink) is False
        
        # cleanup
        outside_target.unlink()
