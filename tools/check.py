# python3 tools/check.py book.json  -> OK or problems (works for partial books with "more":true)
import json,sys,re
b=json.load(open(sys.argv[1]));bad=[]
if not re.fullmatch(r'[a-z0-9_-]+',b.get('id','')):bad.append('id')
if len((b.get('bio') or '').split('\n'))!=3:bad.append('bio 3줄 아님')
for i,x in enumerate(b['orig']):
    if len(x)<40 or len(x)>260:bad.append(f'조각 {i} 길이 {len(x)}')
for j,h in enumerate(b.get('hooks',[])):
    c=b['orig'][h['at']] if 0<=h['at']<len(b['orig']) else None
    if c is None:bad.append(f'훅 {j} at 범위')
    elif h['hl'] not in c:bad.append(f'훅 {j} hl이 조각에 없음')
    if re.search('충격|모르면 손해|썰 푼다|꿀팁|실화냐|ㄷㄷ|정리하면|결국',h['x']):bad.append(f'훅 {j} 금지 말투')
    if re.search('[\U0001F300-\U0001FAFF]',h['x']):bad.append(f'훅 {j} 이모지')
    if re.search(r'[0-9]{3,4}년',h['x']):bad.append(f'훅 {j} 연도')
for j,z in enumerate(b.get('zzal',[])):
    c=b['orig'][z['at']] if 0<=z['at']<len(b['orig']) else ''
    if z['x'] not in c:bad.append(f'짤 {j} 원문과 다름')
for j,x in enumerate(b.get('side',[])):
    if not (0<=x.get('at',-1)<len(b['orig'])):bad.append(f'반응 {j} at 범위')
    if re.search(r'[0-9]{3,4}년',x.get('x','')):bad.append(f'반응 {j} 연도')
ats=[x.get('at') for x in b.get('side',[])]
if len(ats)!=len(set(ats)):bad.append('같은 조각에 반응이 두 개')
seen=set()
for j,g in enumerate(b.get('gl',[])):
    if not g.get('w') or not g.get('m'):bad.append(f'낱말 {j} 비었음')
    elif not any(g['w'] in c for c in b['orig']):bad.append(f'낱말 {j} 원문에 없음: '+g['w'])
    if g.get('w') in seen:bad.append('낱말 중복: '+g['w'])
    seen.add(g.get('w'))
if not b.get('gl'):bad.append('낱말 톡(gl) 없음')
if b.get('lang')=='en' and len(b.get('tr',[]))!=len(b['orig']):bad.append('tr 길이가 orig와 다름')
if b.get('more'):
    if not b.get('total') or b['total']<=len(b['orig']):bad.append('more인데 total이 이상함')
    if any(t.get('lock') for t in b.get('threads',[])):bad.append('아직 다 안 들어왔는데 다 읽은 사람만 타래가 있음')
elif not any(t.get('lock') for t in b.get('threads',[])):bad.append('다 읽은 사람만 타래 없음')
if not b.get('by'):bad.append('담당 유저(by) 없음')
for k in ('name','author','when','color','cvs','lang','tone'):
    if k not in b:bad.append(k+' 없음')
print('\n'.join(bad) if bad else 'OK')
