import pymupdf, sys
d=pymupdf.open('/mnt/user-data/uploads/-10-TM_2009_AllOK.pdf')
pn=int(sys.argv[1]); lo=int(sys.argv[2]) if len(sys.argv)>2 else 0; hi=int(sys.argv[3]) if len(sys.argv)>3 else 999
p=d[pn-1]; rows=[]
for b in p.get_text('dict')['blocks']:
    for l in b.get('lines',[]):
        txt=''.join(s['text'] for s in l['spans'])
        if not txt.strip(): continue
        s0=l['spans'][0]
        rows.append((round(l['bbox'][1]),round(l['bbox'][0]),txt,s0['font'][:20],round(s0['size'],1)))
rows.sort()
for y,x,t,f,s in rows[lo:hi]: print(f"{y:4} {x:4} {f:20} {s:4} {t[:95]!r}")
