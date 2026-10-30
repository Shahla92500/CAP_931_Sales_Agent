from datetime import datetime, timezone
from enum import Enum
from ipaddress import ip_address
from urllib.parse import urlsplit, urlunsplit
from pydantic import BaseModel


def public_url(value: str) -> str:
    value = value.strip()
    if not value.startswith(('https://', 'http://')):
        value = 'https://' + value
    p = urlsplit(value)
    if p.scheme not in ('https', 'http') or not p.hostname or p.username or p.password:
        raise ValueError('A public HTTP or HTTPS website URL is required.')
    host = p.hostname.lower().rstrip('.')
    if '.' not in host or host.endswith(('.local', '.localhost', '.internal', '.test', '.invalid', '.example')):
        raise ValueError('Local, reserved, and example domains are not accepted in live mode.')
    try:
        ip_address(host)
    except ValueError:
        pass
    else:
        raise ValueError('Use a public domain name rather than an IP address.')
    if p.port and p.port not in (80, 443):
        raise ValueError('Use a standard web port.')
    if len(value) > 1000:
        raise ValueError('URL is too long.')
    return urlunsplit((p.scheme, p.netloc, p.path or '/', p.query, ''))


class SalesInputs(BaseModel):
    product_name: str
    company_url: str
    product_category: str
    competitor_urls: list[str]
    value_proposition: str
    target_customer: str

    @property
    def company_id(self):
        return urlsplit(self.company_url).hostname or "unknown"

    def check(self):
        for name in ('product_name', 'company_url', 'product_category', 'value_proposition', 'target_customer'):
            value = getattr(self, name).strip()
            if not value:
                raise ValueError(f'{name.replace("_", " ").capitalize()} is required.')
            if len(value) > 1600:
                raise ValueError('Input fields must be 1600 characters or fewer.')
            setattr(self, name, value)
        self.company_url = public_url(self.company_url)
        if len(self.competitor_urls) > 3:
            raise ValueError('A maximum of three competitor URLs is supported.')
        self.competitor_urls = list(dict.fromkeys(public_url(x) for x in self.competitor_urls if x.strip()))
        if self.company_url in self.competitor_urls:
            raise ValueError('A competitor URL must differ from the prospect URL.')
        return self


class Source(BaseModel):
    id: str
    title: str
    url: str
    retrieved_at: str


class Evidence(BaseModel):
    notes: str
    sources: list[Source]
    response_id: str
    model: str
    retrieved_at: str
    mode: str


class Kind(str, Enum):
    fact = 'fact'
    hypothesis = 'hypothesis'
    unknown = 'unknown'


class Claim(BaseModel):
    text: str
    kind: Kind
    source_ids: list[str]


class Briefing(BaseModel):
    company_name: str
    inferred_category: str
    strategy: list[Claim]
    competitors: list[Claim]
    leadership: list[Claim]
    product_strategy: list[Claim]
    sales_fit: list[Claim]
    meeting_questions: list[str]
    limitations: list[str]


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def validate_briefing(report: Briefing, evidence: Evidence) -> dict:
    valid = {s.id for s in evidence.sources}
    claims = report.strategy + report.competitors + report.leadership + report.product_strategy + report.sales_fit
    if any(not getattr(report, x) for x in ('strategy', 'competitors', 'leadership', 'product_strategy', 'sales_fit', 'meeting_questions', 'limitations')):
        raise ValueError('Every briefing section must contain content or an explicit unknown.')
    for section in ('strategy','competitors','leadership','product_strategy','sales_fit'):
        if len(getattr(report, section)) > 3:
            raise ValueError('A section exceeds the three-item briefing limit.')
    if len(report.meeting_questions) > 3 or len(report.limitations) > 3:
        raise ValueError('Too many questions or limitations for a one-page briefing.')
    for c in claims:
        if not c.text.strip() or len(c.text) > 550:
            raise ValueError('A claim is blank or too long.')
        if not set(c.source_ids) <= valid:
            raise ValueError('The model referenced a source outside the research packet.')
        if c.kind == Kind.fact and not c.source_ids:
            raise ValueError('A factual claim is missing its source reference.')
    count = len(' '.join([report.company_name,report.inferred_category] + [c.text for c in claims] + report.meeting_questions + report.limitations).split())
    if count > 450:
        raise ValueError('The model exceeded the 450-word limit. Regenerate with shorter points.')
    facts = [c for c in claims if c.kind == Kind.fact]
    return {'words': count, 'factual_claims': len(facts),
            'cited_factual_claims': sum(bool(c.source_ids) for c in facts),
            'unknown_items': sum(c.kind == Kind.unknown for c in claims),
            'citation_check': 'Source IDs valid; factual support still needs manual review'}
