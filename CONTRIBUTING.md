# Contributing

Thank you for your interest in contributing to LinkedIn MCP Server. This guide covers the development workflow, coding standards, and submission process.

---

## Getting Started

### 1. Fork and clone

```bash
git clone https://github.com/<your-username>/linkedin-mcp-server.git
cd linkedin-mcp-server
```

### 2. Install dependencies

This project uses [uv](https://docs.astral.sh/uv/) as its package manager:

```bash
uv sync --group dev
```

### 3. Set up pre-commit hooks

Pre-commit hooks enforce code quality checks (formatting, linting, trailing whitespace, etc.) on every commit:

```bash
uv run pre-commit install
```

### 4. Authenticate with LinkedIn

Required for running the server locally or running integration tests:

```bash
uv run linkedin-mcp-server --login
```

---

## Project Structure

The project follows a hexagonal (ports and adapters) architecture:

```
src/linkedin_mcp_server/
├── domain/         # Core logic — models, parsers, exceptions, value objects
├── ports/          # Abstract interfaces (auth, browser, config)
├── application/    # Use cases — orchestration layer
├── adapters/
│   ├── driven/     # Infrastructure (browser, auth, config implementations)
│   └── driving/    # Interface layer (CLI, MCP tools, serialization)
└── container.py    # Dependency injection composition root
```

### Architecture Rules

- **Domain code has zero external dependencies.** It must never import from `adapters/`.
- **Ports define contracts.** They are abstract classes in `ports/`.
- **Adapters implement ports.** Concrete implementations live in `adapters/`.
- **Use cases depend only on ports**, never on concrete adapters.
- **The Container wires everything.** It is the single place that imports and instantiates concrete adapter classes.

---

## Development Workflow

### Running the server locally

```bash
# stdio (default)
uv run linkedin-mcp-server

# HTTP with debug logging
uv run linkedin-mcp-server --transport streamable-http --port 8000 --log-level DEBUG
```

### Running tests

```bash
# Unit tests
uv run pytest

# With coverage
uv run pytest --cov=linkedin_mcp_server

# Skip integration tests
uv run pytest -m "not integration"
```

### Linting and formatting

This project uses [Ruff](https://docs.astral.sh/ruff/) for both linting and formatting. Pre-commit hooks will run these automatically, but you can also run them manually:

```bash
# Check for issues
uv run ruff check .

# Auto-fix
uv run ruff check . --fix

# Format
uv run ruff format .

# Verify formatting (CI mode)
uv run ruff format --check .
```

---

## How to Contribute

### Reporting Bugs

Open an [issue](https://github.com/eliasbiondo/linkedin-mcp-server/issues) with the following information:

- A clear description of the bug
- Steps to reproduce
- Expected vs. actual behavior
- Environment details (OS, Python version)

### Suggesting Features

Open an [issue](https://github.com/eliasbiondo/linkedin-mcp-server/issues) with:

- A clear description of the feature
- The use case and why it would be valuable
- Any implementation ideas (optional)

### Submitting Pull Requests

1. **Create a branch** from `main`:

   ```bash
   git checkout -b feat/my-feature
   ```

2. **Make your changes**, following the architecture rules above.

3. **Add tests** for new functionality where applicable.

4. **Verify all checks pass**:

   ```bash
   uv run ruff check .
   uv run ruff format --check .
   uv run pytest
   ```

5. **Commit** using a descriptive message following the commit convention below.

6. **Push** and open a pull request against `main`.

---

## Commit Convention

This project follows [Conventional Commits](https://www.conventionalcommits.org/):

| Prefix      | Description                                |
| ----------- | ------------------------------------------ |
| `feat:`     | A new feature                              |
| `fix:`      | A bug fix                                  |
| `docs:`     | Documentation changes                      |
| `refactor:` | Code refactoring with no behavior change   |
| `test:`     | Adding or updating tests                   |
| `chore:`    | Tooling, CI, or dependency updates         |

Examples:

```
feat: add support for scraping volunteer experience
fix: handle rate-limited responses in job search
docs: update configuration reference in README
```

---

## Adding a New Scraping Section

If you want to add a new profile section (e.g., certifications), follow these steps:

1. **Create the data model** in `domain/models/person.py`:

   ```python
   @dataclass
   class CertificationEntry:
       name: str | None = None
       issuer: str | None = None
       date: str | None = None
   ```

2. **Create the parser** in `domain/parsers/person.py`:

   ```python
   def parse_certifications(html: str) -> CertificationsSection:
       ...
   ```

3. **Register the section** in the relevant use case (`application/scrape_person.py`).

4. **Add tests** for the parser.

---

## Code Style Guidelines

- Use type hints consistently throughout the codebase.
- Parsers should be defensive. LinkedIn's HTML structure changes frequently, so use `try/except` blocks and return `None` for missing fields rather than raising exceptions.
- Keep pull requests small and focused on a single feature or fix.
- Use the [MCP Inspector](https://github.com/modelcontextprotocol/inspector) (`npx @modelcontextprotocol/inspector`) to manually test tool changes before submitting.

---

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
