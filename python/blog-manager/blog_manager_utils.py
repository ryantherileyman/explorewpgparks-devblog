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

def is_post_being_edited(frontmatter):
    if not frontmatter:
        return False

    status = frontmatter.get("github-status", "editing")
    result = status.lower() != "published"
    return result
