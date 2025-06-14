import re

def make_valid_filename(s: str, replacement: str = "_") -> str:
    """
    Converts a string into a valid filename by removing or replacing invalid characters.
    """
    # Remove invalid characters: / \ : * ? " < > |
    s = re.sub(r'[<>:"/\\|?*\n\r\t]', replacement, s)
    
    # Optionally strip leading/trailing whitespace and dots
    s = s.strip().strip(".")
    
    # Limit filename length if needed (optional)
    return s[:255]
