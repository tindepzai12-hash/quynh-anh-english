import copy,io,json,sys,tempfile,unittest,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import reading_engine as r,reading_import as imp
from reading_v5_fixture import seed

class Focus(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.store=r.Store(Path(self.temp.name)/'qa-focus.sqlite3');d=seed(self.store.path);self.s={};self.e=r.start(self.s,self.store,{'id':d['id'],'contentVersion':d['version'],'mode':'guided'},100)
 def tearDown(self):self.temp.cleanup()
 def body(self):
  e=self.e;return dict(session=e['id'],version=e['version'],contentVersion=e['contentVersion'],answers=e['answers'],flags=e['flags'],focus=e['focus'],highlights=e['highlights'])
 def test_preferences_notes_persist_and_validation_is_atomic(self):
  p=self.store.get(self.e['test'],self.e['contentVersion'])['passages'][0]['id'];b=self.body();b.update(notes={p:'My evidence'},preferences={'fontSize':20,'split':65});r.draft(self.s,self.store,b,110)
  self.assertEqual(self.e['notes'][p],'My evidence');self.assertEqual(self.e['preferences']['fontSize'],20)
  for bad in ({'fontSize':17},{'split':66},{'fontSize':True},{'unknown':2}):
   before=copy.deepcopy(self.e)
   with self.assertRaises(ValueError):r.draft(self.s,self.store,dict(self.body(),preferences=bad),112)
   self.assertEqual(before,self.e)
  with self.assertRaises(ValueError):r.draft(self.s,self.store,dict(self.body(),notes={'alien':'x'}),112)
 def test_pause_resume_locks_mutations_and_is_versioned(self):
  r.pause(self.s,dict(session=self.e['id'],version=0,paused=True),110)
  with self.assertRaises(ValueError):r.draft(self.s,self.store,self.body(),120)
  with self.assertRaises(ValueError):r.submit(self.s,self.store,dict(session=self.e['id'],version=self.e['version']),120)
  with self.assertRaises(ValueError):r.pause(self.s,dict(session=self.e['id'],version=0,paused=False),120)
  r.pause(self.s,dict(session=self.e['id'],version=1,paused=False),140);self.assertEqual(self.e['pausedSeconds'],30)
  r.draft(self.s,self.store,self.body(),141);self.assertEqual(self.e['version'],3)
 def test_exam_cannot_pause_or_extend_deadline(self):
  self.e['mode']='exam';deadline=self.e['deadline']
  with self.assertRaises(ValueError):r.pause(self.s,dict(session=self.e['id'],version=0,paused=True),110)
  self.assertEqual(self.e['deadline'],deadline)
 def test_malformed_annotations_are_rejected(self):
  for bad in ([None],[{'block':[]}],[{'block':'b1','start':True,'end':3}]):
   with self.assertRaises(ValueError):r.draft(self.s,self.store,dict(self.body(),highlights=bad),110)
  doc=self.store.get(self.e['test'],self.e['contentVersion']);q=next(q for q in doc['questions'] if q['type']=='multiple')
  with self.assertRaises(ValueError):r.draft(self.s,self.store,dict(self.body(),answers={q['id']:[{}]}),110)
 def test_import_retains_paragraph_table_order_and_missing_key(self):
  raw=b'<h1>Title</h1><p>First paragraph.</p><table><tr><td>A</td><td>B</td></tr></table><p>Second paragraph.</p><p>Question 1: What?</p>'
  d=imp.candidate(raw,'own.html',{})
  self.assertEqual([b['type'] for b in d['passages'][0]['blocks']],['heading','paragraph','table','paragraph'])
  self.assertEqual(d['questions'][0]['key']['accepted'],[])
  self.assertEqual(d['questions'][0]['key']['status'],'UNVERIFIED')
 def test_docx_breaks_and_cell_paragraphs(self):
  raw=io.BytesIO()
  with zipfile.ZipFile(raw,'w') as z:z.writestr('word/document.xml','<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Hello</w:t><w:br/><w:t>world</w:t></w:r></w:p><w:tbl><w:tr><w:tc><w:p><w:r><w:t>First</w:t></w:r></w:p><w:p><w:r><w:t>Second</w:t></w:r></w:p></w:tc></w:tr></w:tbl></w:body></w:document>')
  d=imp.extract(raw.getvalue(),'own.docx');self.assertEqual(d['blocks'][0]['text'],'Hello\nworld');self.assertEqual(d['blocks'][1]['rows'][0][0],'First\nSecond')

if __name__=='__main__':unittest.main()
