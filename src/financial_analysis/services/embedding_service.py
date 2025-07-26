"""
Jina Embedding Service for Financial Document Processing
Generates embeddings from Excel content for vector storage
"""

import os
import pandas as pd
import numpy as np
import requests
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class EmbeddingResult:
    embedding: List[float]
    text: str
    tokens: int
    metadata: Dict[str, Any]

class JinaEmbeddingService:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("JINA_API_KEY")
        if not self.api_key:
            raise ValueError("JINA_API_KEY environment variable is required")
        
        self.api_url = "https://api.jina.ai/v1/embeddings"
        self.model = "jina-embeddings-v3"
        self.vector_size = 1024
        
    def generate_embeddings(self, texts: List[str], task: str = "retrieval.passage") -> List[EmbeddingResult]:
        """Generate embeddings for a list of texts using Jina API"""
        if not texts:
            return []
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "input": texts,
            "task": task,
            "encoding_format": "float"
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for item in data["data"]:
                results.append(EmbeddingResult(
                    embedding=item["embedding"],
                    text=texts[item["index"]],
                    tokens=item.get("usage", {}).get("total_tokens", 0),
                    metadata={}
                ))
            
            return results
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Jina API request failed: {str(e)}")
        except KeyError as e:
            raise Exception(f"Invalid response format from Jina API: {str(e)}")
    
    def generate_single_embedding(self, text: str, task: str = "retrieval.query") -> EmbeddingResult:
        """Generate embedding for a single text"""
        results = self.generate_embeddings([text], task)
        return results[0] if results else None
    
    def generate_excel_embeddings(self, df: pd.DataFrame, filename: str, file_id: str) -> List[EmbeddingResult]:
        """Generate embeddings for Excel content with structured metadata"""
        if df.empty:
            return []
            
        texts = []
        metadata_list = []
        
        # Create meaningful text representations for each row
        for idx, row in df.iterrows():
            text_parts = []
            row_metadata = {
                "row_index": idx,
                "filename": filename,
                "file_id": file_id,
                "columns": list(df.columns),
                "column_count": len(df.columns),
                "non_null_fields": 0
            }
            
            # Build text and collect metadata
            for col in df.columns:
                value = row[col]
                if pd.notna(value):
                    text_parts.append(f"{col}: {value}")
                    row_metadata[col] = str(value)
                    row_metadata["non_null_fields"] += 1
            
            text = " | ".join(text_parts)
            texts.append(text)
            metadata_list.append(row_metadata)
        
        # Generate embeddings
        results = self.generate_embeddings(texts, task="retrieval.passage")
        
        # Add metadata to results
        for result, metadata in zip(results, metadata_list):
            result.metadata = metadata
        
        return results
    
    def generate_file_summary_embedding(self, df: pd.DataFrame, filename: str, file_id: str) -> EmbeddingResult:
        """Generate a summary embedding for the entire Excel file"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        date_cols = df.select_dtypes(include=['datetime64']).columns
        
        summary_parts = [
            f"Financial document: {filename}",
            f"File ID: {file_id}",
            f"Contains {len(df)} rows and {len(df.columns)} columns",
            f"Columns: {', '.join(df.columns)}",
            f"Numeric columns: {len(numeric_cols)}",
            f"Date columns: {len(date_cols)}"
        ]
        
        # Add data summary for numeric columns
        if len(numeric_cols) > 0:
            summary_parts.append(f"Total numeric values: {len(numeric_cols) * len(df)}")
        
        summary_text = " | ".join(summary_parts)
        
        result = self.generate_single_embedding(summary_text, task="retrieval.passage")
        if result:
            result.metadata = {
                "type": "file_summary",
                "filename": filename,
                "file_id": file_id,
                "row_count": len(df),
                "column_count": len(df.columns),
                "columns": list(df.columns)
            }
        
        return result
    
    def chunk_large_text(self, text: str, max_tokens: int = 8192) -> List[str]:
        """Split large text into chunks for embedding"""
        # Simple chunking by sentences for now
        sentences = text.split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < max_tokens * 4:  # Approximate character limit
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks