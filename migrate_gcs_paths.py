#!/usr/bin/env python3
"""
Migration script to fix existing GCS file paths
Updates database records and handles path cleanup for existing files
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.financial_analysis.storage.gcs_path_utils import GCSPathManager
from src.financial_analysis.storage.database_manager import db_manager
from src.financial_analysis.storage.gcs_client import get_gcs_client


def migrate_existing_paths():
    """Migrate existing file paths to use consistent format"""
    print("🔄 Starting GCS path migration...")
    
    gcs_client = get_gcs_client()
    
    # Get all uploaded files
    with db_manager.get_session() as session:
        from src.financial_analysis.storage.database_manager import UploadedDocument
        
        documents = session.query(UploadedDocument).all()
        print(f"📊 Found {len(documents)} documents to check")
        
        updated_count = 0
        
        for doc in documents:
            original_path = doc.file_path
            
            # Skip if already clean (relative path without bucket)
            if not original_path.startswith('http') and not original_path.startswith('gs://'):
                if original_path.startswith('uploads/'):
                    print(f"   ✅ {doc.id}: Already clean - '{original_path}'")
                    continue
            
            print(f"   🔍 {doc.id}: Processing - '{original_path}'")
            
            # Extract clean blob name
            clean_blob = GCSPathManager.extract_blob_name_from_url(original_path)
            
            # Check if file exists with both old and new names
            old_exists = gcs_client.file_exists(original_path)
            new_exists = gcs_client.file_exists(clean_blob)
            
            print(f"      Old exists: {old_exists}, New exists: {new_exists}")
            
            # If file exists with old name but not new, we need to handle this
            if old_exists and not new_exists:
                # File might need renaming - for now, just update the database
                print(f"      ⚠️ File exists with old name - may need manual handling")
            
            # Update database with clean path
            doc.file_path = clean_blob
            updated_count += 1
            print(f"      ✅ Updated to: '{clean_blob}'")
        
        # Commit changes
        session.commit()
        
        print(f"\n📈 Migration complete: {updated_count} documents updated")


def verify_migration():
    """Verify the migration was successful"""
    print("\n🔍 Verifying migration...")
    
    gcs_client = get_gcs_client()
    
    with db_manager.get_session() as session:
        from src.financial_analysis.storage.database_manager import UploadedDocument
        
        documents = session.query(UploadedDocument).all()
        
        issues = []
        for doc in documents:
            path = doc.file_path
            
            # Check if path is clean
            is_clean = (not path.startswith('http') and 
                       not path.startswith('gs://') and 
                       path.startswith('uploads/'))
            
            # Check if file exists
            exists = gcs_client.file_exists(path)
            
            if not is_clean or not exists:
                issues.append({
                    'id': doc.id,
                    'filename': doc.original_filename,
                    'path': path,
                    'clean': is_clean,
                    'exists': exists
                })
        
        if issues:
            print(f"❌ Found {len(issues)} issues:")
            for issue in issues:
                print(f"   {issue['id']}: '{issue['filename']}' - '{issue['path']}' (clean: {issue['clean']}, exists: {issue['exists']})")
        else:
            print("✅ All documents have clean paths and files exist")


def list_bucket_contents():
    """List actual bucket contents for verification"""
    print("\n📋 Listing bucket contents...")
    
    try:
        gcs_client = get_gcs_client()
        
        # List all files
        all_files = gcs_client.list_files()
        print(f"   Total files in bucket: {len(all_files)}")
        
        # Group by prefix
        prefixes = {}
        for file_path in all_files:
            prefix = file_path.split('/')[0] if '/' in file_path else 'root'
            if prefix not in prefixes:
                prefixes[prefix] = 0
            prefixes[prefix] += 1
        
        print("   Files by prefix:")
        for prefix, count in prefixes.items():
            print(f"      {prefix}: {count} files")
            
        # Show first few files
        print("   First 10 files:")
        for file_path in all_files[:10]:
            print(f"      {file_path}")
            
    except Exception as e:
        print(f"   ❌ Error listing bucket: {e}")


def main():
    """Main migration process"""
    print("🚀 GCS Path Migration Tool")
    print("=" * 50)
    
    try:
        # Show current status
        list_bucket_contents()
        
        # Run migration
        migrate_existing_paths()
        
        # Verify results
        verify_migration()
        
        print("\n🎉 Migration process completed!")
        print("\nNext steps:")
        print("1. Test file upload/download functionality")
        print("2. Verify existing files are accessible")
        print("3. Monitor for any path-related errors")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()