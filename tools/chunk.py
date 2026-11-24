import re,sys,json

def sents(p):
    out=[];cur='';depth=0
    for i,ch in enumerate(p):
        cur+=ch
        if ch in '“':depth+=1
        elif ch in '”':depth=max(0,depth-1)
        nxt=p[i+1] if i+1<len(p) else ''
        if depth==0 and ch in '.!?…”' and nxt==' ':
            if ch=='”' or cur.rstrip()[-1] in '.!?…':
                out.append(cur.strip());cur=''
    if cur.strip():out.append(cur.strip())
    res=[]
    for x in out:
        if res and len(x)<6:res[-1]+=' '+x
        else:res.append(x)
    return res
def pieces(paras,maxlen=210):
    out=[]  # list of (para_idx, text, para_start)
    for i,p in enumerate(paras):
        if len(p)<=maxlen: out.append([i,p,True]);continue
        cur='';first=True
        for s in sents(p):
            if cur and len(cur)+1+len(s)>maxlen:
                out.append([i,cur,first]);first=False;cur=s
            else: cur=(cur+' '+s).strip()
        if cur: out.append([i,cur,first])
    return out
def chunk(paras,maxlen=215,minlen=75,breaks=()):
    ps=pieces(paras)
    chunks=[];cur=None
    for k,(i,t,start) in enumerate(ps):
        sep='\n' if start else ' '
        force=any(t.startswith(b) for b in breaks)
        if cur is None: cur=t
        elif not force and (len(cur)<minlen or len(cur)+len(t)+1<=maxlen and (len(t)<minlen or len(cur)<110)):
            cur=cur+sep+t
        else:
            chunks.append(cur);cur=t
    if cur: chunks.append(cur)
    # merge a short tail
    if len(chunks)>1 and len(chunks[-1])<40: chunks[-2]+='\n'+chunks.pop()
    return chunks

def fix_long(C,lim=258):
    out=[]
    for c in C:
        if len(c)<=lim: out.append(c);continue
        # split at the sentence/line boundary closest to the middle
        cuts=[m.end() for m in re.finditer(r'(?<=[.!?…”])\s+|\n',c)]
        best=min(cuts,key=lambda k:abs(k-len(c)/2))
        out+= [c[:best].rstrip(), c[best:].lstrip()]
    return out

def sents_en(p):
    out=[];cur='';q=False
    for i,ch in enumerate(p):
        cur+=ch
        if ch=='"':q=not q
        nxt=p[i+1] if i+1<len(p) else ''
        if nxt==' ' and not q and (ch in '.!?' or (ch=='"' and cur[-2:-1] in '.!?,')):
            if ch=='"' and cur[-2]==',':continue
            out.append(cur.strip());cur=''
    if cur.strip():out.append(cur.strip())
    return out
def chunk_en(paras,maxlen=235,minlen=80,breaks=()):
    ps=[]
    for i,p in enumerate(paras):
        if len(p)<=maxlen:ps.append((p,True));continue
        cur='';first=True
        for s in sents_en(p):
            if cur and len(cur)+1+len(s)>maxlen:ps.append((cur,first));first=False;cur=s
            else:cur=(cur+' '+s).strip()
        if cur:ps.append((cur,first))
    C=[];cur=None
    for t,start in ps:
        sep='\n' if start else ' '
        force=any(t.startswith(b) for b in breaks)
        if cur is None:cur=t
        elif not force and (len(cur)<minlen or (len(cur)+len(t)+1<=maxlen and (len(t)<minlen or len(cur)<120))):cur=cur+sep+t
        else:C.append(cur);cur=t
    if cur:C.append(cur)
    if len(C)>1 and len(C[-1])<40:C[-2]+='\n'+C.pop()
    return C

def fix_long_en(C,lim=258):
    out=[]
    for c in C:
        if len(c)<=lim:out.append(c);continue
        cuts=[m.end() for m in re.finditer(r'; |\n|(?<=[.!?]) ',c) if 30<m.end()<len(c)-30]
        if not cuts:cuts=[m.end() for m in re.finditer(r', ',c) if 30<m.end()<len(c)-30]
        if not cuts:out.append(c);continue
        best=min(cuts,key=lambda k:abs(k-len(c)/2))
        out+=fix_long_en([c[:best].rstrip(),c[best:].lstrip()],lim)
    return out

if __name__=='__main__':
    # python3 tools/chunk.py ko|en paragraphs.json out.json [break-prefix ...]
    lang,src,out=sys.argv[1:4];br=tuple(sys.argv[4:]);P=json.load(open(src))
    C=fix_long(chunk(P,breaks=br)) if lang=='ko' else fix_long_en(chunk_en(P,breaks=br))
    assert re.sub(r'\s','',''.join(C))==re.sub(r'\s','',''.join(P)),'text changed'
    json.dump(C,open(out,'w'),ensure_ascii=False,indent=0)
    print(len(C),'chunks; max',max(map(len,C)),'min',min(map(len,C)))
