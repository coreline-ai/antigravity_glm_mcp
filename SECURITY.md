# Security Policy

## Overview

Antigravity GLM MCP server implements a 4-layer security architecture to ensure safe collaboration between Gemini and the GLM-4.5 model.

## Security Layers

### 1. Sandbox (Path Validation)
- All file operations are restricted to the `PROJECT_ROOT` directory.
- Path traversal attacks are blocked by strict path resolving and validation.
- Unauthorized access to system files or sensitive directories (e.g., `~/.ssh`) is prohibited.

### 2. Network Security (SSRF Prevention)
- All HTTP requests are filtered to prevent SSRF (Server-Side Request Forgery).
- Internal IP addresses (10.x.x.x, 172.16.x.x, 192.168.x.x, 127.0.0.1) are blocked.
- DNS Rebinding defense is implemented by resolving hostnames before validation.

### 3. Execution Security (RCE Protection)
- `glm_code_run` executes Python code in a restricted environment.
- Sensitive environment variables (e.g., `ZHIPU_API_KEY`, `CLOUD_CREDENTIALS`) are filtered out during execution to prevent information leakage.
- `glm_shell_exec` uses a strict whitelist of allowed commands. Dangerous commands like `rm -rf`, `sudo`, `chmod`, and pipe redirections are blocked.

### 4. Data Protection
- **Automatic Backups**: Files are automatically backed up before any edit or delete operation, allowing for easy rollback.
- **API Key Isolation**: Actual API keys are never committed to the repository. We provide `.env.sample` and rely on environment variables or local MCP configuration files.

## Reporting a Vulnerability

If you discover a security vulnerability, please do NOT open a public issue. Instead, report it to our security team at [security@coreline.ai](mailto:security@coreline.ai). We will acknowledge your report within 48 hours and provide a fix as soon as possible.
