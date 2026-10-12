"""Small, account-owned coaching context. Never accepts a profile from the client."""
import time

def profile(state, now=None):
    now=now or time.time()
    attempts=[]
    for a in state.get('attempts',[])[-100:]:
        score,total=a.get('score'),a.get('total')
        if type(score) not in (int,float) or type(total) not in (int,float) or not 0<=score<=total or total<=0:continue
        attempts.append(dict(skill='reading' if a.get('engine')=='reading-v5' or str(a.get('id','')).startswith('reading-') else 'lesson_quiz',date=a.get('date'),correct=score,total=total))
    reviews=list(state.get('vocabReviews',{}).values())
    result=dict(observedAt=now,lessonProgressCount=len(state.get('progress',{})),recentTests=attempts[-8:],
        vocabulary=dict(reviewedCards=len(reviews),dueCards=sum(isinstance(r.get('due'),(int,float)) and r['due']<=now for r in reviews)),
        speakingSavedSessions=len(state.get('speakingSessions',[])),writingFeedbackCount=len(state.get('writingFeedback',[])),
        listeningRecent=[dict(date=r.get('date'),accuracy=r.get('accuracy')) for r in state.get('listeningFeedback',[])[-5:]],
        evidenceLimits=['Progress is activity, not proficiency. Vocabulary ratings are self-reported.',
          'Listening accuracy compares written dictation with a supplied reference, not a standardized IELTS score.',
          'Repeated tests are not independent samples. No IELTS band or pronunciation score can be inferred.'])
    # Only already-generated feedback, never original essays, notes, names or email.
    result['recentAIFeedback']=[dict(skill=skill,feedback=str(r.get('text',''))[:1200]) for skill,key in
        [('writing','writingFeedback'),('speaking','speakingFeedback')] for r in state.get(key,[])[-2:]]
    return result
