import csv, sys, collections
def lines(path):
    rows=list(csv.DictReader(open(path, encoding='utf8'), delimiter='\t', quoting=csv.QUOTE_NONE))
    g=collections.OrderedDict()
    for r in rows:
        if r['level']!='5' or not r['text'].strip(): continue
        k=(int(r['block_num']),int(r['par_num']),int(r['line_num']))
        g.setdefault(k,[]).append(r)
    out=[]
    for k,ws in g.items():
        x=int(ws[0]['left']); y=min(int(w['top']) for w in ws); h=max(int(w['height']) for w in ws)
        conf=sum(float(w['conf']) for w in ws)/len(ws)
        out.append({'x':x,'y':y,'h':h,'conf':round(conf),'text':' '.join(w['text'] for w in ws),'words':[(int(w['left']),int(w['top']),int(w['width']),int(w['height']),w['text']) for w in ws]})
    out.sort(key=lambda r:(r['y'],r['x']))
    return out
if __name__=='__main__':
    for l in lines(sys.argv[1]): print(f"{l['y']:5} {l['x']:5} {l['h']:3} {l['conf']:3} {l['text']}")
