"""Keep Vercel's uv project installation in sync with local pip installs."""
from pathlib import Path
import tomllib
from packaging.requirements import Requirement


BACKEND = Path(__file__).resolve().parents[1]


def test_deploy_pyproject_runtime_dependencies_match_requirements_txt():
    metadata = tomllib.loads((BACKEND / 'pyproject.toml').read_text(encoding='utf-8'))
    text = (BACKEND / 'requirements.txt').read_text(encoding='utf-8')
    pip_requirements = [line.strip() for line in text.splitlines()
                        if line.strip() and not line.lstrip().startswith('#')]
    runtime = {Requirement(line).name.lower(): str(Requirement(line).specifier)
               for line in pip_requirements if not line.startswith(('pytest>', 'pytest-', 'pytest=='))}
    project = {Requirement(line).name.lower(): str(Requirement(line).specifier)
               for line in metadata['project']['dependencies']}
    assert project == runtime
    assert metadata['tool']['vercel']['entrypoint'] == 'main:app'
    assert metadata['project']['requires-python'] == '>=3.12,<3.15'


def test_deploy_runtime_has_health_and_auth_security_modules():
    # This catches missing dependencies locally; Vercel's build still needs
    # a real hosted health check and log inspection before release acceptance.
    from app.main import app
    paths = {route.path for route in app.routes}
    assert '/api/v1/health' in paths
    assert '/api/v1/ready' in paths
    assert '/api/v1/auth/login' in paths
