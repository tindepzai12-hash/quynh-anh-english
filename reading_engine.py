"""Versioned Reading content, editorial gates and server-owned attempts.

Answer keys never appear in learner content. Imported candidates are untrusted.
An explicit authenticated editorial review is required before publication.
"""
import copy, hashlib, json, re, sqlite3, time, unicodedata, uuid
from pathlib import Path
from contextlib import contextmanager

CHOICES={'single','multiple','tfng','ynng','matching_headings','matching_information','matching_features','matching_endings'}
TEXT={'sentence','summary','note','table','flowchart','diagram','short'}
TYPES=CHOICES|TEXT
def norm(value): return re.sub(r'\s+',' ',unicodedata.normalize('NFKC',str(value)).strip()).casefold()
def stamp(doc): return hashlib.sha256(json.dumps(doc,sort_keys=True,ensure_ascii=False).encode()).hexdigest()[:24]

def validate(doc, reviewed=True):
    issues=[]
    def issue(code,path,detail): issues.append(dict(code=code,path=path,detail=detail,severity='error'))
    if not isinstance(doc,dict):
        issue('SCHEMA','document','Nội dung phải là object.');return issues
    for field in ('questions','passages','groups'):
        if not isinstance(doc.get(field),list) or any(not isinstance(x,dict) for x in doc.get(field,[])):
            issue('SCHEMA',field,'Cần danh sách object có cấu trúc.');return issues
        if any(not isinstance(x.get('id'),str) for x in doc[field]):
            issue('SCHEMA',field,'ID phải là chuỗi.');return issues
    for p in doc['passages']:
        if not isinstance(p.get('blocks'),list) or any(not isinstance(b,dict) or not isinstance(b.get('id'),str) for b in p.get('blocks',[])):
            issue('SCHEMA','passages','Khối nguồn cần cấu trúc và ID chuỗi.');return issues
        for b in p['blocks']:
            if not isinstance(b.get('text',''),str) or not isinstance(b.get('items',[]),list) or any(not isinstance(x,str) for x in b.get('items',[])) or not isinstance(b.get('rows',[]),list) or any(not isinstance(r,list) or any(not isinstance(c,str) for c in r) for r in b.get('rows',[])) or not isinstance(b.get('labels',[]),list) or any(not isinstance(l,dict) for l in b.get('labels',[])):
                issue('SCHEMA',b['id'],'Văn bản, bảng hoặc nhãn sai cấu trúc.');return issues
    for q in doc['questions']:
        if not isinstance(q.get('type'),str) or not isinstance(q.get('prompt',''),str) or not isinstance(q.get('options',[]),list) or any(not isinstance(o,dict) or not isinstance(o.get('id'),str) or not isinstance(o.get('content',''),str) for o in q.get('options',[])) or any(not isinstance(q.get(k,{}),dict) for k in ('key','constraints','source')):
            issue('SCHEMA','questions','Câu hỏi, phương án hoặc đáp án sai cấu trúc.');return issues
        key=q.get('key',{})
        if any(not isinstance(key.get(k,[]),list) or any(not isinstance(x,str) for x in key.get(k,[])) for k in ('optionIds','accepted')) or (q.get('explanation') is not None and not isinstance(q['explanation'],dict)):
            issue('SCHEMA',q.get('id'),'Danh sách đáp án hoặc lời giải sai cấu trúc.');return issues
    if any(not isinstance(g.get('context',''),str) or not isinstance(g.get('passageIds',[]),list) or any(not isinstance(i,str) for i in g.get('passageIds',[])) for g in doc['groups']) or not isinstance(doc.get('sourceDocument',{}),dict):
        issue('SCHEMA','groups','Liên kết nhóm hoặc nguồn sai cấu trúc.');return issues
    if doc.get('testType') not in ('academic','general','practice'): issue('TEST_TYPE','testType','Chọn Academic, General hoặc bài luyện ngắn.')
    qs=doc.get('questions',[]);ps=doc.get('passages',[]);gs=doc.get('groups',[])
    if not qs: issue('NO_QUESTIONS','questions','Không có câu hỏi.')
    source=doc.get('sourceDocument',{})
    if any(not isinstance(source.get(k,[]),list) or any(not isinstance(x,str) for x in source.get(k,[])) for k in ('warnings','reviewedWarnings')):
        issue('SCHEMA','sourceDocument','Cảnh báo nguồn phải là danh sách chuỗi.');return issues
    if set(source.get('warnings',[]))-set(source.get('reviewedWarnings',[])):issue('SOURCE_PRESERVATION','sourceDocument','Chưa đối chiếu những nội dung parser có thể làm mất hoặc sai thứ tự.')
    if doc.get('fullTest') and (len(qs)!=40 or (doc.get('testType')=='academic' and len(ps)!=3) or (doc.get('testType')=='general' and len(doc.get('sections',[]))!=3)):issue('FULL_STRUCTURE','exam','Bài IELTS đầy đủ cần 40 câu và 3 phần; General có thể gồm nhiều văn bản trong một phần.')
    for field,items in [('passages',ps),('groups',gs),('questions',qs)]:
        ids=[x.get('id') for x in items]
        if any(not isinstance(i,str) or not re.fullmatch(r'[\w.-]{1,100}',i) for i in ids):issue('INVALID_ID',field,'ID phải là chuỗi ổn định hợp lệ.')
        if len(ids)!=len(set(ids)):issue('DUPLICATE_ID',field,'ID trùng nhau.')
    pids={p.get('id') for p in ps};gmap={g.get('id'):g for g in gs}
    block_ids=[b.get('id') for p in ps for b in p.get('blocks',[])]
    if len(set(block_ids))!=len(block_ids) or any(not i for i in block_ids):issue('BLOCK_IDS','passages','Khối văn bản cần ID duy nhất.')
    blockmap={b.get('id'):b for p in ps for b in p.get('blocks',[])}
    block_passages={b.get('id'):p.get('id') for p in ps for b in p.get('blocks',[])}
    question_map={q.get('id'):q for q in qs if isinstance(q.get('id'),str)}
    numbers=[q.get('number') for q in qs]
    if sorted(numbers,key=lambda n:n if type(n)is int else -1)!=list(range(1,len(qs)+1)):issue('QUESTION_NUMBERS','questions','Số câu phải liên tục và không trùng.')
    for p in ps:
        if not p.get('blocks'):issue('MISSING_PASSAGE',p.get('id'),'Bài đọc trống.')
        for b in p.get('blocks',[]):
            linked=re.findall(r'\{\{([\w.-]+)\}\}',b.get('text','')+' '.join(b.get('items',[]))+' '.join(c for r in b.get('rows',[]) for c in r))
            linked.extend(l.get('questionId') for l in b.get('labels',[]))
            for qid in linked:
                target=question_map.get(qid) if isinstance(qid,str) else None
                if not target or target.get('passageId')!=p.get('id'):issue('INLINE_LINK',b.get('id'),'Chỗ trống hoặc nhãn phải trỏ đến câu thuộc cùng passage.')
            if b.get('type') not in ('paragraph','heading','table','image','list','caption','flowchart','diagram'):issue('BLOCK_TYPE',p.get('id'),'Khối nội dung không được hỗ trợ.')
            if b.get('type')=='table' and (not b.get('rows') or len({len(r) for r in b['rows']})!=1):issue('TABLE_SHAPE',b.get('id'),'Bảng thiếu hàng hoặc lệch cột.')
            if b.get('type') in ('image','diagram') and not (str(b.get('src','')).startswith('/reading-media/') or re.match(r'^data:image/(png|jpeg|webp);base64,',str(b.get('src','')))):issue('MEDIA',b.get('id'),'Hình phải được nhập vào kho nội bộ.')
            for label in b.get('labels',[]):
                if 'x' in label or 'y' in label:
                    if any(type(label.get(axis)) not in (float,int) or not 0<=label[axis]<=1 for axis in ('x','y')):
                        issue('DIAGRAM_POSITION',b.get('id'),'Tọa độ nhãn cần cả x/y trong khoảng 0–1 của hình nguồn.')
    for q in qs:
        path=q.get('id');typ=q.get('type');opts=q.get('options',[]);key=q.get('key',{});con=q.get('constraints',{})
        if typ not in TYPES:issue('QUESTION_TYPE',path,'Loại câu chưa xác định.')
        if q.get('passageId') not in pids:issue('PASSAGE_LINK',path,'Không tìm thấy passage.')
        group=gmap.get(q.get('groupId'))
        if not group or q.get('passageId') not in group.get('passageIds',[]):issue('GROUP_LINK',path,'Nhóm và passage không khớp.')
        if not q.get('prompt') or re.search('Đọc câu.*đề gốc|trong PDF',q.get('prompt','')):issue('UNRESOLVED_PROMPT',path,'Câu hỏi vẫn cần mở tài liệu gốc.')
        if not q.get('source',{}).get('reference'):issue('SOURCE',path,'Thiếu căn cứ nguồn câu hỏi.')
        if typ in CHOICES:
            ids=[o.get('id') for o in opts]
            if len(opts)<2 or len(set(ids))!=len(ids) or any(not re.fullmatch(r'[\w.-]{1,100}',i) for i in ids):issue('OPTIONS',path,'Thiếu hoặc trùng ID phương án.')
            if len({norm(o.get('content','')) for o in opts})!=len(opts):issue('DUPLICATE_OPTIONS',path,'Nội dung phương án trùng nhau.')
            if any(not o.get('content') or re.search('trong PDF',o.get('content','')) for o in opts):issue('OPTION_CONTENT',path,'Phương án chưa có nội dung hoàn chỉnh.')
            correct=key.get('optionIds',[])
            if not correct or not set(correct)<=set(ids) or len(correct)!=len(set(correct)):issue('KEY_OPTIONS',path,'Đáp án không trỏ tới ID phương án có thật.')
            if typ!='multiple' and len(correct)!=1:issue('KEY_COUNT',path,'Câu chọn một cần đúng một đáp án.')
            if typ=='multiple' and (type(con.get('select'))is not int or con['select']<2 or con['select']!=len(correct)):issue('MULTI_POLICY',path,'Số lựa chọn và đáp án phải khớp; chấm exact-set được cấu hình rõ.')
            expected={'tfng':{'true','false','not given'},'ynng':{'yes','no','not given'}}.get(typ)
            if expected and {norm(o.get('content','')) for o in opts}!=expected:issue('TRUTH_OPTIONS',path,'Không được đổi FALSE/NO thành NOT GIVEN.')
        if typ in TEXT:
            if opts:issue('TEXT_OPTIONS',path,'Câu nhập văn bản không dùng option ID; cần chọn loại câu và khóa phù hợp với nguồn.')
            if not key.get('accepted') or any(not norm(a) for a in key['accepted']):issue('MISSING_KEY',path,'Không có đáp án văn bản nguồn.')
            if type(con.get('maxWords'))is not int or not 1<=con['maxWords']<=10:issue('WORD_LIMIT',path,'Chưa xác minh giới hạn từ.')
            if type(con.get('maxNumbers',0))is not int or not 0<=con.get('maxNumbers',0)<=10:issue('NUMBER_LIMIT',path,'Giới hạn số chưa hợp lệ.')
        if not key.get('provenance'):issue('KEY_PROVENANCE',path,'Đáp án chưa có nguồn.')
        if reviewed and (key.get('status')!='VERIFIED' or not key.get('reviewer') or not key.get('reviewedAt')):issue('UNVERIFIED_KEY',path,'Cần người kiểm duyệt đối chiếu đáp án nguồn.')
        exp=q.get('explanation')
        if exp and (exp.get('questionId')!=path or exp.get('status')!='VERIFIED'):issue('EXPLANATION_LINK',path,'Lời giải chưa duyệt hoặc liên kết sai câu.')
        if exp and exp.get('evidence'):
            ev=exp['evidence']
            if not isinstance(ev,dict):issue('EVIDENCE',path,'Căn cứ phải có cấu trúc.');continue
            block=blockmap.get(ev.get('blockId')) if isinstance(ev.get('blockId'),str) else None
            if not block or block_passages.get(ev.get('blockId'))!=q.get('passageId') or not isinstance(ev.get('quote'),str) or not ev['quote'] or ev['quote'] not in block.get('text',''):issue('EVIDENCE',path,'Trích dẫn phải có thật trong passage của câu hỏi.')
    for g in gs:
        if not set(g.get('passageIds',[]))<=pids:issue('GROUP_PASSAGE',g.get('id'),'Nhóm trỏ tới passage không có.')
        for qid in re.findall(r'\{\{([\w.-]+)\}\}',g.get('context','')):
            if qid not in question_map or question_map[qid].get('groupId')!=g['id']:issue('GROUP_INLINE',g['id'],'Chỗ trống trong ngữ cảnh phải trỏ tới câu thuộc nhóm.')
    return issues

