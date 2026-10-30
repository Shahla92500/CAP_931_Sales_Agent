# CAP 931 Sales Assistant Agent

A Python and Streamlit prototype that helps sales representatives prepare for meetings with prospective customers.

The application collects product and account information and includes a GPT-powered workflow for researching public sources and producing a one-page sales briefing.

## Project status

- The Streamlit interface runs locally.
- Offline demo mode generates a briefing and PDF without an API key.
- Live research and prompt-comparison workflows are implemented.
- Live GPT execution has not been verified because an OpenAI API key was unavailable.
- The application has not been deployed publicly.

## Installation and launch

Python 3.12 and uv are recommended.

Open a terminal in the project folder containing `pyproject.toml`, then run:

```bash
uv sync
uv run streamlit run src/cap_931/app.py
```

Open the Local URL displayed in the terminal, usually:

http://localhost:8501

## Application inputs

| Input | Purpose |
| --- | --- |
| Product name | Identifies the product being sold |
| Company URL | Identifies the prospective account |
| Product category | Describes the product category for normalization by the model |
| Competitor URLs | Identifies up to three competing vendors or products the prospect might use |
| Value proposition | Describes the seller's proposed benefit |
| Target customer name | Identifies the person being approached |

## Demo mode

Select **Demo — no API key** and click **Generate briefing** with the supplied inputs unchanged.

Demo mode uses a fixed fictional company, executive, competitor, and source packet. It demonstrates the interface, report structure, validation, and PDF export.

It does not perform website research or call an LLM.

## Live research

Select **Live research**, complete the required inputs, and enter an OpenAI API key in the password field.

Alternatively, copy `.env.example` to `.env` and configure:

```env
OPENAI_API_KEY=replace_with_a_local_key
OPENAI_MODEL=gpt-4.1-mini
```

The `.env` file is excluded from Git. API keys must not appear in source code, screenshots, or submitted documents.

The default model is `gpt-4.1-mini`. Live operation requires API access to a model supporting Responses API web search and structured output. API charges and model access depend on the account.

## Research and report workflow

1. Validate the required inputs and website URLs.
2. Research public company pages, competitor mentions, leadership, relevant job postings, and annual filings.
3. Extract cited source URLs and organize the research evidence.
4. Generate a structured briefing using the evidence and sales context.
5. Validate report sections, source references, and length.
6. Export the briefing and supporting evidence.

The research prompts distinguish a competitor mention or integration from evidence that the prospect currently uses that vendor.

## Briefing contents

The one-page PDF includes:

- Company strategy.
- Competitor information.
- Relevant leadership.
- Product and annual report strategy.
- Sales opportunity hypotheses.
- Meeting questions.
- Limitations and supporting source links.

Claims are labeled as facts, hypotheses, or unknowns. Missing information should remain unknown rather than be invented.

Download options include PDF, Markdown, and an evidence JSON file.

## Prompt engineering

The application uses prompt chaining:

- **Research prompt:** gathers business evidence and identifies gaps.
- **Synthesis prompt:** converts that evidence into a concise briefing.

Baseline and improved synthesis prompts are included in `src/cap_931/prompts.py`. The improved version adds instructions about identity verification, evidence dates, competitor relationships, and meeting relevance.

After generating a live briefing, **Run prompt comparison** compares both versions against the same research packet. The experiment log records outputs, metadata, validation results, and failures.

No measured improvement in live model performance is claimed before this experiment is executed.

## Project structure

```text
CAP_931_Sales_Agent/
├── pyproject.toml
├── uv.lock
├── README.md
├── .env.example
├── docs/
├── evidence/
├── tests/
│   └── test_app.py
└── src/
    └── cap_931/
        ├── __init__.py
        ├── app.py
        ├── models.py
        ├── prompts.py
        ├── service.py
        ├── export.py
        └── demo.py
```

## Testing

Run the automated tests from the project root:

```bash
uv run --with pypdf python -m unittest discover -s tests -v
```

Tests cover input validation, citation checks, PDF generation, mocked API integration, and Streamlit interaction.

Mocked API tests verify application behavior without making paid requests. They do not demonstrate successful live API execution. Tests must be rerun after changes to the package structure.

## Documentation and examples

- `docs/CAP_931_Technical_Report.docx`: architecture, implementation decisions, testing, limitations, and proposed enhancements.
- `docs/Prompts.md`: prompt versions and evaluation approach.
- `docs/Sample_Briefing.pdf`: fictional offline demonstration.
- `docs/Reference_Shopify_Briefing.pdf`: separately authored reference brief using public sources.
- `evidence/`: available test logs and research packets.

The Shopify reference brief was not generated through the application's live API workflow.

## Limitations and future improvements

Website coverage may be incomplete because of blocked pages, paywalls, search limitations, or recent changes. Valid source references do not prove that every claim is supported; source review remains necessary.

Proposed enhancements include document uploads, scheduled research alerts, authentication, and production deployment. These features are not currently implemented.

## References

- [OpenAI web search](https://developers.openai.com/api/docs/guides/tools-web-search)
- [OpenAI structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
- [Streamlit application testing](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest)
- [Streamlit downloads](https://docs.streamlit.io/develop/api-reference/widgets/st.download_button)