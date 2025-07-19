import os
import shutil
import toml
import re

BLOG_POSTS_SOURCE_DIR = "../../blog-posts"
HUGO_CONTENT_DIR = "../../content/posts"

def extract_toml_frontmatter(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    if not (lines[0].strip() == "+++" and "+++\n" in lines[1:]):
        return None  # Not TOML frontmatter

    end_idx = lines[1:].index("+++\n") + 1
    toml_text = "".join(lines[1:end_idx])
    return toml.loads(toml_text)

def is_post_for_preview(frontmatter):
    if not frontmatter:
        return False

    if frontmatter.get("draft", False) is not True:
        return False

    status = frontmatter.get("hashnode-status", "editing")
    result = status.lower() != "published"
    return result

def sync_post_folder(src_folder, dst_folder):
    if os.path.exists(dst_folder):
        for filename in os.listdir(dst_folder):
            file_path = os.path.join(dst_folder, filename)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
    
    shutil.copytree(src_folder, dst_folder, dirs_exist_ok=True)
    print(f"Synced: {src_folder} -> {dst_folder}")

def main():
    post_folder_pattern = re.compile(rf"^{re.escape(BLOG_POSTS_SOURCE_DIR)}/\d{{4}}/\d{{2}}/[^/]+$")
    
    for root, dirs, files in os.walk(BLOG_POSTS_SOURCE_DIR):
        norm_root = root.replace("\\", "/")
        
        if not post_folder_pattern.fullmatch(norm_root):
            continue
        
        if "index.md" not in files:
            print(f"Warning: Expected index.md in {root}")
            continue
        
        src_index_path = os.path.join(root, "index.md")
        
        frontmatter = extract_toml_frontmatter(src_index_path)
        if is_post_for_preview(frontmatter):
            rel_path = os.path.relpath(root, BLOG_POSTS_SOURCE_DIR)
            dst_folder = os.path.join(HUGO_CONTENT_DIR, rel_path)
            sync_post_folder(root, dst_folder)

if __name__ == "__main__":
    main()
