"""Authorized local/Drive imports. Extraction produces candidates, never approval."""
import base64, copy, hashlib, io, json, os, re, urllib.request, zipfile
from html.parser import HTMLParser
from pathlib import Path
import xml.etree.ElementTree as ET
import reading_engine as engine

def docx_text(node,ns):
    """Keep explicit line breaks/tabs and paragraph boundaries in table cells."""
    chunks=[]
    def walk(e):
        tag=e.tag.rsplit('}',1)[-1]
        if tag=='t':chunks.append(e.text or '')
        elif tag in ('br','cr'):chunks.append('\n')
        elif tag=='tab':chunks.append('\t')
        else:
            for child in e:walk(child)
            if tag=='p':chunks.append('\n')
    walk(node)
    return ''.join(chunks).rstrip('\n')

class BlocksHTML(HTMLParser):
    def __init__(self):super().__init__();self.blocks=[];self.buf=[];self.row=[];self.rows=[];self.cell=[];self.in_table=False;self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style'):self.skip+=1
        if tag=='table':self.flush();self.in_table=True;self.rows=[]
        if tag=='tr':self.row=[]
        if tag in ('td','th'):self.cell=[]
        if tag=='br':self.handle_data('\n')
        if tag=='img':self.flush();a=dict(attrs);self.blocks.append(dict(type='image',src=a.get('src',''),alt=a.get('alt','')))
    def handle_data(self,data):
        if self.skip:return
        (self.cell if self.in_table else self.buf).append(data)
    def handle_endtag(self,tag):
        if tag in ('script','style'):self.skip=max(0,self.skip-1)
        if tag in ('td','th'):self.row.append(''.join(self.cell).strip())
        if tag=='tr' and self.row:self.rows.append(self.row)
        if tag=='table':self.blocks.append(dict(type='table',rows=self.rows));self.in_table=False
        if tag in ('p','div','li','h1','h2','h3','h4'):self.flush('heading' if tag.startswith('h') else 'paragraph')
    def flush(self,kind='paragraph'):
        text=''.join(self.buf).strip();self.buf=[]
        if text:self.blocks.append(dict(type=kind,text=text))

def extract(raw,name,mime=None):
    suffix=Path(name).suffix.lower();issues=[]
    if suffix=='.json':return dict(structured=json.loads(raw.decode('utf-8-sig')),blocks=[],issues=[])
    if suffix=='.pdf' or mime=='application/pdf':
        from pypdf import PdfReader
        reader=PdfReader(io.BytesIO(raw));blocks=[]
        for i,page in enumerate(reader.pages):
            text=page.extract_text(extraction_mode='layout') or ''
            for j,para in enumerate(re.split(r'\n\s*\n',text)):
                if para.strip():blocks.append(dict(type='paragraph',text=para.strip(),page=i+1))
            if not text.strip():issues.append(f'PAGE_{i+1}_OCR_REQUIRED')
            if page.images:issues.append(f'PAGE_{i+1}_MEDIA_LAYOUT_REVIEW')
        issues.append('PDF_READING_ORDER_TABLES_FORMATTING_REQUIRE_SOURCE_REVIEW')
    elif suffix=='.docx':
        blocks=[];ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            if sum(i.file_size for i in z.infolist())>40_000_000:raise ValueError('DOCX quá lớn sau giải nén.')
            root=ET.fromstring(z.read('word/document.xml'));body=root.find('w:body',ns)
            for node in body:
                if node.tag.endswith('}tbl'):
                    rows=[[docx_text(c,ns) for c in r.findall('w:tc',ns)] for r in node.findall('w:tr',ns)]
                    blocks.append(dict(type='table',rows=rows))
                elif node.tag.endswith('}p'):
                    text=docx_text(node,ns)
                    style=node.find('w:pPr/w:pStyle',ns);kind='heading' if style is not None and 'heading' in str(style.attrib).lower() else 'paragraph'
                    if text:blocks.append(dict(type=kind,text=text))
            for info in z.infolist():
                if info.filename.startswith('word/media/'):
                    kind={'.png':'png','.jpg':'jpeg','.jpeg':'jpeg','.webp':'webp'}.get(Path(info.filename).suffix.lower())
                    if kind:blocks.append(dict(type='image',src=f'data:image/{kind};base64,'+base64.b64encode(z.read(info)).decode(),alt=Path(info.filename).name))
                    else:issues.append('UNSUPPORTED_DOCX_MEDIA')
            if any('drawing' in e.tag for e in root.iter()):issues.append('DOCX_IMAGE_ANCHORS_REQUIRE_REVIEW')
        issues.append('DOCX_INLINE_EMPHASIS_LISTS_REQUIRE_REVIEW')
    elif suffix in ('.html','.htm') or mime=='text/html':
        parser=BlocksHTML();parser.feed(raw.decode('utf-8-sig'));parser.flush();blocks=parser.blocks
        issues.append('HTML_INLINE_EMPHASIS_REQUIRE_REVIEW')
    elif suffix in ('.txt','.md'):
        blocks=[dict(type='heading' if s.startswith('#') else 'paragraph',text=s.strip()) for s in re.split(r'\n\s*\n',raw.decode('utf-8-sig')) if s.strip()]
    else:raise ValueError('Hỗ trợ JSON cấu trúc, PDF text, DOCX, TXT, Markdown, HTML. Scan phải OCR và duyệt ngoài trước.')
    for i,b in enumerate(blocks):b['id']=f'source-b{i+1}'
    return dict(blocks=blocks,issues=issues,text='\n\n'.join(b.get('text','') or '\n'.join(' | '.join(r) for r in b.get('rows',[])) for b in blocks))

