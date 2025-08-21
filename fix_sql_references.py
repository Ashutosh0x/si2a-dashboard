#!/usr/bin/env python3
"""
Fix SQL file references to use correct project ID
"""

import os
import re

PROJECT_ID = "shadow-it-incident-autopilot"

def fix_sql_file(file_path):
    """Fix project references in SQL file"""
    print(f"Fixing {file_path}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace all si2a. references with ${PROJECT_ID}.si2a_
    # This handles both dataset and function references
    content = re.sub(r'`si2a\.', f'`${{PROJECT_ID}}.si2a_', content)
    
    # Write back the file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Fixed {file_path}")

def main():
    """Fix all SQL files"""
    sql_files = [
        "sql/01_ddl_tables.sql",
        "sql/02_embeddings_and_vector_search.sql", 
        "sql/03_generative_ai_architect.sql",
        "sql/04_multimodal_pioneer.sql"
    ]
    
    for sql_file in sql_files:
        if os.path.exists(sql_file):
            fix_sql_file(sql_file)
        else:
            print(f"⚠️ File not found: {sql_file}")

if __name__ == "__main__":
    main()
