"""Synthetic educational fixtures, never learner state. Prints no credentials."""
import sys,os,json,base64,time
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
for line in (root.parent/'.env.gemini.local').read_text(encoding='utf-8-sig').splitlines():
    if '=' in line and not line.lstrip().startswith('#'):
        k,v=line.split('=',1);os.environ[k.strip()]=v.strip().strip('"').strip("'")
import ai_tutor,listening_practice,speaking_feedback
out=[]
cases=[('coach',lambda:ai_tutor.answer({'lessons':[]},{'question':'Dựa vào dữ liệu này, mình nên học gì tiếp? Trả lời ngắn.','personal':True,'consent':True},root,state={'attempts':[dict(id='reading-1',score=6,total=10,date=time.time())]})),
 ('writing',lambda:ai_tutor.writing_feedback(dict(task='task2',prompt='Is studying in a group useful?',text='I think study in a group is useful. Students can sharing ideas and explain difficult problems together. However, some people prefer a quiet place because they can focus better. A group should have a clear goal so everyone can contribute.',consent=True))),
 ('listening',lambda:listening_practice.feedback(dict(reference='The library opens at nine on Monday.',answer='The library open at night on Monday.',consent=True))),
 ('speaking-text',lambda:speaking_feedback.feedback(dict(prompt='Describe where you study.',transcript='I like study in the library. It is quiet and I can focus on my homework. I usually go there with my friend after school.',consent=True)))]
audio=root/'qa'/'tutor-synthetic-speech.wav'
if audio.exists():cases.append(('speaking-audio',lambda:speaking_feedback.feedback(dict(prompt='Describe where you study.',audio=dict(mime='audio/wav',data=base64.b64encode(audio.read_bytes()).decode()),consent=True))))
for label,run in cases:
    start=time.time()
    try:
        r=run();out.append(dict(feature=label,ok=True,seconds=round(time.time()-start,2),result=r));print(label+': OK',flush=True)
    except Exception as e:out.append(dict(feature=label,ok=False,error=str(e)));print(label+': '+str(e),flush=True)
    (root/'qa'/'tutor-live-smoke.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
