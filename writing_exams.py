"""Local timed Writing sessions. Completion rewards are never band scores."""
import re
import uuid
import ecosystem


def active(s, now):
    return [e for e in s.get('writingExams', {}).values()
            if not e.get('submitted') and now < e['deadline']]


def start(s, body, data, now):
    existing = active(s, now)
    if existing:
        return existing[0]
    prompts = body.get('prompts')
    if not isinstance(prompts, dict) or set(prompts) != {'task1', 'task2'}:
        raise ValueError('Cần đề cho cả Task 1 và Task 2.')
    if any(not isinstance(p, str) or not p.strip() or len(p) > 4000 for p in prompts.values()):
        raise ValueError('Mỗi đề cần 1–4.000 ký tự.')
    source = body.get('source') or None
    allowed = {rid for l in data['lessons'] if l['skill']=='Writing Task 1' for rid in l['resources']
               if data['resources'][rid]['kind']=='PDF'}
    if source and source not in allowed:
        raise ValueError('Chọn PDF trong học liệu để xem biểu đồ Task 1.')
    e = dict(id=uuid.uuid4().hex, kind='writing', mode='exam', started=now,
             deadline=now+3600, prompts=prompts, source=source,
             texts={'task1': '', 'task2': ''}, focus='task1', version=0, submitted=False)
    s.setdefault('writingExams', {})[e['id']] = e
    return e


def get(s, body):
    e = s.get('writingExams', {}).get(body.get('session'))
    if not e:
        raise ValueError('Phiên Writing không tồn tại.')
    return e


def draft(s, body, now):
    e = get(s, body)
    if e['submitted'] or now >= e['deadline']:
        raise ValueError('Phiên đã kết thúc; bài đã lưu được giữ trong kết quả.')
    if body.get('version') != e['version']:
        raise ValueError('Bài đã thay đổi ở tab khác. Tải lại để đồng bộ.')
    texts = body.get('texts')
    if not isinstance(texts, dict) or set(texts) != {'task1', 'task2'} or any(
            not isinstance(t, str) or len(t) > 40000 for t in texts.values()):
        raise ValueError('Nội dung Writing không hợp lệ.')
    focus = body.get('focus', 'task1')
    if focus not in ('task1', 'task2'):
        raise ValueError('Chọn Task 1 hoặc Task 2.')
    e.update(texts=texts, focus=focus, updated=now, version=e['version']+1)
    return e


def submit(s, e, now):
    if e['submitted']:
        return e['result']
    words = {task: len(re.findall(r"\b[\w]+(?:['’-][\w]+)*\b", text))
             for task, text in e['texts'].items()}
    complete = {task: words[task] >= minimum for task, minimum in [('task1', 150), ('task2', 250)]}
    result = dict(session=e['id'], prompts=e['prompts'], texts=dict(e['texts']), source=e['source'],
                  words=words, complete=complete, date=now, expired=now >= e['deadline'])
    e.update(submitted=True, result=result)
    for task in ('task1', 'task2'):
        ecosystem.reward(s, 'writing:'+task+':'+ecosystem.day(now), int(complete[task]),
                         'Hoàn thành '+task.upper(), now)
    return result


def expire(s, now):
    for e in s.get('writingExams', {}).values():
        if not e['submitted'] and now >= e['deadline']:
            submit(s, e, now)
