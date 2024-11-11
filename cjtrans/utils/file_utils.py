

def write_to_file(path: str, content: str):
    with open(path, 'w', encoding="utf-8") as file:
        file.write(content)

def read_file(path: str) -> str:
    try:
        with open(path, 'r', encoding="utf-8") as file:
            content = file.read()
        return content
    except FileNotFoundError:
        return "File not found"
    except Exception as e:
        return f"An error occurred: {str(e)}"