def candidate(raw,name,source):
    parsed=extract(raw,name,source.get('mime'));checksum=hashlib.sha256(raw).hexdigest();source=dict(source,name=name,checksum=checksum,reference=source.get('reference',name))
    if parsed.get('structured'):
        doc=parsed['structured'];doc['sourceDocument']=dict(source=source,blocks=[]);return doc
    # Only explicitly delimited questions are detected. Ambiguous layouts stay in the queue.
    text=parsed['text'];pid='passage-1';gid='group-1';questions=[]
    matches=list(re.finditer(r'^\s*(?:Question|Q)\s*(\d+)\s*[.:]\s*([^\n]+)',text,re.M|re.I))
    for i,m in enumerate(matches):
        body=text[m.end():matches[i+1].start() if i+1<len(matches) else len(text)]
        options=[dict(id=f'q{m[1]}-option-{o[1]}',label=o[1],content=o[2].strip()) for o in re.finditer(r'^\s*([A-G])[.)]\s+(.+?)(?=^\s*[A-G][.)]\s+|^\s*Answer:|\Z)',body,re.M|re.S)]
        key=re.search(r'^\s*Answer:\s*(.+)',body,re.M|re.I);value=key[1].strip() if key else ''
        typ='single' if options else 'short';maxwords=re.search(r'(?:NO MORE THAN|MAX)\s+(ONE|TWO|THREE|\d+)\s+WORDS?',body,re.I)
        limits={'ONE':1,'TWO':2,'THREE':3};limit=limits.get(maxwords[1].upper(),int(maxwords[1]) if maxwords and maxwords[1].isdigit() else None) if maxwords else None
        questions.append(dict(id=f'q{m[1]}',number=int(m[1]),type=typ,prompt=m[2].strip(),passageId=pid,groupId=gid,options=options,constraints=dict(maxWords=limit,maxNumbers=0),source=source,key=dict(optionIds=[o['id'] for o in options if o['label']==value],accepted=[value] if value and not options else [],provenance=source['reference'] if key else '',status='UNVERIFIED')))
    passage_blocks=copy.deepcopy(parsed['blocks'])
    if matches:
        # Preserve paragraphs, tables, headings and images in source order.
        # Stop at the first explicitly delimited question, including within a block.
        passage_blocks=[]
        for b in parsed['blocks']:
            fragment=b.get('text','');m=re.search(r'^\s*(?:Question|Q)\s*\d+\s*[.:]',fragment,re.M|re.I)
            if m:
                prefix=fragment[:m.start()].strip()
                if prefix:passage_blocks.append(dict(copy.deepcopy(b),text=prefix))
                break
            passage_blocks.append(copy.deepcopy(b))
    return dict(id='import-'+checksum[:16],title=Path(name).stem,testType='practice',fullTest=False,duration=600,passages=[dict(id=pid,title=Path(name).stem,blocks=passage_blocks)],groups=[dict(id=gid,passageIds=[pid],instructions='Đối chiếu hướng dẫn nguồn trước khi xuất bản.')],questions=questions,sourceDocument=dict(source=source,blocks=parsed['blocks'],warnings=parsed['issues']))

