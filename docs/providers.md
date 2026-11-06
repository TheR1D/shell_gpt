# Providers

`sgpt setup` stores named provider profiles in `~/.config/shell_gpt/providers.json`
(`%USERPROFILE%\.config\shell_gpt\providers.json` on Windows). A profile holds a base URL, a model and
the *name* of the environment variable that holds the key — never the key itself.

## Built-in presets

| preset | base URL | default model | key variable |
|---|---|---|---|
| openai | `https://api.openai.com/v1` | `gpt-6-luna` | `OPENAI_API_KEY` |
| anthropic | `https://api.anthropic.com/v1/` | `claude-sonnet-5-5` | `ANTHROPIC_API_KEY` |
| gemini | `https://generativelanguage.googleapis.com/v1beta/openai/` | `gemini-3.8-flash` | `GEMINI_API_KEY` |
| deepseek | `https://api.deepseek.com` | `deepseek-flash` | `DEEPSEEK_API_KEY` |
| openrouter | `https://openrouter.ai/api/v1` | `anthropic/claude-sonnet-5.5` | `OPENROUTER_API_KEY` |
| groq | `https://api.groq.com/openai/v1` | `openai/gpt-oss-120b` | `GROQ_API_KEY` |
| mistral | `https://api.mistral.ai/v1` | `mistral-large-4` | `MISTRAL_API_KEY` |
| ollama | `http://localhost:11434/v1` | `qwen3:8b` | *(none)* |

The wizard uses these values as editable defaults, so any OpenAI-compatible endpoint works — choose
`custom` and type the base URL.

## Commands

```
sgpt setup                 wizard: preset -> base URL -> model -> profile name -> key variable -> test
sgpt --setup               same wizard (alias)
sgpt setup list            profiles, key presence, which one is active
sgpt setup use <name>      activate a profile
sgpt setup test [name]     one-token request with a 15 s timeout; reports latency or the reason
sgpt setup remove <name>   delete a profile (active falls back to another, or to none)
```

`sgpt setup` needs a real terminal. In scripts and CI use `list`, `use` and `test`.

## Precedence

1. `--provider <name>` on the command line
2. `SGPT_PROVIDER` environment variable
3. the active profile in `providers.json`
4. a saved `API_BASE_URL` that is not `default`
5. the legacy `.sgptrc` values (`DEFAULT_MODEL`, `OPENAI_API_KEY`)

Setting `API_BASE_URL` explicitly beats a profile's base URL — an env var you typed by hand outranks
saved configuration.

## Keys

```shell
export DEEPSEEK_API_KEY=sk-...          # macOS / Linux
setx DEEPSEEK_API_KEY "sk-..."          # Windows, new shell afterwards
```

If a key variable is missing, `sgpt setup test` says so by name, and a normal run fails with
`Missing API key: set <VAR>` rather than a stack trace.

## Ollama and other local servers

Choose the `ollama` preset (no key required, a placeholder is sent) or `custom` with your own base URL.
`USE_LITELLM=true` in `.sgptrc` still works for providers that need litellm's translation layer; in
that mode `--provider` does not apply.

## Troubleshooting

- **`key rejected (401)`** — the variable exists but the value is wrong or revoked.
- **`cannot reach ...`** — base URL or network; check the URL ends with the API root, not `/chat/completions`.
- **`HTTP 404`** — usually a wrong base URL or a model name the provider does not serve.
- **`No interactive terminal`** — `sgpt setup` was called from a script; use `use` / `test`.

> Model names are the fast-moving part of every provider. They were verified against vendor docs on
> 2026-11-05; when one is retired, `sgpt setup` lets you type a new one and nothing else in the profile
> needs to change. Presets only supply defaults.
