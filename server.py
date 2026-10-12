"""Ocean English local study server. Run: python server.py [--port 8765]."""
import argparse, json, mimetypes, os, re, sqlite3, time, unicodedata
import uuid
from contextlib import closing
import ai_tutor, ai_provider, listening_practice, speaking_feedback
import ecosystem, knowledge, exams, writing_exams, reading_engine, reading_import, hmac, base64, hashlib
import srs
from datetime import date, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, unquote

BASE=Path(__file__).resolve().parent
DATA=json.loads(Path(os.environ.get('OCEAN_CATALOG',str(BASE/'catalog.private.json'))).read_text(encoding='utf-8'))
MIDPOINTS=json.loads((BASE/'deploy/midpoint-questions.json').read_text(encoding='utf-8')) if (BASE/'deploy/midpoint-questions.json').is_file() else {}
VOCAB_REVIEWED=json.loads((BASE/'vocab-reviewed.json').read_text(encoding='utf-8'))
QUESTION_FILE=BASE/'reading-questions.json'
QUESTIONS=json.loads(QUESTION_FILE.read_text(encoding='utf-8')) if QUESTION_FILE.is_file() else {}
PRONUNCIATION=json.loads((BASE/'vocab-pronunciation.json').read_text(encoding='utf-8')) if (BASE/'vocab-pronunciation.json').is_file() else {}
KNOWLEDGE=knowledge.build(BASE,DATA)
DB=Path(os.environ.get('OCEAN_DB',str(BASE/'state'/'learning.sqlite3')))
DB.parent.mkdir(exist_ok=True)
READING=reading_engine.Store(Path(os.environ.get('OCEAN_READING_DB',str(DB.with_name(DB.stem+'-reading-content.sqlite3')))))
reading_import.migrate(READING,DATA,QUESTIONS)
with closing(sqlite3.connect(DB)) as db, db:
    db.execute('CREATE TABLE IF NOT EXISTS state (id INTEGER PRIMARY KEY CHECK(id=1), body TEXT NOT NULL)')
    db.execute('INSERT OR IGNORE INTO state VALUES(1,?)',(json.dumps(dict(progress={},notes={},attempts=[],plan=None,testDrafts={},known=[])),))

def public_catalog():
    d=json.loads(json.dumps(DATA))
    d['midpointQuestions']={lid:{k:v for k,v in q.items() if k not in ('correct','explanation','wrongReasons')} for lid,q in MIDPOINTS.items()}
    d['resources']={k:{a:b for a,b in v.items() if a not in ('path','sourcePath','original','source')} for k,v in d['resources'].items()}
    d['tests']=[{k:v for k,v in t.items() if k not in ('answers','groups')} for t in d['tests']]
    for test in d['tests']:
        test.update(publicationStatus='NEEDS_REVIEW',questions=[])
    d['readingContent']=READING.list()
    d['readingAudit']=[{k:v for k,v in t.items() if k in ('id','title','status','count','issueCount')} for t in READING.list(admin=True)]
    d['shop']=ecosystem.SHOP
    d['quizzes']={k:[{a:b for a,b in q.items() if a not in ('answers','explanation')} for q in qs] for k,qs in d['quizzes'].items()}
    image_path=BASE/'public/assets/vocab/card-images.json'
    images=json.loads(image_path.read_text(encoding='utf-8')) if image_path.is_file() else {}
    for word in d['vocab']:
        word['id']=srs.word_id(word)
        image=images.get(word['id'])
        if image and image.get('reviewed') is True and re.fullmatch(r'assets/vocab/cards/[a-f0-9]{16}\.webp',image.get('src','')):word['illustration']=image
        word['phonetics']=PRONUNCIATION.get(word['term'])
        reviewed=VOCAB_REVIEWED.get(word['term'])
        if reviewed:
            word.update({k:v for k,v in reviewed.items() if k in ('translation_vi','example_en')})
    return d

def normalize(s): return re.sub(r'\s+',' ',unicodedata.normalize('NFKC',str(s)).strip()).casefold()

def grade(answers,key,groups=()):
    result=[normalize(a) in [normalize(x) for x in k.split('|')] for a,k in zip(answers,key)]
    for group in groups:
        pool=[normalize(key[n-1]) for n in group]
        for n in group:
            a=normalize(answers[n-1]); result[n-1]=a in pool
            if a in pool: pool.remove(a)
    return result