def drive_download(file_id):
    if not re.fullmatch(r'[\w-]{10,150}',str(file_id)):raise ValueError('File ID Drive không hợp lệ.')
    token=os.environ.get('OCEAN_DRIVE_ACCESS_TOKEN')
    if not token:raise ValueError('Chưa có quyền Drive ở backend. Có thể export tệp rồi nhập bản local; không thay đổi chia sẻ.')
    def request(url):
        req=urllib.request.Request(url,headers={'Authorization':'Bearer '+token})
        with urllib.request.urlopen(req,timeout=30) as response:
            raw=response.read(20_000_001)
            if len(raw)>20_000_000:raise ValueError('Tệp vượt giới hạn 20 MB.')
            return raw
    root='https://www.googleapis.com/drive/v3/files/'+file_id
    meta=json.loads(request(root+'?fields=id,name,mimeType,modifiedTime,version,capabilities(canDownload)'))
    if not meta.get('capabilities',{}).get('canDownload'):raise ValueError('Tài khoản không có quyền tải/export tệp này.')
    mime=meta['mimeType'];name=meta['name']
    if mime=='application/vnd.google-apps.document':raw=request(root+'/export?mimeType=text%2Fhtml');name+='.html';mime='text/html'
    elif mime.startswith('application/vnd.google-apps.'):raise ValueError('Chỉ Google Docs native được hỗ trợ export; loại tệp khác cần export thủ công.')
    else:raw=request(root+'?alt=media')
    return raw,name,dict(reference='drive:'+file_id,id=file_id,mime=mime,revision=meta.get('version'),modifiedTime=meta.get('modifiedTime'))

def migrate(store,data,questions):
    """Preserve all legacy sources and attempts; quarantine rather than guess corrections."""
    for t in data['tests']:
        if any(x['id']==t['id'] for x in store.list(admin=True)):continue
        source=dict(reference=t['paper'],answerReference=t['answer'],origin='legacy-local-archive')
        blocks=[];warnings=[]
        path=Path(data['resources'][t['paper']]['path'])
        if path.is_file():
            parsed=extract(path.read_bytes(),path.name);blocks=parsed['blocks'];warnings=parsed['issues']
        else:warnings=['SOURCE_MISSING']
        # Actual passage bounds from printed READING PASSAGE headings. Do not invent bounds.
        passages=[]
        for b in blocks:
            match=re.search(r'READING PASSAGE\s+([123])',b.get('text',''),re.I)
            if match:passages.append(dict(id='p'+match[1],title='Reading Passage '+match[1],blocks=[]))
            if passages:passages[-1]['blocks'].append(b)
        if not passages:passages=[dict(id='unresolved-passage',title='Nguồn chưa phân tách',blocks=blocks)]
        pids={p['id'] for p in passages};groups={};qs=[]
        mapping={'mcq':'single','matching':'matching_information','gap':'summary','text':'short','tfng':'tfng','ynng':'ynng','multi':'multiple'}
        for q in questions.get(t['id'],[]):
            n=q['number'];pid='unresolved-passage';page=q.get('page',0)
            candidates=[p for p in passages if any(b.get('page',999)<=page for b in p['blocks'])]
            if candidates:pid=candidates[-1]['id']
            gkey=pid+'-'+hashlib.sha256(q.get('instructions','').encode()).hexdigest()[:8];groups.setdefault(gkey,dict(id=gkey,passageIds=[pid],instructions=q.get('instructions',''),source=source))
            opts=[dict(id=f'{t["id"]}-q{n}-o{i+1}',label=o['value'],content=o['label'].removeprefix(o['value']+' · ')) for i,o in enumerate(q.get('options',[]))]
            value=t['answers'][n-1] if n<=len(t['answers']) else ''
            wordlimit=re.search(r'NO MORE THAN\s+(ONE|TWO|THREE|\d+)\s+WORDS?|\b(ONE) WORD',q.get('instructions',''),re.I)
            word={'ONE':1,'TWO':2,'THREE':3}.get((wordlimit[1] or wordlimit[2]).upper(),None) if wordlimit else None
            qs.append(dict(id=f'{t["id"]}-q{n}',number=n,type=mapping[q['type']],prompt=q['prompt'],passageId=pid,groupId=gkey,options=opts,constraints=dict(maxWords=word,maxNumbers=0,select=len(q.get('group',[])) or None),source=dict(source,page=page),key=dict(optionIds=[o['id'] for o in opts if norm_label(o['label'])==norm_label(value)],accepted=value.split('|') if not opts else [],provenance=t['answer'],status='UNVERIFIED')))
        doc=dict(id=t['id'],title=t['title'],testType='academic',fullTest=True,duration=3600,passages=passages,groups=list(groups.values()),questions=qs,sourceDocument=dict(source=source,blocks=blocks,warnings=warnings),legacyAnswerResource=t['answer'],legacyPaperResource=t['paper'])
        store.import_doc(doc,'legacy-migration')
def norm_label(x):return engine.norm(x)
