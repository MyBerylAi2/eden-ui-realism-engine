"""
EDEN UI REALISM ENGINE - Database Models
========================================
SQLAlchemy models for model management, chat history, and generation tracking.
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from typing import Optional
import json

from config import get_settings

settings = get_settings()
Base = declarative_base()


class HFModel(Base):
    """Hugging Face model registry."""
    __tablename__ = "hf_models"
    
    id = Column(Integer, primary_key=True)
    model_id = Column(String(500), unique=True, nullable=False)  # e.g., "stabilityai/stable-diffusion-xl-base-1.0"
    name = Column(String(255))
    description = Column(Text)
    model_type = Column(String(50))  # "diffusion", "transformer", "vae", "lora", etc.
    source = Column(String(50), default="huggingface")  # huggingface, civitai, local
    download_url = Column(String(1000))
    local_path = Column(String(1000))
    is_downloaded = Column(Boolean, default=False)
    is_favorite = Column(Boolean, default=False)
    config = Column(JSON)  # Model-specific configuration
    tags = Column(JSON)  # Tags for filtering
    file_size = Column(Integer)  # In bytes
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    generations = relationship("Generation", back_populates="model")


class Generation(Base):
    """Generation history tracking."""
    __tablename__ = "generations"
    
    id = Column(Integer, primary_key=True)
    generation_type = Column(String(50), nullable=False)  # "text2image", "text2video", "image2video", "video2video"
    model_id = Column(Integer, ForeignKey("hf_models.id"))
    
    # Input parameters
    prompt = Column(Text)
    negative_prompt = Column(Text)
    width = Column(Integer)
    height = Column(Integer)
    num_frames = Column(Integer)  # For video
    fps = Column(Float)
    guidance_scale = Column(Float)
    num_inference_steps = Column(Integer)
    seed = Column(Integer)
    scheduler = Column(String(50))
    sampler = Column(String(50))
    
    # Additional settings
    settings = Column(JSON)
    
    # Input/Output files
    input_image_path = Column(String(1000))
    input_video_path = Column(String(1000))
    output_path = Column(String(1000))
    
    # Status
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    error_message = Column(Text)
    
    # Metadata
    duration_seconds = Column(Float)  # Generation time
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    model = relationship("HFModel", back_populates="generations")


class ChatMessage(Base):
    """Natural language chat history."""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(255), index=True)
    role = Column(String(50))  # "user", "assistant", "system"
    content = Column(Text)
    message_type = Column(String(50), default="text")  # text, image, video, command
    attachments = Column(JSON)  # File paths for drag-drop
    generation_id = Column(Integer, ForeignKey("generations.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class FineTuningJob(Base):
    """Model fine-tuning job tracking."""
    __tablename__ = "fine_tuning_jobs"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    base_model_id = Column(String(500))
    job_type = Column(String(50))  # "lora", "dreambooth", "full", "distillation"
    
    # Training config
    dataset_path = Column(String(1000))
    output_path = Column(String(1000))
    config = Column(JSON)
    
    # Progress
    status = Column(String(50), default="pending")
    current_step = Column(Integer, default=0)
    total_steps = Column(Integer, default=0)
    loss = Column(Float)
    learning_rate = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    error_message = Column(Text)


class ModelMerge(Base):
    """Model merging configuration."""
    __tablename__ = "model_merges"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    
    # Models to merge
    model_a_id = Column(String(500))
    model_b_id = Column(String(500))
    merge_method = Column(String(50))  # "weighted", "slerp", "ties", "dare"
    alpha = Column(Float, default=0.5)  # Merge ratio
    
    # Result
    output_path = Column(String(1000))
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)


class UserSettings(Base):
    """User preferences and settings."""
    __tablename__ = "user_settings"
    
    id = Column(Integer, primary_key=True)
    
    # Default generation settings
    default_image_width = Column(Integer, default=1024)
    default_image_height = Column(Integer, default=1024)
    default_video_width = Column(Integer, default=832)
    default_video_height = Column(Integer, default=480)
    default_guidance_scale = Column(Float, default=7.5)
    default_steps = Column(Integer, default=30)
    
    # Negative prompt preferences
    use_full_negative = Column(Boolean, default=True)
    custom_negative_additions = Column(Text)
    
    # UI preferences
    theme = Column(String(50), default="dark")
    language = Column(String(10), default="en")
    
    # Paths
    default_output_dir = Column(String(1000))
    comfyui_path = Column(String(1000))
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Database engine and session
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
