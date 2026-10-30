import json
import os
from dotenv import load_dotenv
import streamlit as st
from openai import AuthenticationError, RateLimitError, APIConnectionError, APIStatusError
from cap_931.models import SalesInputs
from cap_931.demo import demo_inputs, demo_evidence, demo_briefing
from cap_931.service import research, synthesize
from cap_931.export import markdown, pdf_bytes
from cap_931.prompts import RESEARCH, BASELINE, IMPROVED

load_dotenv()
st.set_page_config(page_title='Sales meeting brief',page_icon='📋',layout='wide')
st.title('Sales meeting brief')
st.write('Research a prospective company and prepare a source-linked briefing for the next sales conversation.')

with st.sidebar:
    mode=st.radio('Mode',['Demo — no API key','Live research'],key='mode')
    demo=mode.startswith('Demo')
    model=st.text_input('OpenAI model',value=os.getenv('OPENAI_MODEL','gpt-4.1-mini'))
    key=st.text_input('OpenAI API key',type='password',help='Stored only in the running session; excluded from evidence downloads.') or os.getenv('OPENAI_API_KEY','')
    if demo: st.info('Fictional sample. No web research or model call.')
    else: st.caption('Live research uses the OpenAI API and web search. API access and billing may be required.')
    with st.expander('Prompts'):
        st.code(RESEARCH,language=None);st.code(BASELINE,language=None);st.code(IMPROVED,language=None)

preset=demo_inputs()
# Separate widget keys avoid carrying fictional URLs into live mode.
prefix='demo_' if demo else 'live_'
with st.form(prefix+'inputs'):
    left,right=st.columns(2)
    with left:
        product=st.text_input('Product name',value=preset.product_name if demo else '',key=prefix+'product')
        url=st.text_input('Prospective company URL',value=preset.company_url if demo else '',key=prefix+'url')
        category=st.text_input('Product category',value=preset.product_category if demo else '',key=prefix+'category')
    with right:
        competitors=st.text_area('Competitor URLs — one per line',value='\n'.join(preset.competitor_urls) if demo else '',help='Competing vendors/products the prospect might use; maximum three.',key=prefix+'competitors')
        value=st.text_area('Value proposition',value=preset.value_proposition if demo else '',key=prefix+'value')
        target=st.text_input('Target customer name',value=preset.target_customer if demo else '',key=prefix+'target')
    submitted=st.form_submit_button('Generate briefing',type='primary')


def error_message(exc):
    # Do not display provider exception strings: they can include request metadata.
    if isinstance(exc,AuthenticationError):return 'API authentication failed. Check the key and account access.'
    if isinstance(exc,RateLimitError):return 'API quota or rate limit reached. Check billing or retry later.'
    if isinstance(exc,APIConnectionError):return 'The API could not be reached. Check the network and retry.'
    if isinstance(exc,APIStatusError):return 'The API rejected the request. Check model and web-search access.'
    if isinstance(exc,ValueError):return str(exc)
    return 'The briefing could not be completed. Check the inputs and retry.'

if submitted:
    # Invalidate stale results before attempting a new request.
    st.session_state.pop('result',None);st.session_state.pop('experiment',None)
    try:
        inputs=SalesInputs(product_name=product,company_url=url,product_category=category,
            competitor_urls=competitors.splitlines(),value_proposition=value,target_customer=target)
        if not all(x.strip() for x in [product,url,category,value,target]):raise ValueError('Complete all required input fields.')
        if demo:
            # The fictional company fixture is fixed; do not relabel it as researched input.
            if inputs.model_dump()!=preset.model_dump():raise ValueError('Demo uses the fixed fictional inputs. Switch to Live research for another company or product.')
            evidence=demo_evidence();report,meta=demo_briefing(inputs,evidence)
        else:
            inputs.check()
            if not key:raise ValueError('An OpenAI API key is required for live research.')
            with st.spinner('Researching public sources and preparing the briefing…'):
                evidence=research(inputs,key,model)
                report,meta=synthesize(inputs,evidence,key,model)
        pdf=pdf_bytes(report,evidence,inputs,meta)
        st.session_state.result={'inputs':inputs,'evidence':evidence,'report':report,'meta':meta,'pdf':pdf}
    except Exception as exc:
        st.error(error_message(exc))

result=st.session_state.get('result')
if result and ((result['meta']['mode']=='demo')==demo):
    r=result
    st.divider()
    if demo: st.warning('FICTIONAL OFFLINE DEMO — this is a fixed test fixture, not an LLM-generated or researched report.')
    st.markdown(markdown(r['report'],r['evidence'],r['inputs'],r['meta']))
    c1,c2,c3=st.columns(3)
    c1.download_button('Download one-page PDF',r['pdf'],'sales_briefing.pdf','application/pdf')
    c2.download_button('Download Markdown',markdown(r['report'],r['evidence'],r['inputs'],r['meta']),'sales_briefing.md','text/markdown')
    packet={'inputs':r['inputs'].model_dump(),'evidence':r['evidence'].model_dump(),'briefing':r['report'].model_dump(mode='json'),'metadata':r['meta']}
    c3.download_button('Download evidence JSON',json.dumps(packet,indent=2),'sales_evidence.json','application/json')
    with st.expander('Research notes and validation'):
        st.write(r['evidence'].notes);st.json(r['meta'])
        st.caption('Valid source references do not prove that the cited page supports the claim. Review sources before a meeting.')
    st.subheader('Prompt experiment')
    st.caption('Compare baseline and improved prompts on the same research packet. This makes two additional model calls.')
    if st.button('Run prompt comparison',disabled=demo or not key):
        try:
            with st.spinner('Comparing both prompts on the same evidence…'):
                outputs={}
                for version in ['baseline','improved']:
                    try:
                        b,m=synthesize(r['inputs'],r['evidence'],key,model,version)
                        outputs[version]={'briefing':b.model_dump(mode='json'),'metrics':m}
                    except Exception as exc:outputs[version]={'error':error_message(exc)}
                st.session_state.experiment={'research_response_id':r['evidence'].response_id,'outputs':outputs}
        except Exception as exc:st.error(error_message(exc))
    if st.session_state.get('experiment'):
        st.json(st.session_state.experiment)
        st.download_button('Download experiment log',json.dumps(st.session_state.experiment,indent=2),'prompt_experiment.json','application/json')
