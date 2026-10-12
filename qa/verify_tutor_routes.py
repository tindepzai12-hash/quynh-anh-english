import os,sys,io,runpy,json,time,unittest
from pathlib import Path
from contextlib import redirect_stdout
from unittest.mock import patch
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
os.environ['OCEAN_CATALOG']=str(root/'deploy/catalog.json')
os.environ['OCEAN_READING_DB']=str(root/'state/qa-tutor-route-reading.sqlite3')
with redirect_stdout(io.StringIO()),patch('sys.stdin',io.StringIO('')):bridge=runpy.run_path(str(root/'node/bridge.py'))
execute=bridge['execute']
def call(path,state,body):return execute(dict(path=path,method='POST',state=state,body=body))
def fresh():return dict(progress={},notes={},attempts=[],known=[],plan=None)
class RouteTests(unittest.TestCase):
    def test_profile_account_isolation(self):
        with patch('ai_tutor.configured',return_value=True),patch('ai_provider.generate',return_value='ok') as generate:
            a=fresh();a['attempts']=[dict(id='reading-1',score=7,total=10)]
            self.assertEqual(call('/api/tutor',a,dict(question='help',personal=True,consent=True))['status'],200)
            self.assertIn('"correct": 7',generate.call_args.args[0])
            b=call('/api/tutor',fresh(),dict(question='help',personal=True,consent=True))
            self.assertNotIn('"correct": 7',generate.call_args.args[0]);self.assertEqual(len(b['state']['chatHistory']),1)
    def test_speaking_saved_without_raw_audio(self):
        with patch('ai_provider.generate',return_value='sample feedback'):
            r=call('/api/speaking-feedback',fresh(),dict(consent=True,transcript='I like studying in a quiet room after school.'))
            self.assertEqual(r['status'],200);self.assertEqual(r['state']['speakingFeedback'][0]['inputMode'],'text');self.assertNotIn('transcript',r['state']['speakingFeedback'][0])
    def test_exam_blocks_every_ai(self):
        for path in ['/api/tutor','/api/speaking-feedback','/api/listening-feedback','/api/writing-feedback']:
            s=fresh();s['writingExams']={'test':dict(submitted=False,deadline=time.time()+600)}
            with patch('ai_provider.generate') as generate:
                self.assertEqual(call(path,s,{})['status'],403);generate.assert_not_called()
    def test_invalid_consent_does_not_save(self):
        r=call('/api/speaking-feedback',fresh(),dict(transcript='I like studying in a quiet room after school.'))
        self.assertEqual(r['status'],400);self.assertEqual(r['state'].get('speakingFeedback',[]),[])
if __name__=='__main__':unittest.main()
