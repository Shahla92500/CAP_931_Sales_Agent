from io import BytesIO
from pathlib import Path
import reportlab
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from html import escape
from xml.sax.saxutils import escape as xml_escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus.doctemplate import LayoutError

SECTIONS=[('strategy','Company strategy'),('competitors','Competitor information'),
          ('leadership','Leadership'),('product_strategy','Product and annual report strategy'),('sales_fit','Sales opportunity hypotheses')]


def markdown(report,evidence,inputs,meta):
    mode={'demo':'FICTIONAL OFFLINE DEMO','reference':'ASSISTANT AUTHORED REFERENCE SAMPLE - separate from app API'}.get(meta['mode'],'LIVE RESEARCH')
    lines=[f'# {report.company_name} | Sales meeting briefing',f'**{mode}** · {meta["generated_at"]}',
           f'Product: {inputs.product_name} | Category: {report.inferred_category} | Target: {inputs.target_customer}']
    for key,title in SECTIONS:
        lines+=['',f'## {title}']
        for c in getattr(report,key):
            refs=' '.join(f'[{x}]' for x in c.source_ids)
            lines.append(f'- **{c.kind.value.capitalize()}**: {c.text} {refs}')
    lines+=['','## Meeting questions']+[f'- {x}' for x in report.meeting_questions]
    lines+=['','## Limitations']+[f'- {x}' for x in report.limitations]
    used={x for k,_ in SECTIONS for c in getattr(report,k) for x in c.source_ids}
    lines+=['','## Supporting sources']+[f'- [{s.id}] [{s.title}]({s.url}) · accessed {s.retrieved_at}' for s in evidence.sources if s.id in used]
    return '\n'.join(lines)


class SinglePageCanvas(Canvas):
    def showPage(self):
        if self.getPageNumber()>1:
            raise LayoutError('Briefing exceeds one page.')
        super().showPage()


def pdf_bytes(report,evidence,inputs,meta):
    # Try readable sizes; reject overflow rather than silently cut text.
    fonts=Path(reportlab.__file__).parent / 'fonts'
    if 'Vera' not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont('Vera',str(fonts / 'Vera.ttf')))
        pdfmetrics.registerFont(TTFont('Vera-Bold',str(fonts / 'VeraBd.ttf')))
    used={x for k,_ in SECTIONS for c in getattr(report,k) for x in c.source_ids}
    for size in (10,9.5,9):
        buffer=BytesIO();styles=getSampleStyleSheet()
        body=ParagraphStyle('Body',fontName='Vera',fontSize=size,leading=size*1.22,spaceAfter=3)
        head=ParagraphStyle('Head',parent=body,fontName='Vera-Bold',spaceBefore=6,spaceAfter=3)
        title=ParagraphStyle('BriefingTitle',parent=head,fontSize=16,leading=19)
        source=ParagraphStyle('Source',parent=body,fontSize=7.5,leading=9)
        flow=[Paragraph(xml_escape(report.company_name+' | Sales meeting briefing'),title)]
        mode={'demo':'FICTIONAL OFFLINE DEMO - no LLM or web research','reference':'REFERENCE SAMPLE - assistant authored; app API not executed'}.get(meta['mode'],'LIVE RESEARCH')
        flow+=[Paragraph(xml_escape(mode+' | '+meta['generated_at']),source),
               Paragraph(xml_escape('Product: '+inputs.product_name+' | '+report.inferred_category+' | Target: '+inputs.target_customer),body)]
        for key,label in SECTIONS:
            flow.append(Paragraph(label,head))
            for c in getattr(report,key):
                refs=' '.join('['+x+']' for x in c.source_ids)
                flow.append(Paragraph(xml_escape(c.kind.value.capitalize()+': '+c.text+' '+refs),body))
        for label,items in [('Meeting questions',report.meeting_questions),('Limitations',report.limitations)]:
            flow.append(Paragraph(label,head))
            flow.extend(Paragraph(xml_escape(str(i)+'. '+v),body) for i,v in enumerate(items,1))
        flow.append(Paragraph('Supporting sources',head))
        for s in evidence.sources:
            if s.id in used:
                flow.append(Paragraph(f'[{xml_escape(s.id)}] <link href="{escape(s.url,quote=True)}" color="#174f8a">{xml_escape(s.title)}</link> | {xml_escape(s.url)}',source))
        doc=SimpleDocTemplate(buffer,pagesize=letter,leftMargin=38,rightMargin=38,topMargin=30,bottomMargin=30)
        try:
            doc.build(flow,canvasmaker=SinglePageCanvas)
            return buffer.getvalue()
        except LayoutError:
            pass
    raise ValueError('Briefing and source links do not fit one page. Generate a shorter report.')
