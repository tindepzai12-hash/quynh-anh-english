"""Private, serialized stdio adapter: reuse the existing learning engine.

Each request restores only the server-owned account state into scratch SQLite.
No network listener, no public source paths, no real learner database writes.
"""
import io, json, os, sqlite3, sys, tempfile, traceback
from pathlib import Path
from contextlib import closing
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
scratch=tempfile.TemporaryDirectory(prefix='quynh-anh-engine-')
os.environ['OCEAN_DB']=str(Path(scratch.name)/'learning.sqlite3')
os.environ.pop('OCEAN_EDITOR_TOKEN',None)
import server
from types import SimpleNamespace
seed=ROOT/'deploy'/'reading-seed.json'
if seed.is_file():
    with server.READING.connect() as db:
        for row in json.loads(seed.read_text(encoding='utf-8')):
            db.execute('INSERT OR IGNORE INTO reading_content(id,version,status,body,issues,updated) VALUES(?,?,?,?,?,?)',row)

class Request(server.Handler):
    def reply(self,data,status=200): self.result=dict(status=status,data=data)
    def send_file(self,*a,**kw): self.reply({'error':'Tài liệu này chỉ có trong thư viện trên laptop.'},404)

def execute(message):
    route=message['path']
    if not route.startswith('/api/') or route.startswith('/api/reading-admin/'):
        return dict(status=403,data={'error':'Không có quyền truy cập.'},state=message['state'])
    with closing(sqlite3.connect(server.DB)) as db, db:
        db.execute('UPDATE state SET body=? WHERE id=1',(json.dumps(message['state'],ensure_ascii=False),))
    request=object.__new__(Request)
    request.server=SimpleNamespace(server_port=8765)
    body=json.dumps(message.get('body',{})).encode()
    request.path=route
    request.headers={'Host':'127.0.0.1:8765','Content-Length':str(len(body))}
    request.rfile=io.BytesIO(body)
    request.result=None
    if message['method']=='GET': request.do_GET()
    else: request.do_POST()
    with closing(sqlite3.connect(server.DB)) as db:
        state=json.loads(db.execute('SELECT body FROM state WHERE id=1').fetchone()[0])
    return dict(**request.result,state=state)

print(json.dumps({'ready':True}),flush=True)
for line in sys.stdin:
    try:
        message=json.loads(line)
        response=execute(message)
        print(json.dumps(dict(id=message['id'],**response),ensure_ascii=False),flush=True)
    except Exception:
        # No request data, token, paths or answers in logs/client errors.
        print(json.dumps(dict(id=message.get('id'),status=500,data={'error':'Không xử lý được yêu cầu học. Dữ liệu cũ vẫn được giữ.'})),flush=True)