class Store:
    def __init__(self,path):
        self.path=Path(path)
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS reading_content(id TEXT, version TEXT, status TEXT, body TEXT, issues TEXT, updated REAL, PRIMARY KEY(id,version))')
            db.execute('CREATE TABLE IF NOT EXISTS reading_events(id INTEGER PRIMARY KEY, contentId TEXT, version TEXT, action TEXT, actor TEXT, at REAL)')
    @contextmanager
    def connect(self):
        db=sqlite3.connect(self.path,timeout=10)
        try:
            with db:yield db
        finally:db.close()
    def import_doc(self,doc,actor='import'):
        preliminary=validate(doc,False)
        if any(i['code']=='SCHEMA' for i in preliminary):raise ValueError('Cấu trúc nội dung không hợp lệ: '+preliminary[0]['detail'])
        doc=copy.deepcopy(doc);doc.pop('version',None);doc.pop('status',None);doc.pop('issues',None)
        if not re.fullmatch(r'[\w.-]{1,100}',str(doc.get('id',''))):raise ValueError('ID đề không hợp lệ.')
        for q in doc.get('questions',[]):
            q.setdefault('key',{}).update(status='UNVERIFIED');q['key'].pop('reviewer',None);q['key'].pop('reviewedAt',None)
            if q.get('explanation'):q['explanation']['status']='UNVERIFIED'
        version=stamp(doc);issues=validate(doc);status='NEEDS_REVIEW'
        with self.connect() as db:
            existing=db.execute('SELECT body FROM reading_content WHERE id=? AND version=?',(doc['id'],version)).fetchone()
            if existing:return self.get(doc['id'],version)
            db.execute('INSERT INTO reading_content VALUES(?,?,?,?,?,?)',(doc['id'],version,status,json.dumps(doc,ensure_ascii=False),json.dumps(issues,ensure_ascii=False),time.time()))
            db.execute('INSERT INTO reading_events(contentId,version,action,actor,at) VALUES(?,?,?,?,?)',(doc['id'],version,'IMPORT',actor,time.time()))
        return self.get(doc['id'],version)
    def get(self,id,version=None,published=False):
        with self.connect() as db:
            sql='SELECT version,status,body,issues FROM reading_content WHERE id=?';args=[id]
            if version:sql+=' AND version=?';args.append(version)
            if published:sql+=" AND status='PUBLISHED'"
            row=db.execute(sql+' ORDER BY updated DESC LIMIT 1',args).fetchone()
        if not row:raise ValueError('Đề chưa xuất bản hoặc phiên bản không tồn tại.')
        version,status,body,issues=row;doc=json.loads(body);doc.update(version=version,status=status,issues=json.loads(issues));return doc
    def list(self,admin=False):
        with self.connect() as db:rows=db.execute('SELECT id,version,status,body,issues FROM reading_content ORDER BY updated DESC').fetchall()
        return [dict(id=i,version=v,status=s,title=json.loads(b).get('title',i),testType=json.loads(b).get('testType'),fullTest=json.loads(b).get('fullTest',False),count=len(json.loads(b).get('questions',[])),issueCount=len(json.loads(issues))) for i,v,s,b,issues in rows if admin or s=='PUBLISHED']
    def review(self,id,version,reviewer,question_ids,acknowledge_source=False):
        doc=self.get(id,version)
        if doc['status']=='PUBLISHED':raise ValueError('Phiên bản đã xuất bản bất biến; hãy nhập phiên bản mới.')
        if not isinstance(reviewer,str) or len(reviewer.strip())<2:raise ValueError('Cần tên người đối chiếu nguồn.')
        known={q['id'] for q in doc['questions']}
        if not isinstance(question_ids,list) or not set(question_ids)<=known:raise ValueError('ID câu kiểm duyệt không hợp lệ.')
        for q in doc['questions']:
            if q['id'] in question_ids:
                q['key'].update(status='VERIFIED',reviewer=reviewer.strip(),reviewedAt=time.time())
                if q.get('explanation'):q['explanation']['status']='VERIFIED'
            else:
                q['key'].update(status='UNVERIFIED')
                if q.get('explanation'):q['explanation']['status']='UNVERIFIED'
        if acknowledge_source:
            doc.setdefault('sourceDocument',{}).update(reviewedWarnings=doc.get('sourceDocument',{}).get('warnings',[]),reviewer=reviewer,reviewedAt=time.time())
        issues=validate(doc);status='APPROVED' if not issues else 'NEEDS_REVIEW'
        self._update(doc,status,issues,'REVIEW',reviewer);return self.get(id,version)
    def publish(self,id,version,actor):
        doc=self.get(id,version);issues=validate(doc)
        if doc['status']!='APPROVED' or issues:raise ValueError('Chỉ xuất bản bản đã được kiểm duyệt và không còn lỗi.')
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute("UPDATE reading_content SET status='ARCHIVED' WHERE id=? AND version<>? AND status IN ('PUBLISHED','APPROVED','NEEDS_REVIEW')",(id,version))
            db.execute("UPDATE reading_content SET status='PUBLISHED',updated=? WHERE id=? AND version=?",(time.time(),id,version))
            db.execute('INSERT INTO reading_events(contentId,version,action,actor,at) VALUES(?,?,?,?,?)',(id,version,'PUBLISH',actor,time.time()))
        return self.get(id,version)
    def _update(self,doc,status,issues,action,actor):
        body={k:v for k,v in doc.items() if k not in ('version','status','issues')}
        with self.connect() as db:
            db.execute('UPDATE reading_content SET status=?,body=?,issues=?,updated=? WHERE id=? AND version=?',(status,json.dumps(body,ensure_ascii=False),json.dumps(issues,ensure_ascii=False),time.time(),doc['id'],doc['version']))
            db.execute('INSERT INTO reading_events(contentId,version,action,actor,at) VALUES(?,?,?,?,?)',(doc['id'],doc['version'],action,actor,time.time()))
    def history(self,id):
        with self.connect() as db:rows=db.execute('SELECT version,action,actor,at FROM reading_events WHERE contentId=? ORDER BY id DESC',(id,)).fetchall()
        return [dict(version=v,action=a,actor=r,at=t) for v,a,r,t in rows]

