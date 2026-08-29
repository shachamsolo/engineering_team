# Engineering Team

A [CrewAI](https://www.crewai.com) crew that turns a product brief into a working Python app: design, backend, Gradio UI, and unit tests.

Paste a brief in the live UI. Four agents collaborate in sequence, write into a sandboxed `uv` project, and execute code in Docker. You can watch each station as it works.

A full run usually takes several minutes and uses an OpenAI API key.

## Requirements

- Python **3.10–3.13**
- [uv](https://docs.astral.sh/uv/)
- [Docker](https://docs.docker.com/get-docker/) (used to run sandbox code)
- An [OpenAI API key](https://platform.openai.com/api-keys)

## Quick start

```bash
git clone https://github.com/shachamsolo/engineering_team.git
cd engineering_team
```

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) if you do not have it, then:

```bash
uv tool install crewai
crewai install
```

Create a `.env` file in the project root:

```
OPENAI_API_KEY=sk-...
```

Start the UI:

```bash
crewai run
```

Open the local Gradio URL, paste a product brief (or pick an example), and click **Start build**. The sandbox is wiped at the start of every run.

After a successful build, generated files live in `sandbox/`. To try the app:

```bash
cd sandbox
uv run app.py
```

## How it works

1. **Engineering Lead** — turns the brief into a design (`sandbox/design.md`). Uses [Context7](https://context7.com) for current Gradio API notes.
2. **Backend Engineer** — implements the design in Python (stdlib only).
3. **Frontend Engineer** — writes a Gradio UI in `app.py` and a validation script.
4. **Test Engineer** — writes `unittest` tests, runs them, and fixes backend defects until they pass.

Engineers share one sandbox directory. They use tools to list, read, write, and run files. Python execution happens in an ephemeral Docker container (`ghcr.io/astral-sh/uv:python3.13-bookworm-slim`) with the sandbox mounted as the working directory.

Default models are set in `src/engineering_team/config/agents.yaml` (`openai/gpt-5.5` for the lead, `openai/gpt-5.4-mini` for the others). Change those strings to use different models.

## Project layout

```
engineering_team/
├── src/engineering_team/
│   ├── config/
│   │   ├── agents.yaml      # roles, goals, backstories, models
│   │   └── tasks.yaml       # sequential tasks and outputs
│   ├── tools/
│   │   └── sandbox_tools.py # list / read / write / run in the sandbox
│   ├── ui/                  # Gradio live build floor
│   ├── crew.py              # crew wiring
│   └── main.py              # entry point (`crewai run`)
├── sandbox/                 # generated app (reset on each build)
├── pyproject.toml
└── .env                     # local secrets — do not commit
```

## Customize

| What | Where |
|---|---|
| Agent roles and models | `src/engineering_team/config/agents.yaml` |
| Task prompts and outputs | `src/engineering_team/config/tasks.yaml` |
| Example briefs in the UI | `src/engineering_team/examples.py` |
| Sandbox tools | `src/engineering_team/tools/sandbox_tools.py` |
| Crew wiring | `src/engineering_team/crew.py` |

## License

Use and modify this project as you like. Please keep API keys out of git — `.env` is already ignored.
