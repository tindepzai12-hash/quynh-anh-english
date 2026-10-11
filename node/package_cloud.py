"""Package only deployable app files. Never copy learner databases or secrets."""
import json,sqlite3,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TARGET=ROOT/'cloud-deploy'
assert (TARGET/'.git').is_dir(),'Clone the intended private deployment repo first.'
for name in ['node','public']:
    shutil.copytree(ROOT/name,TARGET/name,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__'))
for name in ['package.json','package-lock.json','server.py','ecosystem.py','exams.py','writing_exams.py','reading_engine.py','reading_import.py','ai_tutor.py','knowledge.py','srs.py','vocab-reviewed.json','vocab-pronunciation.json','.env.example']:
    shutil.copy2(ROOT/name,TARGET/name)
deploy=TARGET/'deploy';deploy.mkdir(exist_ok=True)
catalog=json.loads((ROOT/'catalog.private.json').read_text(encoding='utf-8'))
for r in catalog['resources'].values():
    for key in ['sourcePath','source','original','sourceRoot']:r.pop(key,None)
    r.update(path='',exists=False,cloudAvailable=False)
for lesson in catalog['lessons']:lesson['cloudMediaAvailable']=False
for t in catalog['tests']:t['answers']=[]
catalog['quizzes']={}
(deploy/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False),encoding='utf-8')
with sqlite3.connect(ROOT/'state'/'learning-reading-content.sqlite3') as db:
    rows=db.execute('SELECT id,version,status,body,issues,updated FROM reading_content').fetchall()
(deploy/'reading-seed.json').write_text(json.dumps(rows,ensure_ascii=False),encoding='utf-8')
(TARGET/'.gitignore').write_text('node_modules/\nstate/\n.env*\n!.env.example\n__pycache__/\npublic/assets/justin-mini/natural-v2/\n',encoding='utf-8')
(TARGET/'render.yaml').write_text('''services:
  - type: web
    name: quynh-anh-english
    runtime: node
    plan: free
    region: singapore
    buildCommand: npm ci --omit=dev && python3 --version
    startCommand: npm start
    healthCheckPath: /api/health
    envVars:
      - key: NODE_VERSION
        value: 24.19.0
      - key: SESSION_SECRET
        generateValue: true
      - key: PYTHON_BIN
        value: python3
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_ANON_KEY
        sync: false
      - key: SUPABASE_SERVICE_ROLE_KEY
        sync: false
''',encoding='utf-8')
(TARGET/'README.md').write_text('''# Quỳnh Anh English

Node.js web server, managed Supabase accounts and durable learning state.
The existing Python learning engine runs as a private serialized child process.
Deploy on Render **Free**, Node.js runtime. Build: `npm ci --omit=dev && python3 --version`. Start: `npm start`.
Set SESSION_SECRET (32+ chars), SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY privately on Render.
Run `node/schema.sql` in your Supabase SQL editor. No service key is exposed to the browser.
Configure Auth redirect allowlist for `/auth/callback` on the Render URL and localhost.
Enable Google/Facebook only after configuring real provider credentials in Supabase.

Original course videos/PDFs, personal progress, administrator keys, logs and Blender tools are excluded.
Without account configuration the online app is a read-only preview, never a fake saving session.
Course media remains on the laptop. Speaking recordings currently remain in browser IndexedDB.
The cloud service uses Node.js for HTTP/accounts/storage and Python for existing IELTS business logic.
Free services can sleep; free infrastructure is not a substitute for backups or an uptime guarantee.
''',encoding='utf-8')
print(json.dumps({'packaged':str(TARGET),'files':sum(1 for p in TARGET.rglob('*') if p.is_file() and '.git' not in p.parts),'personalProgressIncluded':False,'secretsIncluded':False}))
