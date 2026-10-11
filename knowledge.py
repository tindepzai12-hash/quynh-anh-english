"""Local page-cited FTS retrieval. Source excerpts are data, never instructions.

This is lexical retrieval (BM25), not a claimed vector embedding service.
No user documents leave the machine for indexing or searching.
"""
import json, re, sqlite3, unicodedata
from pathlib import Path

def source_path(base, resource):
    parts=Path(resource.get('sourcePath',resource['path'])).parts
    if 'combined_course' not in parts: return None
    return base.parent/'ielts_materials'/'text'/Path(*parts[parts.index('combined_course')+1:]).with_suffix('.txt')

def build(base,data):
    target=base/'state'/'knowledge.sqlite3'
    with sqlite3.connect(target) as db:
        db.execute('CREATE VIRTUAL TABLE IF NOT EXISTS chunks USING fts5(text, title, rid UNINDEXED, page UNINDEXED, lesson UNINDEXED, tokenize="unicode61 remove_diacritics 2")')
        db.execute('CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY, value TEXT)')
        signatures=[]; sources=[]
        for rid,r in data['resources'].items():
            if r['kind']!='PDF' or 'ANSWER' in r.get('original','').upper(): continue
            path=source_path(base,r)
            if path and path.is_file():
                signatures.append([rid,path.stat().st_mtime_ns,path.stat().st_size]); sources.append((rid,r,path))
        stamp=json.dumps(['readable-titles-v2',signatures])
        previous=db.execute('SELECT value FROM metadata WHERE key="signature"').fetchone()
        if not previous or previous[0]!=stamp:
            db.execute('DELETE FROM chunks')
            for rid,r,path in sources:
                owners=[l for l in data['lessons'] if rid in l['resources']+l.get('related',[])]
                lid=' '.join(l['id'] for l in owners)
                test=next((t for t in data['tests'] if t['paper']==rid),None)
                title=(r['title']+' · '+owners[0]['title']) if owners else test['title'] if test else r['title']
                parts=re.split(r'===== PAGE (\d+) =====',path.read_text(encoding='utf-8'))
                for i in range(1,len(parts),2):
                    page=int(parts[i]); text=parts[i+1].strip()
                    text=re.sub(r'© The British Council 2012\. All rights reserved\.\s*\d+','',text)
                    for start in range(0,len(text),1400):
                        chunk=text[max(0,start-160):start+1400].strip()
                        if len(chunk)>50:
                            db.execute('INSERT INTO chunks VALUES(?,?,?,?,?)',(chunk,title,rid,page,lid))
            db.execute('INSERT OR REPLACE INTO metadata VALUES("signature",?)',(stamp,))
    return target

def stats(path):
    with sqlite3.connect(path) as db:
        n,docs=db.execute('SELECT count(*),count(distinct rid) FROM chunks').fetchone()
    return dict(chunks=n,documents=docs,method='SQLite FTS5 / BM25',local=True)

def retrieve(path,query,lesson=None,limit=5):
    if not isinstance(query,str) or not 1<=len(query.strip())<=2000: raise ValueError('Nhập nội dung cần tìm (tối đa 2.000 ký tự)')
    tokens=re.findall(r'[^\W_]+',query,flags=re.UNICODE)
    stop={'the','a','an','to','of','and','in','is','what','how','giải','thích','tôi','mình','là','cách','bài','hãy','cho'}
    tokens=[t for t in tokens if t.casefold() not in stop][:20]
    if not tokens: return []
    expr=' OR '.join('"'+t+'"' for t in tokens)
    sql='SELECT text,title,rid,page,lesson FROM chunks WHERE chunks MATCH ?'
    args=[expr]
    if lesson: sql+=' AND instr(lesson,?)>0'; args.append(lesson)
    sql+=' ORDER BY bm25(chunks) LIMIT ?'; args.append(limit)
    with sqlite3.connect(path) as db: rows=db.execute(sql,args).fetchall()
    return [dict(text=t,title=title,id=rid,page=int(page),lesson=lid) for t,title,rid,page,lid in rows]

def overview(path,lesson):
    with sqlite3.connect(path) as db:
        rows=db.execute('SELECT text,title,rid,page FROM chunks WHERE instr(lesson,?)>0 ORDER BY CAST(page AS INTEGER) LIMIT 6',(lesson,)).fetchall()
    return [dict(text=text[:1400],title=title,id=rid,page=int(page)) for text,title,rid,page in rows]
