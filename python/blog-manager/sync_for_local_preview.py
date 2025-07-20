import os
import shutil
from blog_manager_utils import extract_toml_frontmatter
import re

BLOG_POSTS_SOURCE_DIR = "../../blog-posts"
HUGO_CONTENT_DIR = "../../content/posts"

def is_post_being_edited(frontmatter):
    if not frontmatter:
        return False

    status = frontmatter.get("github-status", "editing")
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
        if is_post_being_edited(frontmatter):
            rel_path = os.path.relpath(root, BLOG_POSTS_SOURCE_DIR)
            dst_folder = os.path.join(HUGO_CONTENT_DIR, rel_path)
            sync_post_folder(root, dst_folder)

if __name__ == "__main__":
    main()