def public(doc):
    # Whitelist every level: imported editor metadata may include key hints,
    # original-file details or option.isCorrect. None belongs in learner DTOs.
    def fields(obj,allowed):return {k:copy.deepcopy(obj[k]) for k in allowed if k in obj}
    out=fields(doc,('id','version','title','testType','fullTest','duration'))
    out['passages']=[]
    for p in doc['passages']:
        passage=fields(p,('id','title'));passage['blocks']=[]
        for b in p['blocks']:
            block=fields(b,('id','type','text','rows','items','caption','src','alt'))
            if 'labels' in b:block['labels']=[fields(l,('questionId','label','x','y')) for l in b['labels']]
            passage['blocks'].append(block)
        out['passages'].append(passage)
    out['groups']=[fields(g,('id','title','instructions','context','passageIds')) for g in doc['groups']]
    out['questions']=[]
    for q in doc['questions']:
        question=fields(q,('id','number','type','prompt','passageId','groupId'))
        question['options']=[fields(o,('id','label','content')) for o in q.get('options',[])]
        question['constraints']=fields(q.get('constraints',{}),('maxWords','maxNumbers','select'))
        out['questions'].append(question)
    return out
def sessions(s):return s.setdefault('readingSessions',{})
def active(s,now):return [e for e in sessions(s).values() if e['mode']=='exam' and not e['submitted'] and now<e['deadline']]
def start(s,store,body,now):
    mode=body.get('mode')
    if mode not in ('guided','exam'):raise ValueError('Chế độ không hợp lệ.')
    doc=store.get(body.get('id'),body.get('contentVersion'),published=True)
    existing=next((e for e in sessions(s).values() if e['test']==doc['id'] and not e['submitted']),None)
    if existing:return existing
    duration=3600 if doc.get('fullTest') else int(doc.get('duration',600))
    if not 60<=duration<=3600:raise ValueError('Thời lượng không hợp lệ.')
    e=dict(id=uuid.uuid4().hex,test=doc['id'],contentVersion=doc['version'],mode=mode,started=now,deadline=now+duration,version=0,answers={},flags=[],focus=doc['questions'][0]['id'],highlights=[],submitted=False,events=[dict(action='START',at=now)])
    sessions(s)[e['id']]=e;return e
