"""Server-owned rewards, pet inventory and fixed 24-hour online cycles.

No client-supplied score, price, coin amount or time credit is trusted.
All mutations run inside the host server's BEGIN IMMEDIATE transaction.
"""
import re, uuid, math
from datetime import datetime, timedelta, timezone

TAIPEI=timezone(timedelta(hours=8), 'Asia/Taipei')
SHOP=[
    dict(id='berry', name='Dâu ngọt', category='food', price=8, art='berry', detail='Một bữa ăn vui vẻ; dùng một lần.'),
    dict(id='fish', name='Bánh cá', category='food', price=12, art='fish', detail='Bữa ăn nhỏ cho Justin Mini; dùng một lần.'),
    dict(id='scarf', name='Khăn san hô', category='outfit', price=30, art='scarf', detail='Khăn đỏ mềm, có thể tháo và mặc lại.'),
    dict(id='cap', name='Mũ thuyền trưởng', category='hat', price=45, art='cap', detail='Mũ xanh với ngôi sao vàng.'),
    dict(id='lagoon', name='Ánh xanh đầm phá', category='skin', price=50, art='lagoon', detail='Tông xanh ngọc, giữ nguyên tạo hình Justin.'),
    dict(id='plant', name='Góc cây xanh', category='decor', price=25, art='plant', detail='Một chậu cây đặt cạnh góc đọc sách.'),
    dict(id='lamp', name='Đèn đọc sách', category='decor', price=35, art='lamp', detail='Ánh sáng ấm cho căn phòng.'),
    dict(id='school', name='Bạn nhỏ đến lớp', category='outfit', price=55, art='school', detail='Ba lô san hô cùng quai kem, dựng bằng mesh 3D.'),
    dict(id='space', name='Nhà thám hiểm nhỏ', category='outfit', price=65, art='space', detail='Đai và vòng tay phi hành gia, giữ nguyên mặt Justin.'),
]

def day(now): return datetime.fromtimestamp(now, TAIPEI).date().isoformat()

def ensure(s):
    e=s.setdefault('ecosystem',{})
    for k,v in dict(balance=0, ledger=[], rewards={}, days=[], receipts={}, inventory={'berry':3}, equipped={}, mood='happy', fed=0).items():
        e.setdefault(k,v)
    e.setdefault('voice',dict(mode='raw',speed=1.22,volume=.8))
    s.setdefault('writingDrafts',{}); s.setdefault('writingSubmissions',[])
    s.setdefault('speakingSessions',[]); s.setdefault('timestampNotes',{})
    s.setdefault('exams',{}); s.setdefault('settings',dict(name='Quỳnh Anh', motion=True))
    return e

def reward(s, token, stars, label, now):
    e=ensure(s); stars=max(0,min(3,int(stars)))
    old=e['rewards'].get(token,{}).get('stars',0)
    if stars<=old: return None
    values=[0,10,20,35]; coins=values[stars]-values[old]
    row=dict(id=uuid.uuid4().hex, token=token, kind='reward', label=label, stars=stars, amount=coins, date=now)
    e['balance']+=coins; e['ledger'].append(row); e['rewards'][token]=dict(stars=stars,date=now,label=label)
    d=day(now)
    if d not in e['days']: e['days'].append(d)
    e['mood']='proud'
    return row

def sync(s,data,now):
    e=ensure(s)
    for l in data['lessons']:
        p=s['progress'].get(l['id'],{})
        if p.get('complete'):
            stars=1+(len(s['notes'].get(l['id'],'').strip())>=80)
            quizzes=[a for a in s['attempts'] if a['id']==l['id']]
            if quizzes and max(a['score']/a['total'] for a in quizzes)>=.8: stars=3
            reward(s,'lesson:'+l['id'],stars,l['title'],p.get('updated',now))
    for a in s['attempts']:
        if a['id'].startswith('reading-') or a.get('engine')=='reading-v5':
            ratio=a['score']/a['total']; stars=3 if ratio>=.85 else 2 if ratio>=.6 else 1
            reward(s,'test:'+a['id'],stars,'Luyện đề Reading',a['date'])
    reviews=s.get('vocabReviews',{}); by_day={}; day_times={}
    for wid,r in reviews.items():
        for h in r.get('history',[]):
            d=day(h['at']); by_day.setdefault(d,set()).add(wid)
            day_times[d]=max(day_times.get(d,0),h['at'])
    for d,words in by_day.items():
        n=len(words); stars=3 if n>=20 else 2 if n>=10 else 1 if n>=5 else 0
        if stars:
            # Preserve the activity date when importing earlier recorded reviews.
            when=day_times[d]
            reward(s,'vocab:'+d,stars,'Ôn '+str(n)+' từ khác nhau',when)
    return e

def summary(s,now):
    e=ensure(s); ds=set(e['days']); today=day(now); streak=0
    cursor=datetime.fromisoformat(today).date()
    if today not in ds: cursor-=timedelta(days=1)
    while cursor.isoformat() in ds: streak+=1; cursor-=timedelta(days=1)
    return dict(**e,streak=streak,today=today,todayQualified=today in ds,shop=SHOP)

def request_token(body):
    t=body.get('requestId')
    if not isinstance(t,str) or not re.fullmatch(r'[a-zA-Z0-9_-]{12,80}',t): raise ValueError('Thiếu mã giao dịch hợp lệ')
    return t

