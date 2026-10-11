"""Timed Reading runs, persistent sessions and idempotent submissions."""
import uuid
import writing_exams
import reading_engine

def active(s,now):
    return writing_exams.active(s,now) + reading_engine.active(s,now)

def start(s,test,mode,now):
    if mode not in ('guided','exam'): raise ValueError('Chế độ không hợp lệ')
    sessions=s.setdefault('exams',{})
    existing=next((e for e in sessions.values() if e['test']==test['id'] and not e.get('submitted')),None)
    if existing: return existing
    if active(s,now): raise ValueError('Hãy nộp bài thi đang làm trước khi mở bài khác.')
    e=dict(id=uuid.uuid4().hex,test=test['id'],mode=mode,started=now,deadline=now+3600,answers=['']*40,version=0,submitted=False,flags=[],focus=0)
    sessions[e['id']]=e
    return e

def get(s,body):
    e=s.get('exams',{}).get(body.get('session'))
    if not e: raise ValueError('Phiên luyện đề không tồn tại')
    return e

def draft(s,body,now):
    e=get(s,body)
    if e['submitted']: raise ValueError('Bài đã nộp')
    if e['mode']=='exam' and now>=e['deadline']: raise ValueError('Đã hết giờ. Bài đã lưu được dùng để chấm điểm.')
    if body.get('version')!=e['version']: raise ValueError('Bài đã thay đổi ở tab khác. Tải lại để đồng bộ.')
    answers=body.get('answers')
    if not isinstance(answers,list) or len(answers)!=40 or any(not isinstance(a,str) or len(a)>500 for a in answers): raise ValueError('Cần 40 câu trả lời hợp lệ')
    flags=body.get('flags',[])
    if not isinstance(flags,list) or any(type(i) is not int or i not in range(40) for i in flags): raise ValueError('Câu đánh dấu không hợp lệ')
    focus=body.get('focus',0)
    if type(focus) is not int or focus not in range(40): raise ValueError('Vị trí câu không hợp lệ')
    e.update(answers=answers,flags=sorted(set(flags)),focus=focus,version=e['version']+1,updated=now)
    return e

def submit(s,e,data,now,grade):
    if e.get('submitted'): return e['result']
    t=next(t for t in data['tests'] if t['id']==e['test'])
    correct=grade(e['answers'],t['answers'],t['groups'])
    result=dict(id=t['id'],session=e['id'],mode=e['mode'],date=now,score=sum(correct),total=40,answers=list(e['answers']),correct=correct,key=t['answers'],explanations=[],expired=e['mode']=='exam' and now>=e['deadline'])
    s['attempts'].append(result); e.update(submitted=True,result=result)
    return result

def expire(s,data,now,grade):
    writing_exams.expire(s,now)
    for e in s.get('exams',{}).values():
        if not e['submitted']:e['needsContentReview']=True
