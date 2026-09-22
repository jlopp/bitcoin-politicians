# Automated updates

The pipeline downloads congressional financial disclosures, extracts asset names from document images with a multimodal model through OpenRouter, identifies crypto-related holdings, and regenerates the datasets and root `README.md`.

Run commands from the repository root. The CLI returns a nonzero exit code when a stage fails, so these instructions can be followed by a human or a coding agent such as Claude Code or Codex.

## Setup

Use Python 3.11 or newer in a virtual environment:

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -r automated_updates/requirements.txt
```

Create `automated_updates/.env` with:

```dotenv
CONGRESS_GOV_API_KEY='...'
CHROME_DRIVER_PATH='/path/to/chromedriver'
OPENROUTER_API_KEY='...'
OPENROUTER_MODEL='qwen/qwen3-vl-235b-a22b-instruct'
```

Get a [Congress.gov API key](https://api.congress.gov/sign-up/), an [OpenRouter API key](https://openrouter.ai/settings/keys), and a ChromeDriver build matching the installed Chrome version from [Chrome for Testing](https://googlechromelabs.github.io/chrome-for-testing/). `OPENROUTER_MODEL` is optional; the value above is the default.

Keep `.env` and all credentials untracked. An agent should ask the user to populate the file and can run the CLI without reading or printing it.

## CLI

For a routine update, process only newly gathered disclosures:

```sh
./bitcoin-politicians update --new-only --workers 8
```

Omit `--new-only` to rebuild extraction output for every disclosure:

```sh
./bitcoin-politicians update --workers 8
```

Stages can also be run independently:

```sh
./bitcoin-politicians gather
./bitcoin-politicians extract --new-only --workers 8
./bitcoin-politicians summarize
```

- `gather` downloads House and Senate disclosures, refreshes Congress membership data, and prepares document images. Use `gather --test-set` only for a small pipeline check.
- `extract` sends prepared images to OpenRouter. `--workers N` controls concurrency, and completed outputs are skipped when a run is resumed.
- `summarize` rebuilds the final CSV and Markdown datasets and updates the table in the root `README.md` without gathering or extraction.
- `update` runs all three stages in order and stops at the first failure.

If a run is interrupted, rerun the failed stage. Use `./bitcoin-politicians COMMAND --help` for command-specific options.

## Agent workflow

1. Create a branch from `upstream/master` and complete the setup above.
2. Run the routine update command. Monitor long extraction runs and resume the failed stage if needed.
3. Review `git diff`, especially holder matches, disclosure links, filing years, Congress status, generated datasets, and the root `README.md`.
4. Confirm secrets, caches, virtual environments, and ignored intermediate files are not included.
5. Commit the reviewed refresh and prepare the pull request.

The committed source and final-data directories let most users inspect the results without running the pipeline themselves. The pipeline reads disclosures from the official [House](https://disclosures-clerk.house.gov/) and [Senate](https://efdsearch.senate.gov/) sites. Crypto classification terms and exclusions are maintained in `config.py`.