def merge_intervals(intervals):
    merged=[]
    for a,b in sorted(intervals):
        if merged and a <= merged[-1][1]+.25: merged[-1][1]=max(merged[-1][1],b)
        else: merged.append([a,b])
    return merged

class Handler(BaseHTTPRequestHandler):
    def log_message(self,fmt,*args): pass
    def reply(self,data,status=200):
        raw=json.dumps(data,ensure_ascii=False).encode()
        try:
            self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(raw))); self.send_header('Cache-Control','no-store'); self.end_headers(); self.wfile.write(raw)
        except (BrokenPipeError,ConnectionResetError,ConnectionAbortedError): pass
    def allowed(self):
        # Reject DNS rebinding and cross-origin writes. This service has no public login.
        host=self.headers.get('Host',''); expected=f'127.0.0.1:{self.server.server_port}'
        if host not in (expected,f'localhost:{self.server.server_port}'): return False
        origin=self.headers.get('Origin')
        return not origin or origin in (f'http://{expected}',f'http://localhost:{self.server.server_port}')
    def do_GET(self):
        if not self.allowed(): return self.reply({'error':'Host/origin không hợp lệ'},403)
        route=unquote(urlparse(self.path).path)
        if route=='/api/reading-list': return self.reply({'published':READING.list(),'queue':[dict(id=t['id'],title=t['title'],status=t['status'],count=t['count'],issueCount=t['issueCount']) for t in READING.list(admin=True) if t['status']=='NEEDS_REVIEW']})
        if route=='/api/catalog': return self.reply(public_catalog())
        if route=='/api/ai-status': return self.reply(ai_provider.status())
        if route=='/api/state':
            with closing(sqlite3.connect(DB,timeout=10)) as db, db:
                db.execute('BEGIN IMMEDIATE')
                s=json.loads(db.execute('SELECT body FROM state WHERE id=1').fetchone()[0])
                reading_engine.expire(s,READING,time.time()); exams.expire(s,DATA,time.time(),grade); ecosystem.sync(s,DATA,time.time())
                db.execute('UPDATE state SET body=? WHERE id=1',(json.dumps(s,ensure_ascii=False),))
                s['ecosystem']=ecosystem.summary(s,time.time())
                s['onlineStatus']=ecosystem.online(s,{},time.time())
                s['serverNow']=time.time()
                if exams.active(s,time.time()):
                    s.pop('chatHistory',None);s.pop('writingFeedback',None);s.pop('listeningFeedback',None);s.pop('speakingFeedback',None)
                    for a in s['attempts']:
                        a.update(answers=[],key=[],correct=[],explanations=[]);a.pop('rows',None)
                    for e in s.get('exams',{}).values(): e.pop('result',None)
                    for e in s.get('readingSessions',{}).values(): e.pop('result',None)
            return self.reply(s)
        if route=='/api/knowledge-status': return self.reply(knowledge.stats(KNOWLEDGE))
        if route.startswith('/media/'):
            r=DATA['resources'].get(route.removeprefix('/media/'))
            if r and r['id'] in {t['answer'] for t in DATA['tests']}: return self.reply({'error':'Đáp án nguồn chỉ được truy cập trong studio kiểm duyệt có quyền.'},403)
            if r and ('ANSWER' in r.get('original','').upper() or r['id'] in {t['answer'] for t in DATA['tests']}):
                with closing(sqlite3.connect(DB)) as db:
                    s=json.loads(db.execute('SELECT body FROM state WHERE id=1').fetchone()[0])
                if exams.active(s,time.time()): return self.reply({'error':'Đáp án bị ẩn trong phiên thi.'},403)
            if not r or not Path(r['path']).is_file(): return self.reply({'error':'Không tìm thấy tài liệu gốc; kiểm tra ổ E:.'},404)
            return self.send_file(Path(r['path']),ranges=True)
        if route in ('/catalog.private.json','/answer_keys.json','/server.py','/build_catalog.py') or route.startswith('/state/'): return self.reply({'error':'Không tìm thấy'},404)
        target=(BASE/'public'/('index.html' if route=='/' else route.lstrip('/'))).resolve()
        if not target.is_relative_to((BASE/'public').resolve()) or not target.is_file(): return self.reply({'error':'Không tìm thấy'},404)
        self.send_file(target)
    def send_file(self,path,ranges=False):
        size=path.stat().st_size; start=0; end=size-1; status=200
        request=self.headers.get('Range') if ranges else None
        if request:
            m=re.fullmatch(r'bytes=(\d*)-(\d*)',request)
            if not m or not any(m.groups()): return self.range_error(size)
            if m[1]: start=int(m[1]); end=min(int(m[2]),size-1) if m[2] else size-1
            else: start=max(0,size-int(m[2]))
            if start>=size or end<start: return self.range_error(size)
            status=206
        mime=mimetypes.guess_type(str(path))[0] or 'application/octet-stream'
        self.send_response(status); self.send_header('Content-Type',mime); self.send_header('Content-Length',str(end-start+1)); self.send_header('X-Content-Type-Options','nosniff')
        if ranges: self.send_header('Accept-Ranges','bytes')
        if status==206: self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
        self.end_headers()
        try:
            with path.open('rb') as f:
                f.seek(start); left=end-start+1
                while left:
                    chunk=f.read(min(left,256*1024))
                    if not chunk: break
                    self.wfile.write(chunk); left-=len(chunk)
        except (BrokenPipeError,ConnectionResetError,ConnectionAbortedError): pass
    def range_error(self,size):
        self.send_response(416); self.send_header('Content-Range',f'bytes */{size}'); self.send_header('Content-Length','0'); self.end_headers()
    def do_POST(self):
        if not self.allowed(): return self.reply({'error':'Host/origin không hợp lệ'},403)
        try:
            size=int(self.headers.get('Content-Length','0'))
            limit=28000000 if urlparse(self.path).path.startswith('/api/reading-admin/') else 9000000 if urlparse(self.path).path=='/api/speaking-feedback' else 1000000
            if size<1 or size>limit: raise ValueError('Yêu cầu quá lớn hoặc trống')
            body=json.loads(self.rfile.read(size)); route=urlparse(self.path).path
            if not isinstance(body,dict): raise ValueError('Dữ liệu không hợp lệ')
            if route.startswith('/api/reading-admin/'):
                token=os.environ.get('OCEAN_EDITOR_TOKEN','');auth=self.headers.get('Authorization','').removeprefix('Bearer ')
                if len(token)<24 or not hmac.compare_digest(auth,token):return self.reply({'error':'Studio cần khóa quản trị riêng tại backend.'},403)
                action=route.rsplit('/',1)[-1]
                if action=='list':return self.reply({'items':READING.list(admin=True)})
                if action=='get':return self.reply(dict(document=READING.get(body['id'],body.get('version')),history=READING.history(body['id'])))
                if action=='source':
                    doc=READING.get(body['id'],body.get('version'));rid=body.get('resource')
                    if rid not in (doc.get('legacyPaperResource'),doc.get('legacyAnswerResource')):raise ValueError('Nguồn không thuộc đề.')
                    from pypdf import PdfReader
                    reader=PdfReader(DATA['resources'][rid]['path'])
                    return self.reply({'pages':[dict(page=i+1,text=p.extract_text(extraction_mode='layout') or '') for i,p in enumerate(reader.pages)]})
                if action=='source-file':
                    doc=READING.get(body['id'],body.get('version'));rid=body.get('resource')
                    if rid and rid in (doc.get('legacyPaperResource'),doc.get('legacyAnswerResource')):
                        source_path=Path(DATA['resources'][rid]['path'])
                    else:
                        raw_id=doc.get('sourceDocument',{}).get('rawId','')
                        if not re.fullmatch(r'[a-f0-9]{64}\.[a-z0-9]{1,8}',raw_id):raise ValueError('Chưa lưu bản gốc của nguồn này.')
                        source_path=READING.path.parent/(READING.path.stem+'-sources')/raw_id
                    raw=source_path.read_bytes()
                    if len(raw)>20000000:raise ValueError('Nguồn quá lớn để preview.')
                    return self.reply(dict(name=source_path.name,mime='application/pdf' if source_path.suffix.lower()=='.pdf' else 'application/octet-stream',data=base64.b64encode(raw).decode()))
                if action=='import':
                    if body.get('driveId'):raw,name,source=reading_import.drive_download(body['driveId'])
                    else:
                        raw=base64.b64decode(body.get('data',''),validate=True);name=Path(str(body.get('name','document.json'))).name;source=dict(reference='local:'+name)
                    if len(raw)>20000000:raise ValueError('Tệp vượt 20 MB.')
                    candidate=reading_import.candidate(raw,name,source)
                    suffix=Path(name).suffix.lower().lstrip('.')
                    if not re.fullmatch(r'[a-z0-9]{1,8}',suffix):suffix='bin'
                    raw_id=hashlib.sha256(raw).hexdigest()+'.'+suffix
                    source_dir=READING.path.parent/(READING.path.stem+'-sources');source_dir.mkdir(parents=True,exist_ok=True)
                    (source_dir/raw_id).write_bytes(raw)
                    candidate.setdefault('sourceDocument',{})['rawId']=raw_id
                    return self.reply(READING.import_doc(candidate,'authenticated-editor'))
                if action=='edit':return self.reply(READING.import_doc(body['document'],'authenticated-editor-edit'))
                if action=='review':return self.reply(READING.review(body['id'],body['version'],body.get('reviewer'),body.get('questionIds'),body.get('acknowledgeSource') is True))
                if action=='publish':return self.reply(READING.publish(body['id'],body['version'],'authenticated-editor'))
                raise ValueError('Thao tác studio không tồn tại.')
            if route in ('/api/tutor','/api/knowledge','/api/lesson-overview','/api/writing-feedback','/api/listening-check','/api/listening-feedback','/api/speaking-feedback'):
                with closing(sqlite3.connect(DB)) as db:
                    current=json.loads(db.execute('SELECT body FROM state WHERE id=1').fetchone()[0])
                if exams.active(current,time.time()): return self.reply({'error':'Hỏi đáp và học liệu hỗ trợ bị tắt khi đang thi.'},403)
                if route=='/api/lesson-overview': return self.reply({'sources':knowledge.overview(KNOWLEDGE,str(body.get('id','')))})
                if route=='/api/knowledge': result={'sources':knowledge.retrieve(KNOWLEDGE,body.get('query',''),body.get('lesson')), 'method':'Tra cứu tài liệu gốc, không phải câu trả lời AI'}
                elif route=='/api/writing-feedback': result=ai_tutor.writing_feedback(body)
                elif route=='/api/listening-check': return self.reply(listening_practice.check(body))
                elif route=='/api/listening-feedback': result=listening_practice.feedback(body)
                elif route=='/api/speaking-feedback': result=speaking_feedback.feedback(body)
                else: result=ai_tutor.answer(DATA,body,BASE,KNOWLEDGE,current)
                with closing(sqlite3.connect(DB,timeout=10)) as db, db:
                    db.execute('BEGIN IMMEDIATE')
                    s=json.loads(db.execute('SELECT body FROM state WHERE id=1').fetchone()[0])
                    if exams.active(s,time.time()): return self.reply({'error':'Phiên thi đã bắt đầu; nhận xét và hỏi đáp được tạm ẩn.'},403)
                    if route=='/api/speaking-feedback':
                        s.setdefault('speakingFeedback',[]).append(dict(date=time.time(),text=result['text'],inputMode=result['inputMode']))
                        s['speakingFeedback']=s['speakingFeedback'][-30:]
                    elif route=='/api/listening-feedback':
                        s.setdefault('listeningFeedback',[]).append(dict(date=time.time(),text=result['text'],accuracy=result['accuracy']))
                        s['listeningFeedback']=s['listeningFeedback'][-30:]
                    elif route=='/api/writing-feedback':
                        s.setdefault('writingFeedback',[]).append(dict(task=body['task'],date=time.time(),text=result['text']))
                        s['writingFeedback']=s['writingFeedback'][-30:]
                    else:
                        s.setdefault('chatHistory',[]).append(dict(mode='search' if route=='/api/knowledge' else 'ai',query=body.get('query',body.get('question','')),lesson=body.get('lesson',body.get('id')),date=time.time(),result=result))
                        s['chatHistory']=s['chatHistory'][-50:]
                    db.execute('UPDATE state SET body=? WHERE id=1',(json.dumps(s,ensure_ascii=False),))
                return self.reply(result)
            with closing(sqlite3.connect(DB,timeout=10)) as db, db:
                db.execute('BEGIN IMMEDIATE')
                s=json.loads(db.execute('SELECT body FROM state WHERE id=1').fetchone()[0]); response=None
                ecosystem.ensure(s); reading_engine.expire(s,READING,time.time()); exams.expire(s,DATA,time.time(),grade)
                if exams.active(s,time.time()) and route in ('/api/attempts','/api/checkpoint-answer'):
                    return self.reply({'error':'Chấm bài và đáp án hỗ trợ bị khóa trong phiên thi.'},403)
                if route=='/api/reading-content': response=reading_engine.public(READING.get(body.get('id'),body.get('contentVersion'),published=True))
                elif route=='/api/reading-start':
                    active=exams.active(s,time.time())
                    if active and not any(e.get('test')==body.get('id') and e.get('contentVersion') for e in active):raise ValueError('Hãy kết thúc bài thi đang làm trước khi mở bài mới.')
                    response=dict(**reading_engine.start(s,READING,body,time.time()),serverNow=time.time())
                elif route=='/api/reading-session':
                    e=reading_engine.get(s,body.get('session'))
                    if e['submitted'] and exams.active(s,time.time()):raise ValueError('Xem đáp án bị tắt khi đang thi.')
                    response=dict(session=e,document=reading_engine.public(READING.get(e['test'],e['contentVersion'])),serverNow=time.time())
                elif route=='/api/reading-draft':response=reading_engine.draft(s,READING,body,time.time())
                elif route=='/api/reading-pause':response=reading_engine.pause(s,body,time.time())
                elif route=='/api/reading-submit':
                    if exams.active(s,time.time()) and not any(e['id']==body.get('session') for e in exams.active(s,time.time())):raise ValueError('Không xem đáp án bài khác khi đang thi.')
                    response=reading_engine.submit(s,READING,body,time.time())
                elif route=='/api/listening-draft':response=listening_practice.draft(s,body,time.time())
                elif route=='/api/listening-attempt':
                    if exams.active(s,time.time()):raise ValueError('Đối chiếu transcript bị khóa trong phiên thi.')
                    response=listening_practice.attempt(s,body,time.time())
                elif route=='/api/progress':
                    lesson=next((l for l in DATA['lessons'] if l['id']==body.get('id')),None)
                    if not lesson: raise ValueError('Bài học không tồn tại')
                    p=s['progress'].setdefault(lesson['id'],dict(position=0,intervals=[],watched=0,complete=False))
                    if lesson['video']:
                        duration=lesson['duration']
                        if not duration: raise ValueError('Chưa đọc được thời lượng video')
                        position=float(body.get('position',0))
                        if not 0<=position<=duration+1: raise ValueError('Vị trí không hợp lệ')
                        p['position']=min(position,duration)
                        last=p.get('ping',time.time()); budget=min(15,max(0,time.time()-last))*2.05+1
                        intervals=body.get('intervals',[])
                        if len(intervals)>20: raise ValueError('Quá nhiều khoảng xem')
                        valid=[]; total=0
                        for a,b in intervals:
                            a=float(a); b=float(b)
                            if not 0<=a<b<=duration+1: raise ValueError('Khoảng xem không hợp lệ')
                            total+=b-a; valid.append([a,min(b,duration)])
                        if total>budget: raise ValueError('Khoảng xem vượt thời gian phát')
                        p['intervals']=merge_intervals(p['intervals']+valid); p['watched']=round(sum(b-a for a,b in p['intervals']),2)
                        p['complete']=p['watched']>=duration*.9
                        p['ping']=time.time()
                    else:
                        p['complete']=body.get('complete') is True; p['selfReported']=True
                    p['updated']=time.time(); s['lastLesson']=lesson['id']; response=p
                elif route=='/api/notes':
                    lid=body.get('id')
                    if lid not in {l['id'] for l in DATA['lessons']}: raise ValueError('Bài học không tồn tại')
                    s['notes'][lid]=str(body.get('text',''))[:20000]; response={'saved':True}
                elif route=='/api/attempts':
                    lid=body.get('id'); is_test=lid.startswith('reading-') if isinstance(lid,str) else False
                    if is_test:
                        raise ValueError('Đề cũ đang được kiểm duyệt. Dùng Reading engine sau khi nội dung được duyệt.')
                        test=next((t for t in DATA['tests'] if t['id']==lid),None)
                        if not test: raise ValueError('Đề không tồn tại')
                        key=test['answers']; groups=test['groups']; qs=None
                    else:
                        qs=DATA['quizzes'].get(lid)
                        if not qs: raise ValueError('Chưa có bài kiểm tra cho bài này')
                        key=['|'.join(q['answers']) for q in qs]; groups=[]
                    answers=body.get('answers')
                    if not isinstance(answers,list) or len(answers)!=len(key) or any(not isinstance(a,str) or len(a)>500 for a in answers): raise ValueError('Số câu trả lời không hợp lệ')
                    results=grade(answers,key,groups)
                    attempt=dict(id=lid,date=time.time(),score=sum(results),total=len(key),answers=answers,correct=results,key=key,explanations=[q['explanation'] for q in qs] if qs else [])
                    s['attempts'].append(attempt)
                    if is_test: s['testDrafts'].pop(lid,None)
                    response=attempt
                elif route=='/api/test-draft':
                    lid=body.get('id')
                    if lid not in {t['id'] for t in DATA['tests']}: raise ValueError('Đề không tồn tại')
                    answers=body.get('answers',[])
                    if len(answers)!=40 or any(not isinstance(a,str) or len(a)>500 for a in answers): raise ValueError('Đáp án không hợp lệ')
                    started=float(body.get('started',time.time()))
                    if not 0<started<=time.time()+5: raise ValueError('Thời gian không hợp lệ')
                    s['testDrafts'][lid]=dict(answers=answers,started=started); response={'saved':True}
                elif route=='/api/exam-start':
                    raise ValueError('Phiên Reading cũ được lưu lại để đối chiếu; không mở mới trước khi kiểm duyệt.')
                    t=next((t for t in DATA['tests'] if t['id']==body.get('id')),None)
                    if not t: raise ValueError('Đề không tồn tại')
                    response=dict(**exams.start(s,t,body.get('mode'),time.time()),serverNow=time.time())
                elif route=='/api/exam-draft': response=exams.draft(s,body,time.time())
                elif route=='/api/exam-submit':
                    raise ValueError('Cơ chế chấm cũ đã ngừng; bài làm cũ được giữ nguyên để đối chiếu.')
                    response=exams.submit(s,exams.get(s,body),DATA,time.time(),grade)
                elif route=='/api/writing-exam-start':
                    if exams.active(s,time.time()) and not writing_exams.active(s,time.time()):
                        raise ValueError('Hãy nộp phiên Reading đang làm trước.')
                    response=dict(**writing_exams.start(s,body,DATA,time.time()),serverNow=time.time())
                elif route=='/api/writing-exam-draft': response=writing_exams.draft(s,body,time.time())
                elif route=='/api/writing-exam-submit': response=writing_exams.submit(s,writing_exams.get(s,body),time.time())
                elif route=='/api/pet': response=ecosystem.pet_action(s,body,time.time())
                elif route=='/api/online': response=ecosystem.online(s,body,time.time())
                elif route=='/api/writing': response=ecosystem.writing(s,body,time.time())
                elif route=='/api/timestamp-note':
                    lid=body.get('id'); l=next((l for l in DATA['lessons'] if l['id']==lid),None)
                    at=body.get('at'); text=body.get('text')
                    if not l or not l['video'] or not isinstance(at,(int,float)) or not 0<=at<=l['duration']: raise ValueError('Mốc video không hợp lệ')
                    if not isinstance(text,str) or not 1<=len(text.strip())<=2000: raise ValueError('Ghi chú cần 1–2.000 ký tự')
                    n=dict(id=uuid.uuid4().hex,at=at,text=text.strip(),date=time.time())
                    s['timestampNotes'].setdefault(lid,[]).append(n); response=n
                elif route=='/api/speaking':
                    duration=body.get('duration'); reflection=body.get('reflection',''); prompt=body.get('prompt','')
                    if not isinstance(duration,(int,float)) or not 0<=duration<=600 or not isinstance(reflection,str) or len(reflection)>5000 or not isinstance(prompt,str) or len(prompt)>3000: raise ValueError('Buổi luyện nói không hợp lệ')
                    # Duration is self reported; no fake fluency or band score.
                    stars=1 if duration>=30 else 0
                    if stars and len(reflection.strip())>=40: stars=2
                    rec=dict(id=ecosystem.request_token(body),duration=duration,reflection=reflection,prompt=prompt,date=time.time(),stars=stars,selfReported=True)
                    found=next((x for x in s['speakingSessions'] if x['id']==rec['id']),None)
                    if not found:
                        s['speakingSessions'].append(rec)
                        ecosystem.reward(s,'speaking:'+ecosystem.day(time.time()),stars,'Buổi tự luyện nói',time.time())
                    response=found or rec
                elif route=='/api/settings':
                    name=body.get('name','')
                    if not isinstance(name,str) or not 1<=len(name.strip())<=60: raise ValueError('Tên cần 1–60 ký tự')
                    s['settings']=dict(name=name.strip(),motion=body.get('motion') is True); response=s['settings']
                elif route=='/api/continuity':
                    target=body.get('route','')
                    if not isinstance(target,str) or not re.fullmatch(r'#(?:lesson|reading|writing|speaking|library|vocab-practice|vocab-matching|vocab-images|vocab-context)(?:/[\w.%+-]{1,160})?',target):raise ValueError('Vị trí học không hợp lệ.')
                    s['lastRoute']=target;response={'route':target}
                elif route=='/api/plan':
                    ids=body.get('lessons',[]); available={l['id'] for l in DATA['lessons']}
                    if not ids or len(ids)>63 or len(ids)!=len(set(ids)) or any(i not in available for i in ids): raise ValueError('Chọn ít nhất một bài học')
                    minutes=int(body.get('minutes',30))
                    if minutes not in (20,30,45,60): raise ValueError('Thời gian không hợp lệ')
                    weekdays=body.get('weekdays',list(range(7)))
                    if not isinstance(weekdays,list) or not weekdays or any(type(w) is not int or w not in range(7) for w in weekdays): raise ValueError('Chọn ít nhất một ngày học trong tuần')
                    start=date.fromisoformat(body.get('start',date.today().isoformat())); days=[]; current=start; used=0
                    while current.weekday() not in weekdays: current+=timedelta(days=1)
                    for lid in ids:
                        l=next(l for l in DATA['lessons'] if l['id']==lid); cost=max(10,round((l['duration'] or 1200)/60)+10)
                        remaining=cost
                        while remaining:
                            if used==minutes:
                                current+=timedelta(days=1); used=0
                                while current.weekday() not in weekdays: current+=timedelta(days=1)
                            part=min(remaining,minutes-used)
                            days.append(dict(date=current.isoformat(),id=lid,minutes=part,continued=remaining!=cost)); used+=part; remaining-=part
                    s['plan']=dict(minutes=minutes,start=start.isoformat(),weekdays=sorted(set(weekdays)),days=days,lessons=ids); response=s['plan']
                elif route=='/api/midpoint-answer':
                    lid=body.get('id'); q=MIDPOINTS.get(lid)
                    if not q or type(body.get('choice')) is not int or not 0<=body['choice']<len(q['options']): raise ValueError('Chọn một đáp án trong câu hỏi của bài.')
                    if body.get('version')!=q['version']: raise ValueError('Câu hỏi đã đổi. Hãy mở lại bài học.')
                    if exams.active(s,time.time()): raise ValueError('Câu hỏi bài giảng được ẩn khi đang thi.')
                    response=dict(id=lid,version=q['version'],choice=body['choice'],correct=body['choice']==q['correct'],key=q['options'][q['correct']],explanation=q['explanation'],whyWrong=q.get('wrongReasons',[None]*len(q['options']))[body['choice']],date=time.time())
                    s.setdefault('midpointAnswers',{})[lid]=response
                elif route=='/api/checkpoint':
                    lid=body.get('id'); lesson=next((l for l in DATA['lessons'] if l['id']==lid),None)
                    if not lesson or not lesson['video']: raise ValueError('Cần chọn bài có video')
                    at=float(body.get('at',0)); prompt=body.get('prompt',''); answer=body.get('answer','')
                    if not 0<=at<lesson['duration']: raise ValueError('Mốc thời gian ngoài video')
                    if not isinstance(prompt,str) or not 1<=len(prompt.strip())<=1000 or not isinstance(answer,str) or not 1<=len(answer.strip())<=500: raise ValueError('Nhập câu hỏi và đáp án ngắn')
                    items=s.setdefault('checkpoints',{}).setdefault(lid,[])
                    if len(items)>=30: raise ValueError('Mỗi bài tối đa 30 điểm dừng ôn tập')
                    cp=dict(cid=uuid.uuid4().hex,at=round(at,2),prompt=prompt.strip(),answer=answer.strip(),personal=True)
                    items.append(cp); items.sort(key=lambda x:x['at']); response=cp
                elif route=='/api/checkpoint-answer':
                    lid=body.get('id'); cp=next((q for q in s.get('checkpoints',{}).get(lid,[]) if q['cid']==body.get('cid')),None)
                    if not cp: raise ValueError('Không tìm thấy điểm dừng')
                    answer=body.get('answer','')
                    if not isinstance(answer,str) or len(answer)>500: raise ValueError('Đáp án không hợp lệ')
                    response=dict(id=lid,cid=cp['cid'],date=time.time(),answer=answer,correct=normalize(answer)==normalize(cp['answer']),key=cp['answer'])
                    s.setdefault('checkpointAttempts',[]).append(response)
                elif route=='/api/vocab-review':
                    wid=body.get('id')
                    if wid not in {srs.word_id(w) for w in DATA['vocab']}: raise ValueError('Không tìm thấy từ vựng')
                    cards=s.setdefault('vocabReviews',{}); previous=cards.get(wid,{})
                    if type(body.get('version')) is not int or body['version']!=previous.get('version',0):
                        raise ValueError('Thẻ đã được cập nhật ở tab khác. Tải lại để ôn tiếp.')
                    response=srs.review(previous,body.get('rating'),time.time()); cards[wid]=response
                elif route=='/api/vocab-favorite':
                    wid=body.get('id')
                    if wid not in {srs.word_id(w) for w in DATA['vocab']}: raise ValueError('Không tìm thấy từ vựng')
                    favorites=s.setdefault('vocabFavorites',[])
                    if body.get('favorite') is True and wid not in favorites: favorites.append(wid)
                    elif body.get('favorite') is not True and wid in favorites: favorites.remove(wid)
                    response={'favorites':favorites}
                elif route=='/api/flag':
                    token=body.get('token')
                    if not isinstance(token,str) or not re.fullmatch(r'(reading-\d+|combined-[\w-]+|writing-[\w-]+):\d+:\d+',token): raise ValueError('Mã câu hỏi không hợp lệ')
                    flags=s.setdefault('flags',[])
                    if body.get('flagged') is True and token not in flags: flags.append(token)
                    elif body.get('flagged') is not True and token in flags: flags.remove(token)
                    response={'flags':flags}
                else: return self.reply({'error':'Không tìm thấy'},404)
                ecosystem.sync(s,DATA,time.time())
                db.execute('UPDATE state SET body=? WHERE id=1',(json.dumps(s,ensure_ascii=False),))
            if isinstance(response,dict) and route in ('/api/progress','/api/notes','/api/attempts','/api/vocab-review','/api/writing','/api/speaking','/api/pet','/api/exam-submit','/api/writing-exam-submit','/api/reading-submit'):
                response=dict(response,_world=ecosystem.summary(s,time.time()))
            self.reply(response)
        except OSError: self.reply({'error':'Không đọc được nguồn hoặc nguồn từ chối quyền truy cập. Kiểm tra tệp và quyền kết nối.'},400)
        except (ValueError,TypeError,KeyError,OverflowError,json.JSONDecodeError) as e: self.reply({'error':str(e)},400)

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--port',type=int,default=8765); args=parser.parse_args()
    print(f'QUYNH ANH English: http://127.0.0.1:{args.port}',flush=True)
    ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()
