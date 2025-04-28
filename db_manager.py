import sqlite3
import os
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages SQLite database operations for the Gospel JukeBox application."""
    
    def __init__(self, db_path):
        """Initialize the database manager with the database file path."""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.initialize_database()
    
    def connect(self):
        """Establish a connection to the SQLite database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            return True
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            return False
    
    def disconnect(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
    
    def initialize_database(self):
        """Create database tables if they don't exist."""
        if not self.connect():
            return False
        
        try:
            # Create song_notes table
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS song_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                song_name TEXT NOT NULL UNIQUE,
                notes TEXT,
                last_updated TIMESTAMP
            )
            ''')
            
            # Create sheet_music table
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sheet_music (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                song_name TEXT NOT NULL UNIQUE,
                file_path TEXT NOT NULL,
                upload_date TIMESTAMP
            )
            ''')
            
            self.conn.commit()
            logger.info("Database initialized successfully")
            return True
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
            return False
        finally:
            self.disconnect()
    
    def save_song_notes(self, song_name, notes):
        """Save or update notes for a song."""
        if not self.connect():
            return False
        
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Check if song exists in the database
            self.cursor.execute("SELECT id FROM song_notes WHERE song_name = ?", (song_name,))
            result = self.cursor.fetchone()
            
            if result:
                # Update existing notes
                self.cursor.execute(
                    "UPDATE song_notes SET notes = ?, last_updated = ? WHERE song_name = ?",
                    (notes, timestamp, song_name)
                )
            else:
                # Insert new notes
                self.cursor.execute(
                    "INSERT INTO song_notes (song_name, notes, last_updated) VALUES (?, ?, ?)",
                    (song_name, notes, timestamp)
                )
            
            self.conn.commit()
            logger.info(f"Notes saved for song: {song_name}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error saving song notes: {e}")
            return False
        finally:
            self.disconnect()
    
    def get_song_notes(self, song_name):
        """Retrieve notes for a specific song."""
        if not self.connect():
            return ""
        
        try:
            self.cursor.execute("SELECT notes FROM song_notes WHERE song_name = ?", (song_name,))
            result = self.cursor.fetchone()
            
            if result:
                return result[0]
            else:
                return ""
        except sqlite3.Error as e:
            logger.error(f"Error retrieving song notes: {e}")
            return ""
        finally:
            self.disconnect()
    
    def save_sheet_music_reference(self, song_name, file_path):
        """Save or update sheet music file reference for a song."""
        if not self.connect():
            return False
        
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Check if song exists in the database
            self.cursor.execute("SELECT id FROM sheet_music WHERE song_name = ?", (song_name,))
            result = self.cursor.fetchone()
            
            if result:
                # Update existing reference
                self.cursor.execute(
                    "UPDATE sheet_music SET file_path = ?, upload_date = ? WHERE song_name = ?",
                    (file_path, timestamp, song_name)
                )
            else:
                # Insert new reference
                self.cursor.execute(
                    "INSERT INTO sheet_music (song_name, file_path, upload_date) VALUES (?, ?, ?)",
                    (song_name, file_path, timestamp)
                )
            
            self.conn.commit()
            logger.info(f"Sheet music reference saved for song: {song_name}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error saving sheet music reference: {e}")
            return False
        finally:
            self.disconnect()
    
    def get_sheet_music_path(self, song_name):
        """Retrieve sheet music file path for a specific song."""
        if not self.connect():
            return None
        
        try:
            self.cursor.execute("SELECT file_path FROM sheet_music WHERE song_name = ?", (song_name,))
            result = self.cursor.fetchone()
            
            if result:
                return result[0]
            else:
                return None
        except sqlite3.Error as e:
            logger.error(f"Error retrieving sheet music path: {e}")
            return None
        finally:
            self.disconnect()
    
    def get_all_song_notes(self):
        """Retrieve all song notes as a dictionary."""
        if not self.connect():
            return {}
        
        try:
            self.cursor.execute("SELECT song_name, notes FROM song_notes")
            results = self.cursor.fetchall()
            
            notes_dict = {song_name: notes for song_name, notes in results}
            return notes_dict
        except sqlite3.Error as e:
            logger.error(f"Error retrieving all song notes: {e}")
            return {}
        finally:
            self.disconnect()