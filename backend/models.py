"""
Database models for Nexa AI.
 
Defines the relational schema: a User has many Conversations, and each
Conversation has many Messages (ordered by creation time).
"""
 
from datetime import datetime
 
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
 
from database import Base
 
 
class User(Base):
    __tablename__ = "users"
 
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
 
    conversations = relationship("Conversation", back_populates="user")
 
 
class Conversation(Base):
    __tablename__ = "conversations"
 
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, default="New Conversation")
    created_at = Column(DateTime, default=datetime.utcnow)
 
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", order_by="Message.created_at")
 
 
class Message(Base):
    __tablename__ = "messages"
 
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String, nullable=False)  # "user" or "assistant"
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
 
    conversation = relationship("Conversation", back_populates="messages")
