# python3 tools/put.py book.json "커밋 메시지"   (run from the repo root; merges by id into books.json, commits, pushes)
import json,sys,subprocess
subprocess.run(['git','pull','-q','--rebase','origin','main'],check=True)
B=json.load(open('books.json'));b=json.load(open(sys.argv[1]));L=B['books']
i=next((k for k,x in enumerate(L) if x['id']==b['id']),None)
if i is None:L.append(b)
else:L[i]=b
json.dump(B,open('books.json','w'),ensure_ascii=False,indent=1);json.load(open('books.json'))
subprocess.run(['git','add','books.json','src','catalog.json'],check=True)
subprocess.run(['git','-c','user.name=Claude','-c','user.email=noreply@anthropic.com','commit','-q','-m',sys.argv[2]+'\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>'],check=True)
subprocess.run(['git','push','-q','origin','main'],check=True)
print('pushed',b['name'],len(b['orig']),'/',b.get('total',len(b['orig'])))
