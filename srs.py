"""Personal spaced review scheduling; ratings are self-reported, never exam scores."""
import hashlib
import math

def word_id(word):
    return hashlib.sha256((word['topic']+'\0'+word['number']+'\0'+word['term']).encode()).hexdigest()[:20]

def review(previous, rating, now):
    if rating not in ('again','hard','good','easy'):
        raise ValueError('Mức ghi nhớ không hợp lệ')
    previous=previous or {}
    ease=float(previous.get('ease',2.5)); interval=float(previous.get('interval',0))
    reps=int(previous.get('reps',0))
    if rating=='again':
        interval=10/1440; reps=0; ease=max(1.3,ease-.2)
    elif rating=='hard':
        interval=max(1,interval*1.2); ease=max(1.3,ease-.15); reps+=1
    elif rating=='good':
        interval=1 if reps==0 else 3 if reps==1 else max(1,interval*ease); reps+=1
    else:
        interval=4 if reps==0 else max(4,interval*ease*1.3); ease=min(3.5,ease+.15); reps+=1
    interval=min(365,interval)
    return dict(interval=interval,ease=ease,reps=reps,due=now+interval*86400,
                reviewed=now,version=previous.get('version',0)+1,
                history=previous.get('history',[])+[dict(at=now,rating=rating,interval=interval)])
