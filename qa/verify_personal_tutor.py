import sys,json,base64,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import tutor_profile,ai_tutor,speaking_feedback,ai_provider

class TutorTests(unittest.TestCase):
    def test_no_data_no_fake_scores(self):
        p=tutor_profile.profile({},100);self.assertEqual(p['recentTests'],[]);self.assertEqual(p['speakingSavedSessions'],0)
    def test_profile_minimal_and_real(self):
        p=tutor_profile.profile(dict(email='private',notes={'a':'secret'},writingDrafts={'a':'essay'},progress={'a':{}},attempts=[dict(id='reading-1',score=8,total=10,date=50),dict(id='bad',score=11,total=10)],vocabReviews={'a':dict(due=80)}),100)
        self.assertEqual(p['recentTests'][0]['correct'],8);self.assertEqual(len(p['recentTests']),1);self.assertEqual(p['vocabulary']['dueCards'],1)
        self.assertNotIn('private',json.dumps(p));self.assertNotIn('secret',json.dumps(p));self.assertNotIn('essay',json.dumps(p))
    def test_consent_required(self):
        with patch('ai_tutor.configured',return_value=True),self.assertRaises(ValueError):ai_tutor.answer({'lessons':[]},{'question':'Hi','personal':True},Path('.'),state={})
    def test_client_cannot_spoof_profile_and_no_source_can_coach(self):
        with patch('ai_tutor.configured',return_value=True),patch('tutor_knowledge.study_sources',return_value=[]),patch('ai_provider.generate',return_value='ok') as generate:
            r=ai_tutor.answer({'lessons':[]},{'question':'help','personal':True,'consent':True,'profile':{'fake':999}},Path('.'),state={'attempts':[dict(id='reading-1',score=4,total=10)]})
            prompt=generate.call_args.args[0];self.assertNotIn('999',prompt);self.assertIn('"correct": 4',prompt);self.assertTrue(r['personal'])
    def test_ordinary_chat_does_not_get_profile(self):
        with patch('ai_tutor.configured',return_value=True),patch('tutor_knowledge.study_sources',return_value=[]),patch('ai_provider.generate',return_value='ok') as generate:
            ai_tutor.answer({'lessons':[]},{'question':'help','history':[dict(role='user',content='past')]},Path('.'),state={'attempts':[dict(id='reading-1',score=4,total=10)]})
            self.assertNotIn('"correct": 4',generate.call_args.args[0]);self.assertEqual(generate.call_args.args[1][0]['content'],'past')
    def test_speaking_requires_consent(self):
        with self.assertRaises(ValueError):speaking_feedback.validate({'transcript':'a'*50})
    def test_bad_audio_and_size(self):
        for audio in [dict(mime='text/html',data='a'),dict(mime='audio/wav',data='invalid'),dict(mime='audio/wav',data=base64.b64encode(b'no'*40).decode()),dict(mime='audio/wav',data='a'*8388609)]:
            with self.assertRaises(ValueError):speaking_feedback.validate(dict(consent=True,audio=audio))
    def test_text_feedback_no_pronunciation_band(self):
        with patch('ai_provider.generate',return_value='ok') as generate:
            r=speaking_feedback.feedback(dict(consent=True,transcript='I like studying in the library because it is quiet.'))
            self.assertEqual(r['inputMode'],'text');self.assertIsNone(r['band']);self.assertIsNone(generate.call_args.kwargs['audio'])
    def test_audio_envelope(self):
        audio=dict(mime='audio/wav',data=base64.b64encode(b'RIFF0000WAVE'+b'\0'*100).decode())
        with patch('ai_provider.generate',return_value='ok') as generate:
            r=speaking_feedback.feedback(dict(consent=True,audio=audio));self.assertEqual(r['inputMode'],'audio');self.assertEqual(generate.call_args.kwargs['audio'],audio)
    def test_other_provider_never_receives_audio(self):
        with patch('ai_provider.status',return_value=dict(configured=True,provider='openai',model='x')),self.assertRaises(ValueError):ai_provider.generate('x',[dict(role='user',content='x')],audio={'mime':'audio/wav','data':'x'})

if __name__=='__main__':unittest.main()
