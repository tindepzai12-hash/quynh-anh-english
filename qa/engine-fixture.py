"""Synthetic process only; never imports the app or learner data."""
import json,os,sys,time
print(json.dumps({'ready':True}),flush=True)
for line in sys.stdin:
    r=json.loads(line)
    if r['path']=='/crash':os._exit(7)
    if r['path']=='/timeout':time.sleep(10)
    print(json.dumps({'id':r['id'],'status':200,'data':{'path':r['path'],'pid':os.getpid()}}),flush=True)
