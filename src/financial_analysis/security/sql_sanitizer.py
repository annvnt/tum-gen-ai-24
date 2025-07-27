"""
SQL injection prevention utilities
Provides parameterized queries and SQL sanitization
"""

import re
from typing import Any, Dict, List, Optional, Union
from sqlalchemy import text
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


class SQLSanitizer:
    """SQL injection prevention utilities"""
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r'(?i)(union|select|insert|update|delete|drop|create|alter|exec|execute)',
        r'(?i)(union\s+select|select\s+\*|select\s+.*from\s+.*where)',
        r'(?i)(drop\s+table|drop\s+database|alter\s+table|create\s+table)',
        r'(?i)(exec\s*\(|execute\s*\(|xp_)',
        r'(?i)(;|--|\/\*|\*\/|#|@@|@|char\(|nchar\(|varchar\(|nvarchar\()',
        r'(?i)(and\s+1\s*=\s*1|or\s+1\s*=\s*1|and\s+1\s*=\s*2|or\s+1\s*=\s*2)',
        r'(?i)(waitfor\s+delay|benchmark\(|sleep\()',
        r'(?i)(information_schema|sys\.|master\.|tempdb\.)',
    ]
    
    # Reserved SQL keywords
    RESERVED_KEYWORDS = {
        'select', 'insert', 'update', 'delete', 'drop', 'create', 'alter',
        'exec', 'execute', 'union', 'where', 'from', 'table', 'database',
        'schema', 'column', 'index', 'view', 'trigger', 'procedure',
        'function', 'user', 'role', 'grant', 'revoke', 'commit', 'rollback'
    }
    
    @classmethod
    def sanitize_like_pattern(cls, pattern: str) -> str:
        """Sanitize pattern for LIKE queries"""
        if not pattern or not isinstance(pattern, str):
            return ""
            
        # Remove SQL injection patterns
        sanitized = pattern
        
        # Escape special LIKE characters
        sanitized = sanitized.replace('%', '\\%')
        sanitized = sanitized.replace('_', '\\_')
        
        # Remove SQL keywords
        for keyword in cls.RESERVED_KEYWORDS:
            sanitized = re.sub(rf'(?i)\b{keyword}\b', '', sanitized)
        
        # Remove SQL injection patterns
        for pattern in cls.SQL_INJECTION_PATTERNS:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
        
        return sanitized.strip()
    
    @classmethod
    def validate_column_name(cls, column_name: str) -> bool:
        """Validate column name for SQL injection"""
        if not column_name or not isinstance(column_name, str):
            return False
            
        # Check for valid column name pattern
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', column_name):
            return False
            
        # Check against reserved keywords
        if column_name.lower() in cls.RESERVED_KEYWORDS:
            return False
            
        return True
    
    @classmethod
    def validate_table_name(cls, table_name: str) -> bool:
        """Validate table name for SQL injection"""
        return cls.validate_column_name(table_name)
    
    @classmethod
    def sanitize_order_by(cls, order_by: str, allowed_columns: List[str]) -> Optional[str]:
        """Sanitize ORDER BY clause"""
        if not order_by or not isinstance(order_by, str):
            return None
            
        # Split by comma for multiple columns
        parts = order_by.split(',')
        sanitized_parts = []
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
                
            # Split direction
            direction = 'ASC'
            column = part
            
            if ' ' in part:
                column_part, direction_part = part.rsplit(' ', 1)
                column = column_part.strip()
                direction = direction_part.strip().upper()
                
                if direction not in ['ASC', 'DESC']:
                    direction = 'ASC'
            
            # Validate column name
            if column not in allowed_columns:
                logger.warning(f"Invalid column in ORDER BY: {column}")
                continue
                
            # Validate column name format
            if not cls.validate_column_name(column):
                continue
                
            sanitized_parts.append(f"{column} {direction}")
        
        return ', '.join(sanitized_parts) if sanitized_parts else None
    
    @classmethod
    def build_safe_like_query(cls, column: str, pattern: str, escape_char: str = '\\') -> tuple:
        """Build safe LIKE query with parameters"""
        if not cls.validate_column_name(column):
            raise ValueError(f"Invalid column name: {column}")
            
        sanitized_pattern = cls.sanitize_like_pattern(pattern)
        
        # Use parameterized query
        query = text(f"{column} LIKE :pattern ESCAPE '{escape_char}'")
        params = {'pattern': f'%{sanitized_pattern}%'}
        
        return query, params
    
    @classmethod
    def build_safe_in_query(cls, column: str, values: List[Any]) -> tuple:
        """Build safe IN query with parameter binding"""
        if not cls.validate_column_name(column):
            raise ValueError(f"Invalid column name: {column}")
            
        if not values:
            raise ValueError("Values list cannot be empty")
            
        # Validate values
        validated_values = []
        for value in values:
            if isinstance(value, str):
                validated_values.append(value)
            elif isinstance(value, (int, float)):
                validated_values.append(value)
            elif isinstance(value, bool):
                validated_values.append(value)
            else:
                # Skip invalid values
                continue
        
        if not validated_values:
            raise ValueError("No valid values provided")
            
        # Build parameterized query
        placeholders = [f':value_{i}' for i in range(len(validated_values))]
        query = text(f"{column} IN ({', '.join(placeholders)})")
        
        params = {f'value_{i}': value for i, value in enumerate(validated_values)}
        
        return query, params
    
    @classmethod
    def detect_sql_injection(cls, input_str: str) -> bool:
        """Detect potential SQL injection in input"""
        if not input_str or not isinstance(input_str, str):
            return False
            
        # Check against SQL injection patterns
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, str(input_str), re.IGNORECASE):
                logger.warning(f"SQL injection pattern detected: {pattern} in {input_str}")
                return True
                
        return False
    
    @classmethod
    def validate_limit_offset(cls, limit: int, offset: int = 0) -> tuple:
        """Validate and sanitize LIMIT and OFFSET values"""
        # Validate limit
        if not isinstance(limit, int) or limit < 0:
            limit = 100  # Default limit
        elif limit > 1000:  # Maximum limit
            limit = 1000
            
        # Validate offset
        if not isinstance(offset, int) or offset < 0:
            offset = 0
        elif offset > 10000:  # Maximum offset
            offset = 10000
            
        return limit, offset
    
    @classmethod
    def safe_string_comparison(cls, column: str, value: str, case_sensitive: bool = False) -> tuple:
        """Build safe string comparison query"""
        if not cls.validate_column_name(column):
            raise ValueError(f"Invalid column name: {column}")
            
        if not isinstance(value, str):
            raise ValueError("Value must be a string")
            
        # Sanitize value
        sanitized_value = str(value).replace('\x00', '')
        
        if case_sensitive:
            query = text(f"{column} = :value")
        else:
            query = text(f"LOWER({column}) = LOWER(:value)")
            
        params = {'value': sanitized_value}
        
        return query, params
    
    @classmethod
    def safe_date_range_query(cls, column: str, start_date: str, end_date: str) -> tuple:
        """Build safe date range query"""
        if not cls.validate_column_name(column):
            raise ValueError(f"Invalid column name: {column}")
            
        query = text(f"{column} BETWEEN :start_date AND :end_date")
        params = {
            'start_date': start_date,
            'end_date': end_date
        }
        
        return query, params
    
    @classmethod
    def safe_json_query(cls, column: str, json_path: str, value: Any) -> tuple:
        """Build safe JSON query for SQLite JSON columns"""
        if not cls.validate_column_name(column):
            raise ValueError(f"Invalid column name: {column}")
            
        # Sanitize JSON path
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', json_path):
            raise ValueError(f"Invalid JSON path: {json_path}")
            
        query = text(f"json_extract({column}, '$.{json_path}') = :value")
        params = {'value': value}
        
        return query, params
    
    @classmethod
    def safe_update_query(cls, table: str, set_values: Dict[str, Any], 
                         where_clause: Dict[str, Any]) -> tuple:
        """Build safe UPDATE query"""
        if not cls.validate_table_name(table):
            raise ValueError(f"Invalid table name: {table}")
            
        # Validate set values
        set_parts = []
        params = {}
        
        for column, value in set_values.items():
            if not cls.validate_column_name(column):
                raise ValueError(f"Invalid column name: {column}")
                
            set_parts.append(f"{column} = :set_{column}")
            params[f'set_{column}'] = value
            
        # Validate where clause
        where_parts = []
        for column, value in where_clause.items():
            if not cls.validate_column_name(column):
                raise ValueError(f"Invalid column name: {column}")
                
            where_parts.append(f"{column} = :where_{column}")
            params[f'where_{column}'] = value
            
        query = text(
            f"UPDATE {table} SET {', '.join(set_parts)} WHERE {' AND '.join(where_parts)}"
        )
        
        return query, params
    
    @classmethod
    def safe_insert_query(cls, table: str, values: Dict[str, Any]) -> tuple:
        """Build safe INSERT query"""
        if not cls.validate_table_name(table):
            raise ValueError(f"Invalid table name: {table}")
            
        # Validate columns
        for column in values.keys():
            if not cls.validate_column_name(column):
                raise ValueError(f"Invalid column name: {column}")
                
        columns = list(values.keys())
        placeholders = [f':{col}' for col in columns]
        
        query = text(
            f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        )
        
        params = {col: value for col, value in values.items()}
        
        return query, params