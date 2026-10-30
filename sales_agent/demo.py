from .models import SalesInputs, Source, Evidence, Briefing, Claim, Kind, now, validate_briefing


def demo_inputs():
    return SalesInputs(product_name='PipelinePilot', company_url='https://northstar.example',
        product_category='Sales workflow software', competitor_urls=['https://harborcrm.example'],
        value_proposition='Reduce manual follow-up and keep sales activity visible in one place.',
        target_customer='Maya Chen')


def demo_evidence():
    stamp=now()
    return Evidence(notes='FICTIONAL TEST FIXTURE. S1: Northstar Systems sells inventory software to regional retailers and describes expansion through channel partners. S2: Its leadership page lists Maya Chen as CEO. S3: HarborCRM advertises automated sales follow-up. There is no evidence that Northstar uses HarborCRM. Northstar is fictional and no annual filing exists. No independent evidence, sales budget, CRM, headcount, pricing comparison or buying intent is supplied.',
        sources=[Source(id='S1',title='Fictional Northstar company profile',url='https://northstar.example/about',retrieved_at=stamp),
                 Source(id='S2',title='Fictional Northstar leadership',url='https://northstar.example/leadership',retrieved_at=stamp),
                 Source(id='S3',title='Fictional HarborCRM positioning',url='https://harborcrm.example/product',retrieved_at=stamp)],
        response_id='offline-fixture',model='none',retrieved_at=stamp,mode='demo')


def demo_briefing(inputs, evidence):
    def c(t,k,ids): return Claim(text=t,kind=k,source_ids=ids)
    b=Briefing(company_name='Northstar Systems', inferred_category='Sales workflow software',
        strategy=[c('The fictional company describes inventory software for regional retailers and growth through channel partners.',Kind.fact,['S1'])],
        competitors=[c('HarborCRM advertises automated sales follow-up. No supplied evidence establishes that Northstar uses this competing product.',Kind.fact,['S3'])],
        leadership=[c('The fictional leadership fixture lists Maya Chen as CEO. No real executive identity was researched.',Kind.fact,['S2'])],
        product_strategy=[c('No annual report or 10-K exists for this fictional company. The fixture cannot establish a real product roadmap.',Kind.unknown,[])],
        sales_fit=[c(f'{inputs.product_name} may help organize partner follow-up if Northstar confirms that manual coordination is a problem. The value proposition remains a seller claim.',Kind.hypothesis,[])],
        meeting_questions=['How is partner follow-up managed today?', 'Which handoffs cause missed opportunities?', 'What evidence would justify a pilot?'],
        limitations=['Fictional demonstration only. No website research or LLM call occurred.', 'Budget, systems, buying intent and independent validation are unknown.'])
    return b, {'mode':'demo','model':'none','response_id':'offline-fixture',
               'prompt_version':'fixture','generated_at':now(), **validate_briefing(b,evidence)}
