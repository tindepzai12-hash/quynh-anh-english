"""Real isolated checks. Original fixture; no production content is approved."""
import sys,copy,json,tempfile,io,zipfile,time,subprocess,urllib.request,urllib.error,os,socket,base64
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]));sys.path.insert(0,str(Path(__file__).parent))
import reading_engine as r,reading_import as imp,ecosystem
from reading_v5_fixture import document,seed
checks=[]
def check(name,ok):
    checks.append(dict(name=name,passed=bool(ok)))
    if not ok:raise AssertionError(name)
def rejects(fn):
    try:fn();return False
    except (ValueError,KeyError,TypeError):return True
with tempfile.TemporaryDirectory(prefix='qa-reading-v5-') as temp:
    path=Path(temp)/'qa-content.sqlite3';store=r.Store(path);original=document();d=store.import_doc(original)
    check('Import never approves or exposes draft',d['status']=='NEEDS_REVIEW' and not store.list())
    check('Idempotent import',len(store.list(True))==1 and store.import_doc(original)['version']==d['version'])
    check('Missing key cannot publish',rejects(lambda:store.publish(d['id'],d['version'],'QA')))
    def bad(change,code):
        x=copy.deepcopy(original);change(x);return code in {i['code'] for i in r.validate(x,reviewed=False)}
    check('Duplicate question ID',bad(lambda x:x['questions'][1].update(id='q1'),'DUPLICATE_ID'))
    check('Question numbering off by one',bad(lambda x:x['questions'][4].update(number=6),'QUESTION_NUMBERS'))
    check('Missing option',bad(lambda x:x['questions'][0].update(options=x['questions'][0]['options'][:2]),'KEY_OPTIONS'))
    check('Duplicate option content',bad(lambda x:x['questions'][0]['options'][1].update(content='2016'),'DUPLICATE_OPTIONS'))
    check('Wrong passage link',bad(lambda x:x['questions'][0].update(passageId='p99'),'PASSAGE_LINK'))
    check('Wrong group link',bad(lambda x:x['questions'][0].update(groupId='g4'),'GROUP_LINK'))
    check('Wrong type',bad(lambda x:x['questions'][0].update(type='made-up'),'QUESTION_TYPE'))
    check('Key has provenance',bad(lambda x:x['questions'][0]['key'].update(provenance=''),'KEY_PROVENANCE'))
    check('Multiple policy rejects wrong count',bad(lambda x:x['questions'][3]['constraints'].update(select=1),'MULTI_POLICY'))
    check('Missing word limit',bad(lambda x:x['questions'][8]['constraints'].update(maxWords=None),'WORD_LIMIT'))
    check('TFNG not conflated with YNNG',bad(lambda x:x['questions'][1]['options'][1].update(content='NO'),'TRUTH_OPTIONS'))
    check('Explanation wrong question',bad(lambda x:x['questions'][0]['explanation'].update(questionId='q2'),'EXPLANATION_LINK'))
    check('Evidence must match source',bad(lambda x:x['questions'][0]['explanation']['evidence'].update(quote='imagined quote'),'EVIDENCE'))
    check('Full test requires 40 questions',bad(lambda x:x.update(fullTest=True,testType='academic'),'FULL_STRUCTURE'))
    check('Lossy import warns and blocks release',bad(lambda x:x['sourceDocument'].update(warnings=['TABLE_REVIEW']),'SOURCE_PRESERVATION'))
    check('Inline links cannot point across passages',bad(lambda x:x['passages'][1]['blocks'][-2]['rows'][1].__setitem__(2,'{{q1}}'),'INLINE_LINK'))
    check('Diagram anchors outside source dimensions rejected',bad(lambda x:x['passages'][1]['blocks'][1].update(labels=[dict(questionId='q12',x=1.2,y=.3)]),'DIAGRAM_POSITION'))
    check('Blank accepted answer rejected',bad(lambda x:x['questions'][8]['key'].update(accepted=[' ']),'MISSING_KEY'))
    check('Text controls cannot accidentally store option IDs',bad(lambda x:x['questions'][8].update(options=[dict(id='q9-A',label='A',content='river')]),'TEXT_OPTIONS'))
    check('Malformed JSON schema rejected safely',rejects(lambda:store.import_doc(dict(original,questions=[None]))))
    check('Source evidence stays in its passage',bad(lambda x:x['questions'][9].update(passageId='p1',groupId='g1'),'EVIDENCE'))
    # Explicit QA review of original deterministic fixture, not a human review claim.
    d=store.review(d['id'],d['version'],'QA fixture validation',[q['id'] for q in d['questions']]);check('Approve validates all fixture keys',d['status']=='APPROVED')
    d=store.review(d['id'],d['version'],'QA fixture validation',['q1']);check('Unchecking review revokes approval',d['status']=='NEEDS_REVIEW' and d['questions'][1]['key']['status']=='UNVERIFIED')
    d=store.review(d['id'],d['version'],'QA fixture validation',[q['id'] for q in d['questions']])
    d=store.publish(d['id'],d['version'],'QA fixture publication');check('Publish gated',d['status']=='PUBLISHED')
    check('Learner DTO never contains keys/explanations','key' not in r.public(d)['questions'][0] and 'explanation' not in r.public(d)['questions'][0])
    with_metadata=copy.deepcopy(d);with_metadata['editorAnswerKey']='PRIVATE_METADATA';with_metadata['groups'][0]['teacherNotes']='PRIVATE_METADATA';with_metadata['questions'][0]['options'][0]['isCorrect']='PRIVATE_METADATA';with_metadata['passages'][0]['blocks'][0]['editorNotes']='PRIVATE_METADATA'
    check('Unknown imported private metadata excluded at every level','PRIVATE_METADATA' not in json.dumps(r.public(with_metadata)))
    check('Published immutable',rejects(lambda:store.review(d['id'],d['version'],'QA',['q1'])))
    s=dict(attempts=[],progress={},notes={});e=r.start(s,store,dict(id=d['id'],mode='guided'),1000)
    def save(a,version=None):return r.draft(s,store,dict(session=e['id'],contentVersion=e['contentVersion'],version=e['version'] if version is None else version,answers=a,flags=['q2'],focus='q1',highlights=[dict(block='b2',start=0,end=12)]),1010)
    save({'q1':'q1-A'});old=e['version'];save({'q1':'q1-C'})
    check('A then C stores C',e['answers']['q1']=='q1-C')
    check('Stale draft rejected',rejects(lambda:save({'q1':'q1-A'},old)))
    check('Unrelated option ID rejected',rejects(lambda:save({'q1':'q2-FALSE'})))
    check('Too many multiple answers rejected',rejects(lambda:save({'q4':['q4-A','q4-B','q4-C']})))
    check('Navigate preserves answers and markers',e['answers']['q1']=='q1-C' and e['flags']==['q2'])
    restored=json.loads(json.dumps(s));check('Persistence JSON roundtrip restores',r.get(restored,e['id'])['answers']['q1']=='q1-C')
    values={q['id']:(q['key']['optionIds'] if q['type']=='multiple' else q['key']['optionIds'][0] if q['options'] else q['key']['accepted'][0]) for q in d['questions']};save(values)
    check('Reorder options does not change scoring',r.score(dict(d['questions'][0],options=list(reversed(d['questions'][0]['options']))),'q1-C') is True)
    check('Exact multi answer',r.score(d['questions'][3],['q4-C','q4-A']) is True and r.score(d['questions'][3],['q4-A','q4-B']) is False)
    check('False distinct from Not Given',r.score(d['questions'][1],'q2-NOT GIVEN') is False)
    check('Normalize space and case',r.score(d['questions'][13],'  MARA   LIN  ') is True)
    check('Hyphenated single word',r.score(d['questions'][12],'solar-powered') is True)
    check('Word limit applied',r.score(d['questions'][12],'solar powered') is False)
    check('Missing key not scored as false',r.score(dict(d['questions'][0],key={'status':'UNVERIFIED'}),'q1-C') is None)
    check('Submission requires latest version',rejects(lambda:r.submit(s,store,dict(session=e['id'],version=e['version']-1),1020)))
    result=r.submit(s,store,dict(session=e['id'],version=e['version']),1020);check('Golden 15/15',result['score']==15 and result['accuracy']==100)
    check('Review correctly maps evidence',result['rows'][0]['explanation']['questionId']=='q1')
    check('Duplicate submit idempotent',r.submit(s,store,dict(session=e['id']),1030)==result and len(s['attempts'])==1)
    check('No edits after submission',rejects(lambda:save(values)))
    ecosystem.sync(s,{'lessons':[]},1020);balance=s['ecosystem']['balance'];ecosystem.sync(s,{'lessons':[]},1021);check('No duplicate reward',s['ecosystem']['balance']==balance==35)
    exam=r.start(s,store,dict(id=d['id'],mode='exam'),1100);r.expire(s,store,1701);check('Server expiry submits once',exam['submitted'] and exam['result']['expired'] and len(s['attempts'])==2)
    changed=copy.deepcopy(original);changed['title']='Changed source';new=store.import_doc(changed);check('Import changes create separate unpublished version',new['version']!=d['version'] and new['status']=='NEEDS_REVIEW' and store.get(d['id'],d['version'])['status']=='PUBLISHED')
    check('Historical attempts pin version',s['attempts'][0]['contentVersion']==d['version'])
    new=store.review(new['id'],new['version'],'QA fixture validation',[q['id'] for q in new['questions']]);store.publish(new['id'],new['version'],'QA fixture publication')
    check('Publish archives old version without deleting attempts',store.get(d['id'],d['version'])['status']=='ARCHIVED' and s['attempts'][0]['contentVersion']==d['version'])
    check('Draft version mismatch',rejects(lambda:r.draft(s,store,dict(session=exam['id'],contentVersion='other'),1702)))
    # Structured tables survive actual parsers.
    parsed=imp.extract(b'<h1>Title</h1><p>A paragraph.</p><table><tr><th>Day</th><th>Time</th></tr><tr><td>Monday</td><td>18:00</td></tr></table>','sample.html');check('HTML table preserved',next(b for b in parsed['blocks'] if b['type']=='table')['rows'][1]==['Monday','18:00'])
    xml=b'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Passage</w:t></w:r></w:p><w:tbl><w:tr><w:tc><w:p><w:r><w:t>Monday</w:t></w:r></w:p></w:tc></w:tr></w:tbl></w:body></w:document>'
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w') as z:z.writestr('word/document.xml',xml)
    parsed=imp.extract(buf.getvalue(),'table.docx');check('DOCX table preserved',parsed['blocks'][1]['rows']==[['Monday']])
    check('Missing answer import is blocked',store.import_doc(imp.candidate(b'Passage\n\nQuestion 1: A question\nA. first\nB. second','test.txt',{'reference':'fixture'}))['status']=='NEEDS_REVIEW')
    check('Drive disabled without credentials',rejects(lambda:imp.drive_download('abcdefghijklmno')))
    # Live server on separate temporary database. No real progress writes.
    qa_db=Path(temp)/'qa-http.sqlite3';seed(qa_db.with_name('qa-http-reading-content.sqlite3'))
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    env=dict(os.environ,OCEAN_DB=str(qa_db),OCEAN_EDITOR_TOKEN='qa-test-editor-token-not-production-20261010')
    proc=subprocess.Popen([sys.executable,str(Path(__file__).resolve().parents[1]/'server.py'),'--port',str(port)],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    def req(path,body=None,token=None):
        data=json.dumps(body).encode() if body is not None else None;headers={'Content-Type':'application/json'}
        if token:headers['Authorization']='Bearer '+token
        try:
            with urllib.request.urlopen(urllib.request.Request(f'http://127.0.0.1:{port}'+path,data=data,headers=headers),timeout=10) as resp:return resp.status,json.loads(resp.read())
        except urllib.error.HTTPError as err:return err.code,json.loads(err.read())
    try:
        for _ in range(50):
            try:req('/api/state');break
            except (urllib.error.URLError,ConnectionError):time.sleep(.2)
        check('Draft cannot be accessed by learner',req('/api/reading-content',{'id':'reading-1'})[0]==400)
        check('Admin list requires token',req('/api/reading-admin/list',{})[0]==403)
        check('Admin source requires token',req('/api/reading-admin/source',{'id':'reading-1','resource':'r131'})[0]==403)
        check('Source key resource protected',req('/media/r131')[0]==403)
        check('Legacy grade bypass blocked',req('/api/attempts',{'id':'reading-1','answers':['FALSE']*40})[0]==400)
        check('Legacy exam bypass blocked',req('/api/exam-start',{'id':'reading-1','mode':'guided'})[0]==400)
        status,e=req('/api/reading-start',{'id':'qa-reading-golden','mode':'guided'});check('Live start',status==200)
        _,content=req('/api/reading-content',{'id':'qa-reading-golden'});check('No live keys','key' not in content['questions'][0])
        status,draft=req('/api/reading-draft',dict(session=e['id'],contentVersion=e['contentVersion'],version=0,answers={'q1':'q1-C'},flags=[],focus='q1',highlights=[]));check('Live save',status==200)
        _,live=req('/api/reading-session',{'session':e['id']});check('Live restore',live['session']['answers']=={'q1':'q1-C'})
        _,submitted=req('/api/reading-submit',{'session':e['id'],'version':draft['version']});check('Live review correct',submitted['score']==1 and submitted['rows'][0]['correct'])
        status,exam=req('/api/reading-start',{'id':'qa-reading-golden','mode':'exam'});check('Live exam',status==200)
        check('AI restricted',req('/api/knowledge',{'query':'Lantern'})[0]==403)
        check('Other result blocked in active exam',req('/api/reading-submit',{'session':e['id']})[0]==400)
        check('State redacts review rows',all('rows' not in a for a in req('/api/state')[1]['attempts']))
        check('Session resume uses original deadline',req('/api/reading-start',{'id':'qa-reading-golden','mode':'exam'})[1]['deadline']==exam['deadline'])
        check('Authenticated editor can inspect queue',req('/api/reading-admin/list',{},env['OCEAN_EDITOR_TOKEN'])[0]==200)
        check('Original file endpoint requires editor',req('/api/reading-admin/source-file',{'id':'reading-1','resource':'r131'})[0]==403)
        code,raw_source=req('/api/reading-admin/source-file',{'id':'reading-1','resource':'r131'},env['OCEAN_EDITOR_TOKEN'])
        check('Editor can view exact original PDF',code==200 and base64.b64decode(raw_source['data']).startswith(b'%PDF'))
        imported=dict(document(),id='qa-http-import',title='QA import only')
        code,stored=req('/api/reading-admin/import',dict(name='qa-original.json',data=base64.b64encode(json.dumps(imported).encode()).decode()),env['OCEAN_EDITOR_TOKEN'])
        check('HTTP import stays unpublished',code==200 and stored['status']=='NEEDS_REVIEW')
        code,raw_source=req('/api/reading-admin/source-file',dict(id=stored['id'],version=stored['version']),env['OCEAN_EDITOR_TOKEN'])
        check('Uploaded source roundtrip is exact',code==200 and json.loads(base64.b64decode(raw_source['data']))==imported)
        check('Malformed import returns explicit error',req('/api/reading-admin/edit',dict(document={'id':'broken','questions':[None]}),env['OCEAN_EDITOR_TOKEN'])[0]==400)
    finally:proc.terminate();proc.wait(timeout=10)
out=Path(__file__).resolve().parents[1]/'artifacts/reading-v5/reports';out.mkdir(parents=True,exist_ok=True)
(out/'engine-tests.json').write_text(json.dumps(dict(passed=len(checks),checks=checks),indent=2),encoding='utf8');print(str(len(checks))+' checks passed')
