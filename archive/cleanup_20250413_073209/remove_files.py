import os
import shutil

# Base directory
root_dir = "."

# Files to remove
files_to_remove = [
    os.path.join(root_dir, "src", "modules", "ai_analyzer.py"),
    os.path.join(root_dir, "src", "modules", "cache_manager.py"),
    os.path.join(root_dir, "src", "modules", "db_repository.py"),
    os.path.join(root_dir, "src", "modules", "report_generator.py"),
    os.path.join(root_dir, "src", "modules", "scheduler.py"),
    os.path.join(root_dir, "src", "modules", "webhook_server.py"),
    os.path.join(root_dir, "src", "modules", "zendesk_client.py"),
    os.path.join(root_dir, "src", "infrastructure", "utils", "service_provider.py"),
]

# Directories to remove
dirs_to_remove = [
    os.path.join(root_dir, "src", "modules", "reporters"),
]

# Remove files
for file_path in files_to_remove:
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"Removed file: {file_path}")
        except Exception as e:
            print(f"Error removing file {file_path}: {e}")
    else:
        print(f"File not found: {file_path}")

# Remove directories
for dir_path in dirs_to_remove:
    if os.path.exists(dir_path):
        try:
            shutil.rmtree(dir_path)
            print(f"Removed directory: {dir_path}")
        except Exception as e:
            print(f"Error removing directory {dir_path}: {e}")
    else:
        print(f"Directory not found: {dir_path}")

print("Legacy file removal complete!")
