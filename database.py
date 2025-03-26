import os
import json
import datetime
import base64
import pickle
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

# Get database URL from environment variable
DATABASE_URL = os.environ.get("DATABASE_URL")

# Create SQLAlchemy engine and session
engine = create_engine(DATABASE_URL, poolclass=NullPool)
Session = sessionmaker(bind=engine)
Base = declarative_base()

class BowlingSession(Base):
    """SQLAlchemy model for cricket bowling sessions"""
    __tablename__ = 'bowling_sessions'
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    bowler = Column(String)
    type = Column(String)
    date = Column(DateTime, default=datetime.datetime.now)
    fps = Column(Float)
    session_metadata = Column(Text)  # JSON string for metadata
    
    # Store processed_results data as compressed binary
    processed_results_data = Column(LargeBinary)
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'bowler': self.bowler,
            'type': self.type,
            'date': self.date.strftime('%Y-%m-%d %H:%M:%S') if self.date else None,
            'fps': self.fps,
            'processed_results': pickle.loads(self.processed_results_data) if self.processed_results_data else []
        }

class AnalysisReport(Base):
    """SQLAlchemy model for analysis reports"""
    __tablename__ = 'analysis_reports'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, nullable=False)
    report_date = Column(DateTime, default=datetime.datetime.now)
    report_data = Column(Text)  # JSON string
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'report_date': self.report_date.strftime('%Y-%m-%d %H:%M:%S') if self.report_date else None,
            'report_data': json.loads(self.report_data) if self.report_data else {}
        }

def initialize_database():
    """Initialize database tables if they don't exist"""
    Base.metadata.create_all(engine)
    print("Database tables created successfully")

def save_session_to_db(session_data):
    """
    Save session data to database
    
    Args:
        session_data (dict): Session data to save
        
    Returns:
        bool: Success status
    """
    try:
        # Initialize database
        initialize_database()
        
        # Create a database session
        db_session = Session()
        
        # Create a copy of session data without large frame data for metadata
        session_metadata = {
            'id': session_data['id'],
            'name': session_data['name'],
            'bowler': session_data['bowler'],
            'type': session_data['type'],
            'date': session_data['date'],
            'fps': session_data['fps']
        }
        
        # Serialize processed_results
        processed_results_binary = pickle.dumps(session_data['processed_results'])
        
        # Create a new BowlingSession record
        new_session = BowlingSession(
            id=session_data['id'],
            name=session_data['name'],
            bowler=session_data['bowler'],
            type=session_data['type'],
            date=datetime.datetime.strptime(session_data['date'], '%Y-%m-%d %H:%M:%S') if isinstance(session_data['date'], str) else session_data['date'],
            fps=session_data['fps'],
            session_metadata=json.dumps(session_metadata),
            processed_results_data=processed_results_binary
        )
        
        # Add to database and commit
        db_session.add(new_session)
        db_session.commit()
        db_session.close()
        
        return True
    except Exception as e:
        print(f"Error saving session to database: {str(e)}")
        return False

def load_sessions_from_db():
    """
    Load all sessions from database
    
    Returns:
        list: List of session dictionaries
    """
    try:
        # Initialize database
        initialize_database()
        
        # Create a database session
        db_session = Session()
        
        # Query all bowling sessions
        sessions = db_session.query(BowlingSession).all()
        
        # Convert to dictionaries
        session_dicts = [
            {
                'id': session.id,
                'name': session.name,
                'bowler': session.bowler,
                'type': session.type,
                'date': session.date.strftime('%Y-%m-%d %H:%M:%S') if session.date else None,
                'fps': session.fps
            }
            for session in sessions
        ]
        
        db_session.close()
        
        return session_dicts
    except Exception as e:
        print(f"Error loading sessions from database: {str(e)}")
        return []

def load_session_from_db(session_id):
    """
    Load a specific session from database
    
    Args:
        session_id (str): ID of session to load
        
    Returns:
        dict: Session data or None if not found
    """
    try:
        # Initialize database
        initialize_database()
        
        # Create a database session
        db_session = Session()
        
        # Query the specific bowling session
        session = db_session.query(BowlingSession).filter_by(id=session_id).first()
        
        if not session:
            db_session.close()
            return None
        
        # Convert to dictionary
        session_dict = session.to_dict()
        
        db_session.close()
        
        return session_dict
    except Exception as e:
        print(f"Error loading session from database: {str(e)}")
        return None

def delete_session_from_db(session_id):
    """
    Delete a session from database
    
    Args:
        session_id (str): ID of session to delete
        
    Returns:
        bool: Success status
    """
    try:
        # Initialize database
        initialize_database()
        
        # Create a database session
        db_session = Session()
        
        # Query the specific bowling session
        session = db_session.query(BowlingSession).filter_by(id=session_id).first()
        
        if not session:
            db_session.close()
            return False
        
        # Delete the session
        db_session.delete(session)
        db_session.commit()
        db_session.close()
        
        return True
    except Exception as e:
        print(f"Error deleting session from database: {str(e)}")
        return False

def save_report_to_db(session_id, report_data):
    """
    Save analysis report to database
    
    Args:
        session_id (str): ID of the session
        report_data (dict): Report data to save
        
    Returns:
        int: Report ID or None if error
    """
    try:
        # Initialize database
        initialize_database()
        
        # Create a database session
        db_session = Session()
        
        # Create a new report record
        new_report = AnalysisReport(
            session_id=session_id,
            report_data=json.dumps(report_data)
        )
        
        # Add to database and commit
        db_session.add(new_report)
        db_session.commit()
        
        # Get the ID
        report_id = new_report.id
        
        db_session.close()
        
        return report_id
    except Exception as e:
        print(f"Error saving report to database: {str(e)}")
        return None