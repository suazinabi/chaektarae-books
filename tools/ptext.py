import sys,json,re
from html.parser import HTMLParser
VOID={'br','img','meta','link','hr','input','wbr','source'}
class P(HTMLParser):
    def __init__(s):
        super().__init__();s.ps=[];s.cur=None;s.stack=[];s.on=False
    def skipping(s):return any(x for _,x in s.stack)
    def handle_starttag(s,t,a):
        a=dict(a);c=a.get('class') or ''
        if t=='div' and 'mw-parser-output' in c:s.on=True
        if t=='br' and s.cur is not None:s.cur.append(' ')
        if t in VOID:return
        sk=t in('style','script','sup') or 'pagenum' in c or 'ws-noexport' in c
        s.stack.append((t,sk))
        if t=='p' and s.on:s.cur=[]
    def handle_endtag(s,t):
        if t in VOID:return
        while s.stack:
            x,_=s.stack.pop()
            if x==t:break
        if t=='p' and s.cur is not None:
            y=re.sub(r'\s+',' ',''.join(s.cur)).strip()
            if y:s.ps.append(y)
            s.cur=None
    def handle_data(s,d):
        if s.cur is not None and not s.skipping():s.cur.append(d)
p=P();p.feed(open(sys.argv[1]).read());json.dump(p.ps,open(sys.argv[2],'w'),ensure_ascii=False)
