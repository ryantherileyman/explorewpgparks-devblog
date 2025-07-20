import toml

BLOG_POSTS_SOURCE_DIR = "../../blog-posts"
HUGO_CONTENT_DIR = "../../content/posts"

def extract_toml_frontmatter(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    if not (lines[0].strip() == "+++" and "+++\n" in lines[1:]):
        return None  # Not TOML frontmatter

    end_idx = lines[1:].index("+++\n") + 1
    toml_text = "".join(lines[1:end_idx])
    result = toml.loads(toml_text)
    return result

def extract_toml(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    if not (lines[0].strip() == "+++" and "+++\n" in lines[1:]):
        return None

    end_idx = lines[1:].index("+++\n") + 1
    frontmatter_text = "".join(lines[1:end_idx])
    
    first_markdown_idx = end_idx + 1
    
    result = {
        "frontmatter": toml.loads(frontmatter_text),
        "markdown_lines": lines[first_markdown_idx:]
    }
    return result

def save_toml(output_path, toml_content):
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("+++\n")
        f.write(toml.dumps(toml_content["frontmatter"]))
        f.write("+++\n")
        
        for curr_markdown_line in toml_content["markdown_lines"]:
            f.write(curr_markdown_line)

def is_post_being_edited(frontmatter):
    if not frontmatter:
        return False

    status = frontmatter.get("github-status", "editing")
    result = status.lower() != "published"
    return result