def get(s,id):
    e=sessions(s).get(id)
    if not e:raise ValueError('Phiên làm bài không tồn tại.')
    return e
def check_answers(doc,answers):
    qs={q['id']:q for q in doc['questions']}
    if not isinstance(answers,dict) or not set(answers)<=set(qs):raise ValueError('ID câu trả lời không khớp phiên bản.')
    for id,a in answers.items():
        q=qs[id]
        if q['type'] in CHOICES:
            ids={o['id'] for o in q['options']}
            if q['type']=='multiple':
                if not isinstance(a,list) or any(not isinstance(x,str) for x in a) or len(a)!=len(set(a)) or not set(a)<=ids or len(a)>q['constraints']['select']:raise ValueError('Lựa chọn nhiều đáp án không hợp lệ.')
            elif not isinstance(a,str) or (a and a not in ids):raise ValueError('ID phương án không hợp lệ.')
        elif not isinstance(a,str) or len(a)>500:raise ValueError('Đáp án văn bản không hợp lệ.')
def draft(s,store,body,now):
    e=get(s,body.get('session'))
    if e['submitted']:raise ValueError('Bài đã khóa sau khi nộp.')
    if e.get('paused'):raise ValueError('Tiếp tục buổi luyện trước khi chỉnh bài làm.')
    if e['mode']=='exam' and now>=e['deadline']:raise ValueError('Hết giờ; bài đã lưu sẽ được chấm.')
    if body.get('version')!=e['version']:raise ValueError('Bài thay đổi ở tab khác. Bản nháp của bạn được giữ; tải lại để đối chiếu.')
    if body.get('contentVersion')!=e['contentVersion']:raise ValueError('Phiên bản nội dung không khớp.')
    doc=store.get(e['test'],e['contentVersion']);answers=body.get('answers');check_answers(doc,answers)
    qids={q['id'] for q in doc['questions']};flags=body.get('flags',[]);focus=body.get('focus')
    if not isinstance(flags,list) or any(not isinstance(x,str) for x in flags) or not set(flags)<=qids or not isinstance(focus,str) or focus not in qids:raise ValueError('Điều hướng không hợp lệ.')
    highlights=body.get('highlights',[])
    if not isinstance(highlights,list) or len(highlights)>200:raise ValueError('Quá nhiều đoạn tô sáng.')
    blocks={b.get('id'):b for p in doc['passages'] for b in p['blocks']}
    for h in highlights:
        if not isinstance(h,dict) or not isinstance(h.get('block'),str):raise ValueError('Đoạn tô sáng không hợp lệ.')
        b=blocks.get(h.get('block'));a=h.get('start');z=h.get('end')
        if not b or type(a)is not int or type(z)is not int or not 0<=a<z<=len(b.get('text','')):raise ValueError('Đoạn tô sáng không khớp văn bản nguồn.')
    notes=body.get('notes',e.get('notes',{}));prefs=body.get('preferences',e.get('preferences',{}))
    if not isinstance(notes,dict) or not set(notes)<={p['id'] for p in doc['passages']} or any(not isinstance(v,str) or len(v)>4000 for v in notes.values()):raise ValueError('Ghi chú phải thuộc bài đọc và không vượt 4.000 ký tự mỗi bài.')
    if not isinstance(prefs,dict) or set(prefs)-{'fontSize','split'} or type(prefs.get('fontSize',16))is not int or prefs.get('fontSize',16) not in (16,18,20,22) or type(prefs.get('split',50))is not int or not 35<=prefs.get('split',50)<=65:raise ValueError('Thiết lập khung đọc không hợp lệ.')
    e.update(answers=copy.deepcopy(answers),flags=sorted(set(flags)),focus=focus,highlights=copy.deepcopy(highlights),notes=copy.deepcopy(notes),preferences=copy.deepcopy(prefs),updated=now,version=e['version']+1)
    e['events'].append(dict(action='SAVE',at=now,version=e['version']));e['events']=e['events'][-200:];return e

