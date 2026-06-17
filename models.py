from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def now():
    return datetime.now(timezone.utc)

class Plan(db.Model):
    __tablename__ = 'plans'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, default='')
    source_type = db.Column(db.String(20), default='manual')  # manual / ai / upload
    file_path = db.Column(db.String(500), default='')
    created_at = db.Column(db.DateTime, default=now)
    updated_at = db.Column(db.DateTime, default=now, onupdate=now)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'source_type': self.source_type,
            'file_path': self.file_path,
            'created_at': self.created_at.isoformat() if self.created_at else '',
            'updated_at': self.updated_at.isoformat() if self.updated_at else '',
        }


class KnowledgeDoc(db.Model):
    __tablename__ = 'knowledge_docs'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False)
    file_name = db.Column(db.String(300), default='')
    file_path = db.Column(db.String(500), default='')
    content = db.Column(db.Text, default='')
    card_count = db.Column(db.Integer, default=0)
    group_name = db.Column(db.String(100), default='未分组')
    created_at = db.Column(db.DateTime, default=now)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'file_name': self.file_name,
            'file_path': self.file_path,
            'content': self.content[:2000],
            'card_count': self.card_count,
            'group_name': self.group_name,
            'created_at': self.created_at.isoformat() if self.created_at else '',
        }


class KnowledgeCard(db.Model):
    __tablename__ = 'knowledge_cards'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    doc_id = db.Column(db.Integer, db.ForeignKey('knowledge_docs.id'), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, default='')
    tags = db.Column(db.String(300), default='')
    created_at = db.Column(db.DateTime, default=now)

    def to_dict(self):
        return {
            'id': self.id,
            'doc_id': self.doc_id,
            'title': self.title,
            'content': self.content,
            'tags': self.tags,
            'created_at': self.created_at.isoformat() if self.created_at else '',
        }


class Video(db.Model):
    __tablename__ = 'videos'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    url = db.Column(db.String(500), nullable=False)
    title = db.Column(db.String(300), default='')
    author = db.Column(db.String(100), default='')
    parsed_content = db.Column(db.Text, default='')
    analysis = db.Column(db.Text, default='')
    is_analyzed = db.Column(db.Boolean, default=False)
    group_name = db.Column(db.String(100), default='全部视频')
    created_at = db.Column(db.DateTime, default=now)

    def to_dict(self):
        return {
            'id': self.id,
            'url': self.url,
            'title': self.title,
            'author': self.author,
            'parsed_content': self.parsed_content[:3000],
            'analysis': self.analysis[:20000],
            'is_analyzed': self.is_analyzed,
            'group_name': self.group_name,
            'created_at': self.created_at.isoformat() if self.created_at else '',
        }


class Script(db.Model):
    __tablename__ = 'scripts'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, default='')
    requirement = db.Column(db.Text, default='')
    creative_ratio = db.Column(db.Integer, default=50)  # 创意比例 0-100
    plan_refs = db.Column(db.Text, default='[]')   # JSON array of plan ids
    knowledge_refs = db.Column(db.Text, default='[]')
    video_refs = db.Column(db.Text, default='[]')
    keywords = db.Column(db.String(500), default='')
    created_at = db.Column(db.DateTime, default=now)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'requirement': self.requirement,
            'creative_ratio': self.creative_ratio,
            'plan_refs': self.plan_refs,
            'knowledge_refs': self.knowledge_refs,
            'video_refs': self.video_refs,
            'keywords': self.keywords,
            'created_at': self.created_at.isoformat() if self.created_at else '',
        }


class Ranking(db.Model):
    __tablename__ = 'rankings'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category = db.Column(db.String(100), default='')
    rank = db.Column(db.Integer, default=0)
    author_name = db.Column(db.String(200), default='')
    followers = db.Column(db.String(50), default='')
    avg_likes = db.Column(db.String(50), default='')
    avg_comments = db.Column(db.String(50), default='')
    updated_at = db.Column(db.DateTime, default=now)

    def to_dict(self):
        return {
            'id': self.id,
            'category': self.category,
            'rank': self.rank,
            'author_name': self.author_name,
            'followers': self.followers,
            'avg_likes': self.avg_likes,
            'avg_comments': self.avg_comments,
            'updated_at': self.updated_at.isoformat() if self.updated_at else '',
        }
