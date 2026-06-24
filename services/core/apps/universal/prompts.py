UNIVERSAL_PROMPT = """You are an expert technical documentation generator. Given the source code and project metadata below, produce COMPREHENSIVE, DETAILED documentation.

First, analyze the code to determine:
1. All languages and frameworks used
2. Whether this is **frontend-only**, **backend-only**, or **full-stack** (CHECK file names for frontend indicators like .jsx, .tsx, components/, pages/, .vue, .svelte, .css, .scss; check for backend indicators like views.py, controllers, API routes, models)
3. Key architectural patterns and design decisions

Then generate documentation with the sections below. Be THOROUGH and SPECIFIC — use real code details, not placeholders.

---

## SECTION RULES (read carefully)

**If the project is FRONTEND-ONLY:**
- Output ONLY these sections: Detected, Project Overview, Project Structure (with mermaid), Components/Modules, Getting Started.
- Skip API/Endpoints, Data/State Management, Configuration, Error Handling & Logging, Deployment entirely — do not even mention them.
- The goal is a clean README-style overview, not exhaustive infra docs.

**If the project is BACKEND or FULL-STACK:**
- Output ALL sections listed below.
- For the API section, include concrete examples: curl commands, example request bodies (JSON), and example response bodies for EVERY endpoint.
- Be exhaustive — document every route, model, and config detail.

---

## Detected
- Language: [detected language(s)]
- Framework: [detected framework(s)]
- Type: Frontend-only / Backend-only / Full-stack
- File count: [approximate number of meaningful source files]

## Project Overview
- Language, framework, purpose (3-4 paragraphs)
- Architecture summary: monolith, microservices, serverless, etc.
- Key design patterns observed (MVC, REST, event-driven, etc.)
- Major dependencies and what each is used for

## Project Structure
Here is the actual file tree of the project:
```
{file_tree}
```
For each key directory, explain its purpose. If the tree is very large, group related directories and summarize.

Include a mermaid flowchart diagram showing the project architecture and workflow:
```mermaid
flowchart TD
    [Create a detailed diagram showing how components interact, data flow, request lifecycle, etc.]
```

## Components / Modules
For each major component/module/app found in the code:
- **Purpose**: What it does
- **Key files**: Important files in this component
- **Inputs/Outputs**: What data it receives and produces
- **Dependencies**: What other components it relies on
- **Error handling**: How errors are handled in this component
- **Testing**: Testing strategy if tests are found

## API / Endpoints (backend or full-stack only)
For EVERY endpoint found, provide a detailed table:

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | /api/example/ | Token | Lists resources |

Then for each endpoint, document:
- **Request Headers**: What headers are required
- **Path Parameters**: Variables in the URL path
- **Query Parameters**: Filtering, pagination, sorting
- **Request Body**: JSON schema of the request payload
- **Response**: JSON schema of the response
- **Status Codes**: What each status code means for this endpoint
- **Example request**:
  ```bash
  curl -X GET https://api.example.com/api/example/ \
    -H "Authorization: Bearer <token>"
  ```
- **Example response**:
  ```json
  {
    "id": 1,
    "name": "example"
  }
  ```

If the code has frontend API calls, list which endpoints the frontend consumes.

## Data / State Management
- Database models / tables with their fields, types, and relationships
- State management approach (Redux, Context, Vuex, etc.)
- Data flow diagrams (how data moves through the system)
- Caching strategy if present
- Migrations and seed data

## Configuration
- Build tools and configuration files
- Environment variables and their purpose
- Development, staging, and production configuration differences
- How to configure the project for local development

## Error Handling & Logging
- Error handling patterns (try/catch, middleware, exception handlers)
- Logging setup (log levels, log files, external services)
- Common errors and how they are handled
- Monitoring and alerting if present

## Deployment
- Deployment configuration (Docker, docker-compose, CI/CD)
- Infrastructure requirements
- How to build and run in production
- Database migration strategy

## Getting Started
- **Clone the repository**:
  ```
  git clone {github_url}
  cd {repo_dir}
  ```
- **Install dependencies**:
  Use the correct package manager for this project. Detected requirements files: {req_files}. Provide the exact install commands.
- **Environment setup**: Configuration steps, .env setup
- **Database setup**: Migration commands
- **Run the project**: Exact commands to start the project
- **Run tests**: How to execute tests

Rules:
- Output ONLY valid markdown. No preamble or wrapper text.
- Use actual code details from the provided source. Do NOT hallucinate.
- Use code blocks with language-specific syntax highlighting.
- If the code contains frontend AND backend code, document BOTH thoroughly.
- For mermaid diagrams, ALWAYS start with 'flowchart TD' on its own line. Use 'A --> B' or 'A -->|label| B' syntax only.
- For API tables, use proper markdown table syntax with | pipes.
- If a section has no content to document, output "Not applicable or not detected in the provided code." instead of making things up.
- Be specific about file paths, function names, class names, and variable names found in the code.
- **For EVERY API endpoint in backend/full-stack projects, include a curl example and a JSON response example.**

Quality validation (review your own output before finalizing):
1. **No invented directory names**: In `cd` and path commands, use only names that exist in the provided file tree `{file_tree}`.
2. **No typos in commands**: Every `git clone`, `cd`, `npm install`, `pip install`, or similar command must be syntactically correct. Verify directory names against the file tree.
3. **No invented file paths**: Any file path referenced in the docs (e.g., `src/components/Foo.jsx`) must actually appear in the file tree or file list.
4. **Accuracy over length**: A short correct answer is better than a long invented one. If unsure about a detail, say "not detected" rather than guessing.
5. **`cd` directory rule**: The `cd` directory after `git clone` MUST be `{repo_dir}`. Never use any other name. This is the exact directory created by the clone.
6. **Frontend-only projects**: Must NOT contain API, Data/State Management, Configuration, Error Handling & Logging, or Deployment sections.
7. **Backend/full-stack projects**: Every API endpoint MUST have a curl example and example JSON response."""

MAX_SOURCE_CHARS = 25_000


def get_prompt(mode, source_code, project_name, file_list=None, max_chars=None,
               github_url='', file_tree='', req_files=None):
    safe_source = source_code.replace("```", "\u200b`\u200b`\u200b`\u200b")
    limit = max_chars if max_chars is not None else MAX_SOURCE_CHARS
    if len(safe_source) > limit:
        safe_source = safe_source[:limit] + "\n\n... [truncated]"

    prefix = f"""Project: {project_name}
Source code to document:
```
{safe_source}
```
"""

    file_list_text = ""
    if file_list:
        file_list_text = "\n".join(f"  - {f}" for f in file_list)
        file_list_text = f"\n\nAll files in project:\n{file_list_text}"

    meta_lines = [
        "## Metadata",
        f"- Project name: {project_name}",
        f"- GitHub URL: {github_url}",
    ]
    if req_files:
        meta_lines.append(f"- Detected requirements files: {', '.join(req_files)}")
    meta_lines.append("")

    repo_dir = ''
    if github_url:
        repo_dir = github_url.rstrip('/').split('/')[-1].replace('.git', '')
    if not repo_dir:
        repo_dir = project_name

    prompt_kwargs = {
        'project_name': project_name,
        'github_url': github_url,
        'repo_dir': repo_dir,
        'file_tree': file_tree,
        'req_files': ', '.join(req_files) if req_files else 'None detected',
    }

    prompt_body = UNIVERSAL_PROMPT
    for k, v in prompt_kwargs.items():
        prompt_body = prompt_body.replace(f'{{{k}}}', str(v))

    return prefix + file_list_text + "\n\n" + "\n".join(meta_lines) + prompt_body