def pause(s,body,now):
    e=get(s,body.get('session'))
    if e['submitted'] or e['mode']!='guided':raise ValueError('Chỉ buổi luyện tập chưa nộp mới được tạm dừng.')
    if body.get('version')!=e['version']:raise ValueError('Phiên đã thay đổi. Tải lại để đối chiếu trước khi tiếp tục.')
    target=body.get('paused')
    if type(target)is not bool:raise ValueError('Trạng thái tạm dừng không hợp lệ.')
    if bool(e.get('paused'))==target:return e
    if target:e['pausedAt']=now
    else:e['pausedSeconds']=e.get('pausedSeconds',0)+max(0,now-e.get('pausedAt',now));e.pop('pausedAt',None)
    e.update(paused=target,updated=now,version=e['version']+1)
    e['events'].append(dict(action='PAUSE' if target else 'RESUME',at=now));e['events']=e['events'][-200:]
    return e
def words(answer):
    tokens=norm(answer).split();numbers=[x for x in tokens if re.fullmatch(r'[\d.,:/-]+',x)]
    return len(tokens)-len(numbers),len(numbers)
def score(q,answer):
    key=q['key']
    if key.get('status')!='VERIFIED':return None
    if q['type'] in CHOICES:
        return set(answer or [])==set(key['optionIds']) if q['type']=='multiple' else answer in key['optionIds']
    w,n=words(answer);con=q['constraints']
    valid=w<=con['maxWords'] and n<=con.get('maxNumbers',0) and w+n>0
    return valid and norm(answer) in {norm(x) for x in key['accepted']}
