from langchain_core.tools import tool
import subprocess
import re

@tool
def read_file(file_path: str) -> str:
    """Read the content of a text file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()
@tool
def write_file(file_path: str, content: str) -> str:
    """Write content into a text file (overwrites if it already exists)."""
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)
    return f"Content successfully written to {file_path}"

@tool
def create_file(file_path: str, content: str) -> str:
    """Create a new text file with the given content."""
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)
    return f"File {file_path} has been created with the provided content."

@tool
def delete_file(file_path: str) -> str:
    """Delete a text file."""
    import os
    if os.path.exists(file_path):
        os.remove(file_path)
        return f"File {file_path} has been deleted."
    else:
        return f"File {file_path} does not exist."
    
@tool
def get_all_file_paths(directory: str) -> list:
    """Get all file paths inside a directory (recursively)."""
    import os
    file_paths = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_paths.append(os.path.join(root, file))
    return file_paths

@tool
def create_folder(folder_path: str) -> str:
    """Create a new folder (including parent directories if needed)."""
    import os
    os.makedirs(folder_path, exist_ok=True)
    return f"Folder {folder_path} has been created."

@tool
def delete_folder(folder_path: str) -> str:
    """Delete a folder and all its contents."""
    import os
    import shutil
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
        return f"Folder {folder_path} has been deleted."
    else:
        return f"Folder {folder_path} does not exist."

@tool
def run_command(command: str) -> str:
    """Run a shell command and return its output (or error)."""
    try:
        result = subprocess.run(
            command.replace('\\', '/'), 
            shell=True,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return f"Command executed successfully:\n{result.stdout}"
        else:
            return f"Error executing command:\n{result.stderr}"
    except Exception as e:
        return f"Exception: {str(e)}"

tools = [read_file, write_file, create_file, delete_file, get_all_file_paths, create_folder, delete_folder,run_command]
