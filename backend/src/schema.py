from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import CheckConstraint, BOOLEAN, DateTime, func, text, Index, select, or_, and_
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from uuid import uuid4
import enum

db = SQLAlchemy()
migrate = Migrate()

def utc_now():
    return datetime.now(timezone.utc)

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid4)
    username = db.Column(db.String(32), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(254), unique=True, nullable=False)
    pfp = db.Column(db.Text, nullable=True)
    registered_at = db.Column(DateTime(timezone=True), nullable=False, default=utc_now)

    groups = relationship("UserGroup", back_populates="user", cascade="all, delete-orphan")
    admin_profile = relationship("Admin", uselist=False, back_populates="user", cascade="all, delete-orphan")

class Group(db.Model):
    __tablename__ = "groups"

    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = db.Column(db.String(80), nullable=False)
    registered_at = db.Column(DateTime(timezone=True), nullable=False, default=utc_now)
    icon = db.Column(db.Text, nullable=True)

    members = relationship("UserGroup", back_populates="group", cascade="all, delete-orphan")

class UserGroup(db.Model):
    __tablename__ = "user_groups"

    user_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    group_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True)

    entered_at = db.Column(DateTime(timezone=True), nullable=False, default=utc_now)
    
    role = db.Column(db.String(16), nullable=False)

    user = relationship("User", back_populates="groups")
    group = relationship("Group", back_populates="members")

class Admin(db.Model):
    __tablename__ = "admins"

    id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    registered_at = db.Column(DateTime(timezone=True), nullable=False, default=utc_now)
    
    user = relationship("User", back_populates="admin_profile")

class FriendshipStatus(enum.Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"

class Friendship(db.Model):
    __tablename__ = "friendships"

    requester_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    addressee_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)

    created_at = db.Column(DateTime(timezone=True), nullable=False, default=utc_now)
    status = db.Column(
        SQLEnum(FriendshipStatus, name="friendship_status"), 
        nullable=False,
        default=FriendshipStatus.PENDING,
    )

    __table_args__ = (
        CheckConstraint('requester_id != addressee_id', name='ck_not_self_friend'),
        Index('ix_friend_addr', 'addressee_id'), 
    )

    @classmethod
    def get_between(cls, user1_id, user2_id):
        query = select(cls).where(
            or_(
                and_(cls.requester_id == user1_id, cls.addressee_id == user2_id),
                and_(cls.requester_id == user2_id, cls.addressee_id == user1_id)
            )
        )
        return db.session.execute(query).scalar_one_or_none()

class Block(db.Model):
    __tablename__ = "blocks"

    blocker_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    blockee_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)

    blocked_at = db.Column(DateTime(timezone=True), nullable=False, default=utc_now)

class RefreshToken(db.Model):
    __tablename__ = "refresh_tokens"

    token_id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    token_hash = db.Column(db.Text, nullable=False)
    expires_at = db.Column(DateTime(timezone=True), nullable=False)
    is_valid = db.Column(BOOLEAN, nullable=False, server_default=text("TRUE"), default=True)

    __table_args__ = (
        Index("ix_uid", 'user_id'),
    )