def submit(s,store,body,now):
    e=get(s,body.get('session'))
    if e['submitted']:return e['result']
    if e.get('paused'):raise ValueError('Tiếp tục buổi luyện trước khi nộp bài.')
    expired=e['mode']=='exam' and now>=e['deadline']
    if not expired and body.get('version')!=e['version']:raise ValueError('Hãy lưu lựa chọn mới nhất trước khi nộp.')
    doc=store.get(e['test'],e['contentVersion']);issues=validate(doc)
    if issues:raise ValueError('Không chấm điểm: phiên bản đề có lỗi cần kiểm duyệt.')
    rows=[]
    for q in doc['questions']:
        a=e['answers'].get(q['id'],[] if q['type']=='multiple' else '')
        rows.append(dict(questionId=q['id'],number=q['number'],type=q['type'],answer=a,correct=score(q,a),key=q['key'],explanation=q.get('explanation'),unanswered=not a if isinstance(a,list) else not norm(a)))
    score_=sum(r['correct'] is True for r in rows);total=len(rows)
    result=dict(id=e['test'],session=e['id'],contentVersion=e['contentVersion'],date=now,mode=e['mode'],score=score_,total=total,accuracy=round(score_/total*100,1),rows=rows,answers=[str(r['answer']) for r in rows],correct=[r['correct'] for r in rows],key=[],explanations=[],expired=expired,engine='reading-v5')
    s.setdefault('attempts',[]).append(result);e.update(submitted=True,result=result)
    e['events'].append(dict(action='SUBMIT',at=now));return result
def expire(s,store,now):
    for e in list(sessions(s).values()):
        if e['mode']=='exam' and not e['submitted'] and now>=e['deadline']:submit(s,store,dict(session=e['id']),now)