def pet_action(s,body,now):
    e=ensure(s); token=request_token(body)
    if token in e['receipts']: return e['receipts'][token]
    action=body.get('action'); iid=body.get('item'); item=next((i for i in SHOP if i['id']==iid),None)
    if action=='voice-settings':
        mode=body.get('mode'); speed=body.get('speed'); volume=body.get('volume')
        if mode not in ('raw','text') or type(speed) not in (float,int) or type(volume) not in (float,int) or not 1<=speed<=1.5 or not 0<=volume<=1:
            raise ValueError('Thiết lập giọng nói không hợp lệ')
        e['voice']=dict(mode=mode,speed=round(speed,2),volume=round(volume,2))
    elif action=='tap': e['mood']='excited'
    elif action=='rest': e['mood']='sleepy'
    elif action=='remove':
        category=body.get('category')
        if category not in ('skin','outfit','hat','decor'): raise ValueError('Loại vật phẩm không hợp lệ')
        e['equipped'].pop(category,None); e['mood']='happy'
    elif action in ('buy','use'):
        if not item: raise ValueError('Vật phẩm không tồn tại')
        count=e['inventory'].get(iid,0)
        if action=='buy':
            if count and item['category']!='food': raise ValueError('Bạn đã có vật phẩm này')
            if e['balance']<item['price']: raise ValueError('Chưa đủ xu. Học hoặc ôn từ để nhận thêm xu nhé.')
            e['balance']-=item['price']; e['inventory'][iid]=count+1
            e['ledger'].append(dict(id=token,token=token,kind='purchase',label=item['name'],amount=-item['price'],date=now))
        else:
            if count<1: raise ValueError('Vật phẩm chưa có trong kho')
            if item['category']=='food':
                e['inventory'][iid]-=1; e['fed']=now; e['mood']='excited'
            else: e['equipped'][item['category']]=iid; e['mood']='happy'
    else: raise ValueError('Thao tác không hợp lệ')
    result=dict(saved=True,balance=e['balance'],mood=e['mood'],requestId=token)
    e['receipts'][token]=result
    return result

def merge(intervals):
    out=[]
    for a,b in sorted(intervals):
        if out and a<=out[-1][1]: out[-1][1]=max(b,out[-1][1])
        else: out.append([a,b])
    return out

def online(s,body,now):
    """Union wall-clock heartbeat intervals; inactive gaps never receive credit.
    Anchor is the first explicit Online activation, NOT midnight. Re-login,
    reload and multitab use that same persisted anchor. Exactly 86,400 seconds.
    """
    o=s.setdefault('online',dict(anchor=None,cycle=0,intervals=[],tabs={},enabled=False,lastClock=0))
    now=max(now,o['lastClock']); o['lastClock']=now
    tab=body.get('tab','status')
    if not isinstance(tab,str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,80}',tab): raise ValueError('Tab không hợp lệ')
    active=body.get('active') is True
    if body.get('action')=='on':
        o['enabled']=True
        if o['anchor'] is None: o['anchor']=now
    if body.get('action')=='off': o['enabled']=False; o['tabs']={}
    if o['anchor'] is not None:
        previous=o['tabs'].get(tab)
        start=previous if previous is not None and 0<=now-previous<=35 else now
        cycle=int((now-o['anchor'])//86400); boundary=o['anchor']+cycle*86400
        if cycle!=o['cycle']:
            o['cycle']=cycle; o['intervals']=[]
        if active and o['enabled'] and now>start:
            o['intervals']=merge(o['intervals']+[[max(start,boundary),now]])
        if active and o['enabled']: o['tabs'][tab]=now
        else: o['tabs'].pop(tab,None)
        o['tabs']={k:v for k,v in o['tabs'].items() if now-v<=35}
        reset=boundary+86400
    else: reset=None
    return dict(enabled=o['enabled'],seconds=round(sum(b-a for a,b in o['intervals']),1),reset=reset,anchor=o['anchor'],serverNow=now,timezone='Asia/Taipei',activeTabs=len(o['tabs']))

def writing(s,body,now):
    ensure(s); task=body.get('task')
    if task not in ('task1','task2'): raise ValueError('Chọn Writing Task 1 hoặc Task 2')
    text=body.get('text',''); outline=body.get('outline',''); prompt=body.get('prompt','')
    if any(not isinstance(x,str) for x in (text,outline,prompt)) or len(text)>40000 or len(outline)>10000 or len(prompt)>4000: raise ValueError('Bài viết vượt giới hạn')
    d=s['writingDrafts'].get(task,{})
    if body.get('version')!=d.get('version',0): raise ValueError('Bài viết thay đổi ở tab khác; tải lại để đồng bộ.')
    words=len(re.findall(r"\b[\w]+(?:['’-][\w]+)*\b",text))
    d=dict(task=task,text=text,outline=outline,prompt=prompt,words=words,version=d.get('version',0)+1,updated=now)
    s['writingDrafts'][task]=d
    if body.get('submit'):
        minimum=150 if task=='task1' else 250
        if words<minimum: raise ValueError('Cần ít nhất '+str(minimum)+' từ để lưu một bài hoàn thành.')
        checks=body.get('checks',[])
        if not isinstance(checks,list) or any(c not in ('response','structure','vocabulary','grammar') for c in checks): raise ValueError('Checklist không hợp lệ')
        stars=1+(len(outline.strip())>=40)+(len(set(checks))==4)
        record=dict(**d,id=uuid.uuid4().hex,stars=stars,checks=checks)
        s['writingSubmissions'].append(record)
        reward(s,'writing:'+task+':'+day(now),stars,'Hoàn thành '+task.upper(),now)
        d['stars']=stars
    return d
