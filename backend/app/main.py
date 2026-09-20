from datetime import datetime,timedelta,timezone
import re,shutil,uuid
from pathlib import Path
from fastapi import FastAPI,Depends,HTTPException,UploadFile,File,Form,Request,Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
from jose import jwt,JWTError
from passlib.context import CryptContext
from pydantic import BaseModel,EmailStr,Field
from sqlalchemy.orm import Session
from pypdf import PdfReader
from PIL import Image
from .core import settings
from .database import Base,engine,get_db
from .models import User,Profile,Notice,Extraction,Task
from .ocr import extract_image_text, OCRUnavailableError
Base.metadata.create_all(engine)
app=FastAPI(title='NOTICE LENS API',version='1.0.0')
app.add_middleware(CORSMiddleware,allow_origins=settings.allowed_cors_origins,allow_credentials=True,allow_methods=['*'],allow_headers=['*'])
pwd=CryptContext(schemes=['pbkdf2_sha256'],deprecated='auto'); oauth=OAuth2PasswordBearer(tokenUrl='/api/auth/login', auto_error=False)
class Register(BaseModel): email:EmailStr; password:str=Field(min_length=8)
class ProfileIn(BaseModel): name:str='';college:str='';branch:str='';semester:str='';section:str='';language:str='en'
class TextIn(BaseModel): text:str=Field(min_length=2); source_name:str='Pasted text'
class QA(BaseModel): question:str=Field(min_length=2,max_length=500)
def token(u): return jwt.encode({'sub':str(u.id),'role':u.role,'exp':datetime.now(timezone.utc)+timedelta(hours=12)},settings.secret_key,algorithm='HS256')
def me(request: Request, t: str | None = Depends(oauth), db: Session = Depends(get_db)):
 credential = request.cookies.get('noticelens_session') or t
 if not credential:
  raise HTTPException(401, 'Your session has expired. Please sign in again.')
 try: u=db.get(User,int(jwt.decode(credential,settings.secret_key,algorithms=['HS256'])['sub']))
 except (JWTError,ValueError,KeyError): u=None
 if not u: raise HTTPException(401,'Your session is invalid. Please sign in again.')
 return u
def session_response(response: Response, user: User):
 value=token(user)
 response.set_cookie(key='noticelens_session',value=value,httponly=True,samesite='lax',secure=settings.session_cookie_secure,max_age=60*60*12,path='/')
 return {'access_token':value,'token_type':'bearer'}
