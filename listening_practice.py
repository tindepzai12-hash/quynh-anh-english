"""Reference-based dictation comparison; AI explains, never changes the score."""
import re,unicodedata,json
import ai_provider, tutor_knowledge

def draft(state,body,now):
    old=state.get('listeningDraft',{})
    if body.get('version')!=old.get('version',0):raise ValueError('Bản nghe đã đổi ở tab khác. Bản của bạn giữ trên thiết bị; tải lại để đối chiếu.')
    if body.get('sourceKind') not in ('sample','file'):raise ValueError('Nguồn nghe không hợp lệ.')
    for field,limit in (('reference',5000),('answer',5000),('sourceName',200)):
        if not isinstance(body.get(field),str) or len(body[field])>limit:raise ValueError('Nội dung bản nháp nghe vượt giới hạn.')
    sample=body.get('sample',0)
    if type(sample)is not int or not 0<=sample<=2:raise ValueError('Câu mẫu không hợp lệ.')
    result={key:body[key] for key in ('reference','answer','sourceKind','sourceName')}
    result.update(sample=sample,version=old.get('version',0)+1,updated=now)
    state['listeningDraft']=result;return result

def attempt(state,body,now):
    # Recompute comparison on the server; client percentages are never trusted.
    result=check(body)
    import uuid
    rec=dict(id=uuid.uuid4().hex,date=now,reference=body['reference'],answer=body['answer'],result=result)
    history=state.setdefault('listeningAttempts',[]);history.append(rec);state['listeningAttempts']=history[-50:]
    return rec

def tokens(text):
    text=unicodedata.normalize('NFKC',text).lower().replace('’',"'")
    return re.findall(r"[\w]+(?:'[\w]+)*",text)

def check(body):
    reference=body.get('reference');answer=body.get('answer')
    if not isinstance(reference,str) or not isinstance(answer,str) or not 1<=len(reference)<=5000 or len(answer)>5000:raise ValueError('Transcript và câu trả lời cần dưới 5.000 ký tự.')
    expected=tokens(reference);actual=tokens(answer)
    if not expected:raise ValueError('Transcript cần có từ để đối chiếu.')
    if max(len(expected),len(actual))>350:raise ValueError('Mỗi lượt nghe chép tối đa 350 từ. Hãy chia audio thành đoạn ngắn.')
    # Levenshtein alignment counts substitutions, omissions and inserted words.
    grid=[[0]*(len(actual)+1) for _ in range(len(expected)+1)]
    for i in range(len(expected)+1):grid[i][0]=i
    for j in range(len(actual)+1):grid[0][j]=j
    for i,a in enumerate(expected,1):
        for j,b in enumerate(actual,1):grid[i][j]=min(grid[i-1][j]+1,grid[i][j-1]+1,grid[i-1][j-1]+(a!=b))
    edits=[];i=len(expected);j=len(actual)
    while i or j:
        if i and j and grid[i][j]==grid[i-1][j-1]+(expected[i-1]!=actual[j-1]):
            edits.append(dict(kind='correct' if expected[i-1]==actual[j-1] else 'replace',expected=expected[i-1],actual=actual[j-1]));i-=1;j-=1
        elif i and grid[i][j]==grid[i-1][j]+1:edits.append(dict(kind='missing',expected=expected[i-1],actual=''));i-=1
        else:edits.append(dict(kind='extra',expected='',actual=actual[j-1]));j-=1
    edits.reverse();errors=grid[-1][-1]
    return dict(accuracy=round(max(0,1-errors/len(expected))*100),errors=errors,referenceWords=len(expected),exact=expected==actual,edits=edits,method='Đối chiếu từ với transcript bạn cung cấp; bỏ qua hoa/thường và dấu câu. Không quy đổi band IELTS.')

def feedback(body):
    result=check(body)
    if body.get('consent') is not True:raise ValueError('Cần xác nhận gửi câu trả lời và transcript tới nhà cung cấp AI.')
    instruction=tutor_knowledge.guide('listening')
    text=ai_provider.generate(instruction,[dict(role='user',content=json.dumps(dict(reference=body['reference'],answer=body['answer'],comparison=result),ensure_ascii=False))])
    return dict(**result,text=text,provider=ai_provider.status()['provider'])
