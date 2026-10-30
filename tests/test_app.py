import json
import unittest
from pathlib import Path
from unittest.mock import Mock
from streamlit.testing.v1 import AppTest
from cap_931.models import public_url, validate_briefing, Kind
from cap_931.demo import demo_inputs, demo_evidence, demo_briefing
from cap_931.service import research, synthesize
from cap_931.export import pdf_bytes

class SalesAgentTests(unittest.TestCase):
    def setUp(self):
        self.inputs=demo_inputs();self.evidence=demo_evidence();self.report,self.meta=demo_briefing(self.inputs,self.evidence)

    def test_demo_pdf(self):
        from pypdf import PdfReader
        from io import BytesIO
        pdf=pdf_bytes(self.report,self.evidence,self.inputs,self.meta)
        reader=PdfReader(BytesIO(pdf))
        self.assertEqual(len(reader.pages),1)
        self.assertIn('FICTIONAL OFFLINE DEMO',reader.pages[0].extract_text())

    def test_url_validation(self):
        for url in ['file:///etc/passwd','http://localhost','http://127.0.0.1','http://169.254.169.254','https://abc.local','https://user:pass@site.com','https://company.example']:
            with self.subTest(url=url):
                with self.assertRaises(ValueError):public_url(url)
        self.assertEqual(public_url('example.com'),'https://example.com/')

    def test_missing_fact_citation_rejected(self):
        self.report.strategy[0].source_ids=[]
        with self.assertRaises(ValueError):validate_briefing(self.report,self.evidence)

    def test_unknown_source_rejected(self):
        self.report.leadership[0].source_ids=['S999']
        with self.assertRaises(ValueError):validate_briefing(self.report,self.evidence)

    def test_long_report_rejected(self):
        self.report.limitations=['word '*500]
        with self.assertRaises(ValueError):validate_briefing(self.report,self.evidence)

    def test_research_api_contract(self):
        client=Mock();result=Mock()
        result.status='completed';result.id='mock-research';result.output_text='A sourced company note.'
        result.model_dump.return_value={'output':[{'type':'web_search_call'}, {'type':'message','content':[{'annotations':[{'type':'url_citation','url':'https://example.com/about','title':'About'}]}]}]}
        client.responses.create.return_value=result
        evidence=research(self.inputs,'unused','gpt-4.1-mini',client)
        self.assertEqual(evidence.sources[0].id,'S1')
        self.assertEqual(client.responses.create.call_args.kwargs['tool_choice'],'required')
        self.assertFalse(client.responses.create.call_args.kwargs['store'])

    def test_no_search_rejected(self):
        client=Mock();result=Mock();result.status='completed';result.model_dump.return_value={'output':[]}
        client.responses.create.return_value=result
        with self.assertRaises(ValueError):research(self.inputs,'unused','test-model',client)

    def test_synthesis_api_contract(self):
        client=Mock();result=Mock(status='completed',id='mock-synthesis',output_parsed=self.report)
        client.responses.parse.return_value=result
        b,meta=synthesize(self.inputs,self.evidence,'unused','test-model',client=client)
        self.assertEqual(meta['response_id'],'mock-synthesis')
        self.assertEqual(meta['cited_factual_claims'],3)

    def test_form_demo_and_output(self):
        at=AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'src' / 'cap_931' / 'app.py'),default_timeout=25).run()
        self.assertFalse(at.exception)
        self.assertEqual(len(at.text_input),6)  # 4 form fields plus model and key
        at.button[0].click().run()
        self.assertFalse(at.exception)
        self.assertTrue(any('Northstar Systems' in m.value for m in at.markdown))
        self.assertIn('result',at.session_state)

    def test_live_empty_inputs_error(self):
        at=AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'src' / 'cap_931' / 'app.py'),default_timeout=25).run()
        at.radio[0].set_value('Live research').run()
        at.button[0].click().run()
        self.assertTrue(at.error)
        self.assertFalse(at.exception)

if __name__=='__main__':unittest.main(verbosity=2)
