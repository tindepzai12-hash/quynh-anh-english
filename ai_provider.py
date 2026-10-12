"""Server-only AI adapters. No keys or upstream error bodies reach the browser."""
import json, os, re, urllib.request, urllib.error

def status():
    provider=os.environ.get('AI_PROVIDER','openai' if os.environ.get('OPENAI_API_KEY') and not os.environ.get('GEMINI_API_KEY') else 'gemini').lower()
    key=os.environ.get('GEMINI_API_KEY' if provider=='gemini' else 'OPENAI_API_KEY')
    model=os.environ.get('GEMINI_MODEL' if provider=='gemini' else 'OPENAI_MODEL','')
    return dict(configured=provider in ('gemini','openai') and bool(key and re.fullmatch(r'[A-Za-z0-9._-]{1,100}',model)),provider=provider if provider in ('gemini','openai') else None,model=model if re.fullmatch(r'[A-Za-z0-9._-]{1,100}',model) else None)

def generate(instruction,messages,timeout=60):
    s=status()
    if not s['configured']: raise ValueError('AI chưa kết nối. Cần API key và model được cấu hình riêng trên máy chủ.')
    if s['provider']=='gemini':
        contents=[dict(role='model' if m['role']=='assistant' else 'user',parts=[dict(text=m['content'])]) for m in messages]
        payload=dict(systemInstruction=dict(parts=[dict(text=instruction)]),contents=contents,generationConfig=dict(maxOutputTokens=4096,temperature=.25))
        url='https://generativelanguage.googleapis.com/v1beta/models/'+s['model']+':generateContent'
        headers={'x-goog-api-key':os.environ['GEMINI_API_KEY'],'Content-Type':'application/json'}
    else:
        payload=dict(model=s['model'],instructions=instruction,input=messages,store=False,max_output_tokens=1800)
        url='https://api.openai.com/v1/responses'
        headers={'Authorization':'Bearer '+os.environ['OPENAI_API_KEY'],'Content-Type':'application/json'}
    request=urllib.request.Request(url,data=json.dumps(payload).encode(),headers=headers,method='POST')
    try:
        with urllib.request.urlopen(request,timeout=timeout) as response:
            raw=response.read(2_000_001)
            if len(raw)>2_000_000: raise ValueError('Phản hồi AI vượt giới hạn. Hãy thử lại với nội dung ngắn hơn.')
            result=json.loads(raw)
    except urllib.error.HTTPError as error:
        if error.code==429:raise ValueError('AI đã hết hạn mức hiện tại. Thử lại sau hoặc kiểm tra quota trên Google AI Studio; bài làm vẫn được giữ.') from None
        if error.code in (500,502,503,504):raise ValueError('Dịch vụ AI đang quá tải hoặc gián đoạn. Hãy thử lại sau; bài làm vẫn được giữ.') from None
        raise ValueError('Không gọi được AI (HTTP '+str(error.code)+'). Kiểm tra model, API key và hạn mức máy chủ.') from None
    except (urllib.error.URLError,TimeoutError): raise ValueError('Kết nối AI bị gián đoạn. Nội dung bạn đang viết vẫn được giữ.') from None
    except (json.JSONDecodeError,UnicodeError): raise ValueError('AI trả về dữ liệu không hợp lệ.') from None
    if not isinstance(result,dict):raise ValueError('AI trả về dữ liệu không hợp lệ.')
    if s['provider']=='gemini':
        candidates=result.get('candidates',[])
        if not candidates:raise ValueError('Gemini chưa trả về nhận xét; yêu cầu có thể bị chặn hoặc hết hạn mức.')
        if candidates[0].get('finishReason') not in (None,'STOP'):raise ValueError('Gemini chưa hoàn thành nhận xét. Hãy thử lại với bài ngắn hơn.')
        text='\n'.join(p['text'] for p in candidates[0].get('content',{}).get('parts',[]) if isinstance(p.get('text'),str) and not p.get('thought'))
    else:
        text='\n'.join(p['text'] for i in result.get('output',[]) if i.get('type')=='message' for p in i.get('content',[]) if p.get('type')=='output_text' and isinstance(p.get('text'),str))
    if not text.strip():raise ValueError('AI chưa trả lời dạng văn bản. Hãy thử lại.')
    return text
