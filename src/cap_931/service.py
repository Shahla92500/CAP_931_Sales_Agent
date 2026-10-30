import json
from openai import OpenAI
from .models import SalesInputs, Source, Evidence, Briefing, now, validate_briefing, public_url
from .prompts import RESEARCH, BASELINE, IMPROVED


def make_client(key):
    return OpenAI(api_key=key, timeout=120.0, max_retries=1)


def extract_sources(payload, stamp):
    # A cited URL is usable evidence; a merely visited search result is not.
    found = {}
    for item in payload.get('output', []):
        if item.get('type') == 'message':
            for part in item.get('content', []):
                for a in part.get('annotations', []):
                    if a.get('type') == 'url_citation' and a.get('url'):
                        try:
                            url = public_url(a['url'])
                        except ValueError:
                            continue
                        found.setdefault(url, a.get('title') or url)
    return [Source(id=f'S{i}', title=title[:180], url=url, retrieved_at=stamp)
            for i, (url, title) in enumerate(found.items(), 1)]


def research(inputs: SalesInputs, key: str, model: str, client=None) -> Evidence:
    client = client or make_client(key)
    result = client.responses.create(
        model=model, instructions=RESEARCH,
        input=json.dumps(inputs.model_dump()), tools=[{'type': 'web_search'}],
        tool_choice='required', include=['web_search_call.action.sources'],
        max_output_tokens=5000, store=False)
    if result.status != 'completed':
        raise ValueError('Research did not complete. No briefing was generated.')
    payload = result.model_dump(); stamp = now()
    if not any(x.get('type') == 'web_search_call' for x in payload.get('output', [])):
        raise ValueError('No web search was recorded; research cannot be treated as sourced.')
    sources = extract_sources(payload, stamp)
    if not sources or not result.output_text.strip():
        raise ValueError('Research returned no cited public sources. Try more specific company URLs.')
    if len(sources) > 20:
        raise ValueError('Research returned too many sources; narrow the company research.')
    return Evidence(notes=result.output_text, sources=sources, response_id=result.id,
                    model=model, retrieved_at=stamp, mode='live')


def synthesize(inputs: SalesInputs, evidence: Evidence, key: str, model: str,
               version='improved', client=None):
    client = client or make_client(key)
    prompt = IMPROVED if version == 'improved' else BASELINE
    result = client.responses.parse(
        model=model, instructions=prompt,
        input=json.dumps({'sales_inputs': inputs.model_dump(), 'evidence': evidence.model_dump()}),
        text_format=Briefing, max_output_tokens=3500, store=False)
    if result.status != 'completed' or result.output_parsed is None:
        raise ValueError('Model returned an incomplete response or refusal. No valid briefing is available.')
    report = result.output_parsed
    metrics = validate_briefing(report, evidence)
    return report, {'model': model, 'response_id': result.id, 'prompt_version': version,
                    'generated_at': now(), 'mode': 'live', 'company_id': inputs.company_id, **metrics}
