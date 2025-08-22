"""
Database layer for Prose Store - SQLite with FTS5
"""
import sqlite3
import json
import time
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ProseDB:
    """
    SQLite database with FTS5 for prose storage and full-text search
    """
    
    def __init__(self, db_path: str = "prose_store.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        return conn
    
    def init_database(self):
        """Initialize database schema"""
        with self.get_connection() as conn:
            # Documents table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    world_id TEXT NOT NULL,
                    title TEXT,
                    author TEXT,
                    metadata TEXT,  -- JSON
                    current_version INTEGER DEFAULT 1,
                    created_at REAL,
                    updated_at REAL
                )
            """)
            
            # Document versions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS document_versions (
                    doc_id TEXT,
                    version INTEGER,
                    content TEXT,
                    summary TEXT,
                    word_count INTEGER,
                    char_count INTEGER,
                    created_at REAL,
                    PRIMARY KEY (doc_id, version),
                    FOREIGN KEY (doc_id) REFERENCES documents(id)
                )
            """)
            
            # Spans table (paragraph-level chunks)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS spans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doc_id TEXT,
                    version INTEGER,
                    world_id TEXT,
                    start_pos INTEGER,
                    end_pos INTEGER,
                    text TEXT,
                    span_type TEXT DEFAULT 'paragraph',
                    metadata TEXT,  -- JSON
                    created_at REAL,
                    FOREIGN KEY (doc_id, version) REFERENCES document_versions(doc_id, version)
                )
            """)
            
            # FTS5 virtual table for full-text search
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS spans_fts USING fts5(
                    text,
                    doc_id,
                    world_id,
                    content='spans',
                    content_rowid='id'
                )
            """)
            
            # Edges table for relationships (rolling window aggregation)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS edges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    world_id TEXT,
                    source_span_id INTEGER,
                    target_span_id INTEGER,
                    edge_type TEXT DEFAULT 'co_occurrence',
                    weight REAL DEFAULT 1.0,
                    window_size INTEGER DEFAULT 1,
                    last_seen REAL,
                    decay_factor REAL DEFAULT 0.9,
                    metadata TEXT,  -- JSON
                    created_at REAL,
                    updated_at REAL,
                    FOREIGN KEY (source_span_id) REFERENCES spans(id),
                    FOREIGN KEY (target_span_id) REFERENCES spans(id)
                )
            """)
            
            # Indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_world ON documents(world_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_spans_doc ON spans(doc_id, version)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_spans_world ON spans(world_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_world ON edges(world_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_spans ON edges(source_span_id, target_span_id)")
            
            # Triggers to keep FTS5 in sync
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS spans_ai AFTER INSERT ON spans BEGIN
                    INSERT INTO spans_fts(rowid, text, doc_id, world_id) 
                    VALUES (new.id, new.text, new.doc_id, new.world_id);
                END
            """)
            
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS spans_ad AFTER DELETE ON spans BEGIN
                    INSERT INTO spans_fts(spans_fts, rowid, text, doc_id, world_id) 
                    VALUES ('delete', old.id, old.text, old.doc_id, old.world_id);
                END
            """)
            
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS spans_au AFTER UPDATE ON spans BEGIN
                    INSERT INTO spans_fts(spans_fts, rowid, text, doc_id, world_id) 
                    VALUES ('delete', old.id, old.text, old.doc_id, old.world_id);
                    INSERT INTO spans_fts(rowid, text, doc_id, world_id) 
                    VALUES (new.id, new.text, new.doc_id, new.world_id);
                END
            """)
    
    # Document operations
    def create_document(self, doc_id: str, world_id: str, content: str, 
                       title: str = None, author: str = None, 
                       metadata: Dict[str, Any] = None) -> Tuple[str, int]:
        """Create a new document with initial version"""
        now = time.time()
        
        with self.get_connection() as conn:
            # Insert document
            conn.execute("""
                INSERT OR REPLACE INTO documents 
                (id, world_id, title, author, metadata, current_version, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 1, ?, ?)
            """, (doc_id, world_id, title, author, json.dumps(metadata or {}), now, now))
            
            # Insert version
            word_count = len(content.split())
            char_count = len(content)
            
            conn.execute("""
                INSERT OR REPLACE INTO document_versions
                (doc_id, version, content, word_count, char_count, created_at)
                VALUES (?, 1, ?, ?, ?, ?)
            """, (doc_id, content, word_count, char_count, now))
            
            return doc_id, 1
    
    def update_document(self, doc_id: str, content: str, summary: str = None) -> int:
        """Create new version of document"""
        now = time.time()
        
        with self.get_connection() as conn:
            # Get current version
            result = conn.execute(
                "SELECT current_version FROM documents WHERE id = ?", 
                (doc_id,)
            ).fetchone()
            
            if not result:
                raise ValueError(f"Document {doc_id} not found")
            
            new_version = result['current_version'] + 1
            
            # Update document
            conn.execute("""
                UPDATE documents 
                SET current_version = ?, updated_at = ?
                WHERE id = ?
            """, (new_version, now, doc_id))
            
            # Insert new version
            word_count = len(content.split())
            char_count = len(content)
            
            conn.execute("""
                INSERT INTO document_versions
                (doc_id, version, content, summary, word_count, char_count, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (doc_id, new_version, content, summary, word_count, char_count, now))
            
            return new_version
    
    def get_document(self, doc_id: str, version: int = None) -> Optional[Dict[str, Any]]:
        """Get document by ID and version"""
        with self.get_connection() as conn:
            if version is None:
                # Get latest version
                query = """
                    SELECT d.*, dv.content, dv.summary, dv.word_count, dv.char_count
                    FROM documents d
                    JOIN document_versions dv ON d.id = dv.doc_id AND d.current_version = dv.version
                    WHERE d.id = ?
                """
                result = conn.execute(query, (doc_id,)).fetchone()
            else:
                # Get specific version
                query = """
                    SELECT d.*, dv.content, dv.summary, dv.word_count, dv.char_count
                    FROM documents d
                    JOIN document_versions dv ON d.id = dv.doc_id
                    WHERE d.id = ? AND dv.version = ?
                """
                result = conn.execute(query, (doc_id, version)).fetchone()
            
            if result:
                doc = dict(result)
                doc['metadata'] = json.loads(doc['metadata'])
                return doc
            return None
    
    def list_documents(self, world_id: str = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List documents with pagination"""
        with self.get_connection() as conn:
            if world_id:
                query = """
                    SELECT d.*, dv.word_count, dv.char_count
                    FROM documents d
                    JOIN document_versions dv ON d.id = dv.doc_id AND d.current_version = dv.version
                    WHERE d.world_id = ?
                    ORDER BY d.updated_at DESC
                    LIMIT ? OFFSET ?
                """
                results = conn.execute(query, (world_id, limit, offset)).fetchall()
            else:
                query = """
                    SELECT d.*, dv.word_count, dv.char_count
                    FROM documents d
                    JOIN document_versions dv ON d.id = dv.doc_id AND d.current_version = dv.version
                    ORDER BY d.updated_at DESC
                    LIMIT ? OFFSET ?
                """
                results = conn.execute(query, (limit, offset)).fetchall()
            
            docs = []
            for row in results:
                doc = dict(row)
                doc['metadata'] = json.loads(doc['metadata'])
                docs.append(doc)
            return docs
    
    # Span operations
    def create_spans(self, doc_id: str, version: int, world_id: str, 
                    spans_data: List[Dict[str, Any]]) -> List[int]:
        """Create multiple spans for a document"""
        now = time.time()
        span_ids = []
        
        with self.get_connection() as conn:
            for span_data in spans_data:
                cursor = conn.execute("""
                    INSERT INTO spans 
                    (doc_id, version, world_id, start_pos, end_pos, text, span_type, metadata, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    doc_id, version, world_id,
                    span_data.get('start_pos', 0),
                    span_data.get('end_pos', 0),
                    span_data['text'],
                    span_data.get('span_type', 'paragraph'),
                    json.dumps(span_data.get('metadata', {})),
                    now
                ))
                span_ids.append(cursor.lastrowid)
        
        return span_ids
    
    def get_spans(self, doc_id: str, version: int = None) -> List[Dict[str, Any]]:
        """Get spans for a document"""
        with self.get_connection() as conn:
            if version is None:
                # Get spans for latest version
                query = """
                    SELECT s.* FROM spans s
                    JOIN documents d ON s.doc_id = d.id AND s.version = d.current_version
                    WHERE s.doc_id = ?
                    ORDER BY s.start_pos
                """
                results = conn.execute(query, (doc_id,)).fetchall()
            else:
                query = """
                    SELECT * FROM spans 
                    WHERE doc_id = ? AND version = ?
                    ORDER BY start_pos
                """
                results = conn.execute(query, (doc_id, version)).fetchall()
            
            spans = []
            for row in results:
                span = dict(row)
                span['metadata'] = json.loads(span['metadata'])
                spans.append(span)
            return spans
    
    # Search operations
    def search_spans(self, query: str, world_id: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Full-text search spans using FTS5"""
        with self.get_connection() as conn:
            if world_id:
                sql = """
                    SELECT s.*, rank
                    FROM spans_fts
                    JOIN spans s ON spans_fts.rowid = s.id
                    WHERE spans_fts MATCH ? AND s.world_id = ?
                    ORDER BY rank
                    LIMIT ?
                """
                results = conn.execute(sql, (query, world_id, limit)).fetchall()
            else:
                sql = """
                    SELECT s.*, rank
                    FROM spans_fts
                    JOIN spans s ON spans_fts.rowid = s.id
                    WHERE spans_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                """
                results = conn.execute(sql, (query, limit)).fetchall()
            
            spans = []
            for row in results:
                span = dict(row)
                span['metadata'] = json.loads(span['metadata'])
                spans.append(span)
            return spans
    
    # Edge operations (rolling window aggregation)
    def update_edge(self, world_id: str, source_span_id: int, target_span_id: int,
                   weight: float = 1.0, window_size: int = 1, decay_factor: float = 0.9):
        """Update or create edge with rolling window decay"""
        now = time.time()
        
        with self.get_connection() as conn:
            # Check if edge exists
            existing = conn.execute("""
                SELECT id, weight, last_seen FROM edges
                WHERE world_id = ? AND source_span_id = ? AND target_span_id = ?
            """, (world_id, source_span_id, target_span_id)).fetchone()
            
            if existing:
                # Apply decay and add new weight
                time_diff = now - existing['last_seen']
                decayed_weight = existing['weight'] * (decay_factor ** (time_diff / 3600))  # hourly decay
                new_weight = decayed_weight + weight
                
                conn.execute("""
                    UPDATE edges 
                    SET weight = ?, last_seen = ?, updated_at = ?
                    WHERE id = ?
                """, (new_weight, now, now, existing['id']))
            else:
                # Create new edge
                conn.execute("""
                    INSERT INTO edges 
                    (world_id, source_span_id, target_span_id, weight, window_size, 
                     last_seen, decay_factor, metadata, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (world_id, source_span_id, target_span_id, weight, window_size,
                      now, decay_factor, json.dumps({}), now, now))
    
    def get_top_edges(self, world_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get top weighted edges for a world"""
        with self.get_connection() as conn:
            query = """
                SELECT e.*, 
                       s1.text as source_text, s1.doc_id as source_doc_id,
                       s2.text as target_text, s2.doc_id as target_doc_id
                FROM edges e
                JOIN spans s1 ON e.source_span_id = s1.id
                JOIN spans s2 ON e.target_span_id = s2.id
                WHERE e.world_id = ?
                ORDER BY e.weight DESC
                LIMIT ?
            """
            results = conn.execute(query, (world_id, limit)).fetchall()
            
            edges = []
            for row in results:
                edge = dict(row)
                # Handle None metadata safely
                metadata_str = edge.get('metadata')
                edge['metadata'] = json.loads(metadata_str) if metadata_str else {}
                edges.append(edge)
            return edges
    
    def aggregate_window(self, world_id: str, window_size: int = 1):
        """Aggregate co-occurrences in rolling windows"""
        with self.get_connection() as conn:
            # Get all spans for the world, ordered by document and position
            spans = conn.execute("""
                SELECT id, doc_id, start_pos 
                FROM spans 
                WHERE world_id = ?
                ORDER BY doc_id, start_pos
            """, (world_id,)).fetchall()
            
            # Create co-occurrence edges within windows
            for i in range(len(spans)):
                for j in range(i + 1, min(i + window_size + 1, len(spans))):
                    # Only create edges within same document
                    if spans[i]['doc_id'] == spans[j]['doc_id']:
                        self.update_edge(
                            world_id=world_id,
                            source_span_id=spans[i]['id'],
                            target_span_id=spans[j]['id'],
                            weight=1.0,
                            window_size=window_size
                        )
