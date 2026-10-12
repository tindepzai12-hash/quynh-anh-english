import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import listening_practice as p
class Listening(unittest.TestCase):
 def test_versioned_draft_and_atomic_conflict(self):
  s={};body=dict(version=0,reference='Hello world.',answer='hello',sourceKind='file',sourceName='my.wav',sample=0)
  d=p.draft(s,body,100);self.assertEqual(d['version'],1);self.assertNotIn('audio',d);before=copy.deepcopy(s)
  with self.assertRaises(ValueError):p.draft(s,body,101)
  self.assertEqual(s,before)
  for change in ({'answer':'x'*5001},{'sourceKind':'remote'},{'sample':True}):
   with self.assertRaises(ValueError):p.draft(s,dict(body,version=1,**change),102)
   self.assertEqual(s,before)
 def test_attempt_score_recomputed_and_history_bounded(self):
  s={}
  for i in range(52):r=p.attempt(s,dict(reference='Hello world.',answer='hello',accuracy=100),i)
  self.assertEqual(r['result']['accuracy'],50);self.assertEqual(len(s['listeningAttempts']),50);self.assertEqual(s['listeningAttempts'][0]['date'],2)
if __name__=='__main__':unittest.main()
