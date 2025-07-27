#!/usr/bin/env python3
"""
Validation script for GCS path fix
Tests the path consistency across all services
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.financial_analysis.storage.gcs_path_utils import GCSPathManager


def test_path_consistency():
    """Test path consistency across the platform"""
    print("🧪 Testing GCS Path Consistency...")
    
    # Test 1: Basic normalization
    print("\n1. Testing basic normalization:")
    test_cases = [
        ("uploads/test.xlsx", "uploads/test.xlsx"),
        ("/uploads/test.xlsx", "uploads/test.xlsx"),
        ("tum-gen-ai-24-uploads/uploads/test.xlsx", "uploads/test.xlsx"),
        ("tum-gen-ai-storage/documents/file.json", "documents/file.json"),
    ]
    
    for input_path, expected in test_cases:
        result = GCSPathManager.normalize_blob_name(input_path)
        status = "✅" if result == expected else "❌"
        print(f"   {status} '{input_path}' -> '{result}' (expected: '{expected}')")
    
    # Test 2: URL extraction
    print("\n2. Testing URL extraction:")
    url_cases = [
        ("https://storage.googleapis.com/tum-gen-ai-24-uploads/uploads/test.xlsx", "uploads/test.xlsx"),
        ("https://tum-gen-ai-24-uploads.storage.googleapis.com/uploads/test.xlsx", "uploads/test.xlsx"),
        ("gs://tum-gen-ai-24-uploads/uploads/test.xlsx", "uploads/test.xlsx"),
        ("uploads/test.xlsx", "uploads/test.xlsx"),
    ]
    
    for url, expected in url_cases:
        result = GCSPathManager.extract_blob_name_from_url(url)
        status = "✅" if result == expected else "❌"
        print(f"   {status} '{url}' -> '{result}'")
    
    # Test 3: Upload/download flow
    print("\n3. Testing upload/download flow:")
    filename = "test_report.xlsx"
    file_id = "123e4567-e89b-12d3-a456-426614174000"
    
    # Create upload blob
    upload_blob = GCSPathManager.get_upload_blob_name(filename, file_id)
    print(f"   Upload blob: {upload_blob}")
    
    # Create GCS URL
    gcs_url = GCSPathManager.create_gcs_url("tum-gen-ai-24-uploads", upload_blob)
    print(f"   GCS URL: {gcs_url}")
    
    # Extract for download
    download_blob = GCSPathManager.extract_blob_name_from_url(gcs_url)
    print(f"   Download blob: {download_blob}")
    
    # Check consistency
    if upload_blob == download_blob:
        print("   ✅ Path consistency maintained")
    else:
        print("   ❌ Path inconsistency detected")
    
    # Test 4: Edge case - bucket duplication
    print("\n4. Testing bucket duplication fix:")
    problematic_urls = [
        "https://storage.googleapis.com/tum-gen-ai-24-uploads/tum-gen-ai-24-uploads/uploads/file.xlsx",
        "gs://tum-gen-ai-24-uploads/tum-gen-ai-24-uploads/uploads/file.xlsx",
    ]
    
    for url in problematic_urls:
        extracted = GCSPathManager.extract_blob_name_from_url(url)
        normalized = GCSPathManager.normalize_blob_name(extracted)
        print(f"   Original: {url}")
        print(f"   Extracted: {extracted}")
        print(f"   Normalized: {normalized}")
        expected = "uploads/file.xlsx"
        status = "✅" if normalized == expected else "❌"
        print(f"   {status} Expected: {expected}")
    
    # Test 5: Document storage paths
    print("\n5. Testing document storage paths:")
    doc_id = "doc-123"
    
    doc_blob = GCSPathManager.get_document_blob_name("report.json", doc_id)
    meta_blob = GCSPathManager.get_metadata_blob_name(doc_id)
    
    print(f"   Document blob: {doc_blob}")
    print(f"   Metadata blob: {meta_blob}")
    
    # Test 6: Validation
    print("\n6. Testing validation:")
    valid_paths = [
        "uploads/test.xlsx",
        "documents/123_report.json",
        "metadata/abc_meta.json",
    ]
    invalid_paths = [
        "",
        "uploads/../test.xlsx",
        "uploads\\\\test.xlsx",
    ]
    
    for path in valid_paths:
        valid = GCSPathManager.is_valid_blob_name(path)
        status = "✅" if valid else "❌"
        print(f"   {status} Valid: '{path}' -> {valid}")
    
    for path in invalid_paths:
        valid = GCSPathManager.is_valid_blob_name(path)
        status = "✅" if not valid else "❌"
        print(f"   {status} Invalid: '{path}' -> {valid}")
    
    print("\n🎯 GCS Path Validation Complete!")


if __name__ == "__main__":
    test_path_consistency()