def facts(text):
 lines=[x.strip() for x in text.splitlines() if x.strip()]; rx=lambda p:re.findall(p,text,re.I)
 actions=[x for x in lines if re.search(r'apply|submit|register|pay|attend|bring',x,re.I)]
 deadlines=[x for x in lines if re.search(r'last date|deadline|due date|submit by',x,re.I)]
 return {'title':lines[0][:255] if lines else 'Untitled notice','dates':rx(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'),'deadlines':deadlines,'actions':actions,'fees':[x for x in lines if re.search(r'₹|rs\.?|fee',x,re.I)],'documents':[x for x in lines if re.search(r'document|certificate|mark sheet|id card',x,re.I)],'contacts':rx(r'[\w.+-]+@[\w-]+\.[\w.-]+')+rx(r'(?<!\w)(?:\+91[- ]?)?[6-9]\d{9}(?!\w)'),'links':rx(r'https?://[^\s)>\]]+'),'department':None,'audience':None,'venue':None}
def visible(db,u,nid):
 n=db.get(Notice,nid)
 if not n or (n.owner_id!=u.id and u.role!='admin'): raise HTTPException(404,'Notice not found')
 return n
def out(n): return {'id':n.id,'title':n.title,'source_name':n.source_name,'raw_text':n.raw_text,'status':n.status,'is_archived':n.is_archived,'is_favorite':n.is_favorite,'created_at':n.created_at,'extraction':n.extraction.data if n.extraction else None}
@app.post('/api/auth/register')
def register(data:Register,response:Response,db:Session=Depends(get_db)):
 if db.query(User).filter_by(email=data.email.lower()).first(): raise HTTPException(409,'An account already exists for this email. Please sign in instead.')
 u=User(email=data.email.lower(),password_hash=pwd.hash(data.password));u.profile=Profile();db.add(u);db.commit();db.refresh(u);return session_response(response,u)
@app.post('/api/auth/login')
def login(response:Response,data:OAuth2PasswordRequestForm=Depends(),db:Session=Depends(get_db)):
 u=db.query(User).filter_by(email=data.username.lower()).first()
 if not u or not pwd.verify(data.password,u.password_hash): raise HTTPException(401,'Incorrect email or password. Check your details and try again.')
 return session_response(response,u)
@app.post('/api/auth/logout')
def logout(response:Response):
 response.delete_cookie('noticelens_session',path='/');return {'ok':True}
@app.get('/api/me')
def get_me(u=Depends(me)): return {'email':u.email,'role':u.role,**{k:getattr(u.profile,k) for k in ['name','college','branch','semester','section','language']}}
@app.put('/api/me')
def put_me(data:ProfileIn,u=Depends(me),db:Session=Depends(get_db)):
 for k,v in data.model_dump().items(): setattr(u.profile,k,v)
 db.commit();return {'ok':True}
def create_notice(text,name,path,u,db):
 f=facts(text);n=Notice(owner_id=u.id,title=f['title'],source_name=name,source_path=path,raw_text=text);n.extraction=Extraction(data=f,summary='Structured facts were extracted from the source notice.');db.add(n);db.flush()
 for a in f['actions']: db.add(Task(notice_id=n.id,title=a[:255]))
 db.commit();db.refresh(n);return out(n)
@app.post('/api/notices/text')
def add_text(data:TextIn,u=Depends(me),db:Session=Depends(get_db)): return create_notice(data.text,data.source_name,None,u,db)
@app.post('/api/notices/upload')
def upload(file:UploadFile=File(...),u=Depends(me),db:Session=Depends(get_db)):
 ext=Path(file.filename or '').suffix.lower()
 if ext not in {'.pdf','.png','.jpg','.jpeg'}: raise HTTPException(415,'Only PDF, PNG, JPG and JPEG are allowed')
 path=Path(settings.upload_dir)/f'{uuid.uuid4()}{ext}'
 with path.open('wb') as dest: shutil.copyfileobj(file.file,dest)
 try:
  if ext=='.pdf': text='\n'.join(p.extract_text() or '' for p in PdfReader(str(path)).pages)
  else: text=extract_image_text(path)
 except OCRUnavailableError as e: raise HTTPException(503,str(e)) from e
 except ValueError as e: raise HTTPException(422,str(e)) from e
 except Exception as e: raise HTTPException(422,'Could not extract text from this document. Please try another file or paste the notice text.') from e
 if not text.strip(): raise HTTPException(422,'No readable text found in document')
 return create_notice(text,file.filename,str(path),u,db)
@app.get('/api/notices')
def notices(q:str='',u=Depends(me),db:Session=Depends(get_db)):
 rows=db.query(Notice).filter(Notice.owner_id==u.id,Notice.is_archived==False).order_by(Notice.created_at.desc()).all();return [out(n) for n in rows if q.lower() in (n.title+n.raw_text).lower()]
@app.get('/api/notices/{nid}')
def detail(nid:int,u=Depends(me),db:Session=Depends(get_db)): return out(visible(db,u,nid))
@app.delete('/api/notices/{nid}', status_code=204)
def delete_notice(nid:int,u=Depends(me),db:Session=Depends(get_db)):
 n=visible(db,u,nid)
 db.delete(n)
 db.commit()
@app.patch('/api/notices/{nid}/favorite')
def favorite(nid:int,u=Depends(me),db:Session=Depends(get_db)):
 n=visible(db,u,nid);n.is_favorite=not n.is_favorite;db.commit();return out(n)
@app.post('/api/notices/{nid}/qa')
def qa(nid:int,data:QA,u=Depends(me),db:Session=Depends(get_db)):
 n=visible(db,u,nid);words=set(re.findall(r'\w+',data.question.lower()));hits=[x.strip() for x in re.split(r'(?<=[.!?])\s+|\n+',n.raw_text) if words & set(re.findall(r'\w+',x.lower()))]
 if not hits:return {'answer':'Not mentioned in the notice.','sources':[]}
 return {'answer':' '.join(hits[:3]),'sources':[f'Source notice excerpt {i+1}: {x[:180]}' for i,x in enumerate(hits[:3])]}
@app.get('/api/tasks')
def tasks(u=Depends(me),db:Session=Depends(get_db)):
 return [{'id':t.id,'title':t.title,'completed':t.completed,'notice_id':t.notice_id} for t in db.query(Task).join(Notice).filter(Notice.owner_id==u.id).all()]
@app.patch('/api/tasks/{tid}')
def task(tid:int,completed:bool,u=Depends(me),db:Session=Depends(get_db)):
 t=db.get(Task,tid)
 if not t or t.notice.owner_id!=u.id:raise HTTPException(404,'Task not found')
 t.completed=completed;db.commit();return {'id':t.id,'completed':t.completed}
@app.get('/health')
def health(): return {'status':'ok'}





