def filter_files(files: list[str]) -> list[str]:
    """
    Filters out files that are not in the specified format.
    
    Args:
        files (list[str]): List of file names to filter.
        
    Returns:
        list[str]: Filtered list of file names.
    """
    valid_extensions = {'.pdf', '.pptx', '.docx', '.doc'}
    return [file for file in files if any(file.endswith(ext) for ext in valid_extensions)]