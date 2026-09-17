from datetime import datetime
from sqlalchemy import String,Text,DateTime,ForeignKey,Boolean,JSON
from sqlalchemy.orm import Mapped,mapped_column,relationship
from .database import Base
class User(Base):
 __tablename__='users'; id:Mapped[int]=mapped_column(primary_key=True); email:Mapped[str]=mapped_column(String(255),unique=True,index=True); password_hash:Mapped[str]=mapped_column(String(255)); role:Mapped[str]=mapped_column(String(20),default='student'); created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow); profile=relationship('Profile',uselist=False,back_populates='user',cascade='all,delete-orphan')
class Profile(Base):
 __tablename__='profiles'; id:Mapped[int]=mapped_column(primary_key=True); user_id:Mapped[int]=mapped_column(ForeignKey('users.id'),unique=True); name:Mapped[str]=mapped_column(String(120),default=''); college:Mapped[str]=mapped_column(String(160),default=''); branch:Mapped[str]=mapped_column(String(80),default=''); semester:Mapped[str]=mapped_column(String(30),default=''); section:Mapped[str]=mapped_column(String(30),default=''); language:Mapped[str]=mapped_column(String(10),default='en'); user=relationship('User',back_populates='profile')
class Notice(Base):
 __tablename__='notices'; id:Mapped[int]=mapped_column(primary_key=True); owner_id:Mapped[int]=mapped_column(ForeignKey('users.id'),index=True); title:Mapped[str]=mapped_column(String(255)); source_name:Mapped[str]=mapped_column(String(255)); source_path:Mapped[str|None]=mapped_column(String(500),nullable=True); raw_text:Mapped[str]=mapped_column(Text); status:Mapped[str]=mapped_column(String(30),default='processed'); is_archived:Mapped[bool]=mapped_column(Boolean,default=False); is_favorite:Mapped[bool]=mapped_column(Boolean,default=False); created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow); extraction=relationship('Extraction',uselist=False,back_populates='notice',cascade='all,delete-orphan'); tasks=relationship('Task',back_populates='notice',cascade='all,delete-orphan')
class Extraction(Base):
 __tablename__='extractions'; id:Mapped[int]=mapped_column(primary_key=True); notice_id:Mapped[int]=mapped_column(ForeignKey('notices.id'),unique=True); data:Mapped[dict]=mapped_column(JSON,default=dict); summary:Mapped[str]=mapped_column(Text,default=''); notice=relationship('Notice',back_populates='extraction')
class Task(Base):
 __tablename__='tasks'; id:Mapped[int]=mapped_column(primary_key=True); notice_id:Mapped[int]=mapped_column(ForeignKey('notices.id')); title:Mapped[str]=mapped_column(String(255)); completed:Mapped[bool]=mapped_column(Boolean,default=False); notice=relationship('Notice',back_populates='tasks')
