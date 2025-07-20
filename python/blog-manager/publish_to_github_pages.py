import sys
import os
import subprocess
import toml
from pathlib import Path
from blog_manager_utils import BLOG_POSTS_SOURCE_DIR, HUGO_CONTENT_DIR, extract_toml_frontmatter, extract_toml, save_toml, is_post_being_edited
import re

BLOG_POSTS_SOURCE_DIR = "../../blog-posts"
HUGO_CONTENT_DIR = "../../content/posts"
HUGO_DOCS_DIR = "../../docs"

MAX_COMMIT_LINE_LENGTH = 80

def shorten_with_ellipsis(text, max_length):
    if len(text) <= max_length:
        return text

    if ' ' not in text:
        return text[:max_length - 1] + "..."

    # Cut off at the max_length
    truncated = text[:max_length].rstrip()

    # Find the last space within the truncated portion
    last_space = truncated.rfind(' ')
    if last_space == -1 or last_space < max_length // 2:
        return truncated + "..."
    
    result = truncated[:last_space] + "..."
    return result

def get_current_branch():
    git_output = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True
    )
    result = git_output.stdout.strip()
    return result

def build_hugo_docs():
    repo_root = Path(__file__).resolve().parents[2]
    subprocess.run(["hugo", "--minify", "-d", "docs"], cwd=repo_root, check=True)

def gather_hugo_docs_changed_files():
    results = []
    
    for root, dirs, files in os.walk(HUGO_DOCS_DIR):
        norm_root = root.replace("\\", "/")
        docs_folder = norm_root.removeprefix("../../")
        
        for curr_file in files:
            docs_file_path_str = docs_folder + "/" + curr_file
            results.append(docs_file_path_str)
    
    return results

def stage_files(file_list):
    for curr_file in file_list:
        subprocess.run(["git", "add", "../../" + curr_file], check=True)

def commit_blog_posts(edited_blog_posts):
    command_line_array = [ "git", "commit" ]
    
    if edited_blog_posts["blog_post_count"] == 1:
        title_text = shorten_with_ellipsis(edited_blog_posts['blog_post_titles'][0], MAX_COMMIT_LINE_LENGTH)
        
        command_line_array.append("-m")
        command_line_array.append(f"Publish Post: {title_text}")
    
    if edited_blog_posts["blog_post_count"] > 1:
        command_line_array.append("-m")
        command_line_array.append(f"Publish {edited_blog_posts['blog_post_count']} blog posts")
        
        for curr_title in edited_blog_posts["blog_post_titles"][:3]:
            title_text = shorten_with_ellipsis(curr_title, MAX_COMMIT_LINE_LENGTH)
            
            command_line_array.append("-m")
            command_line_array.append(f"Post: {title_text}")
        
        if edited_blog_posts["blog_post_count"] > 3:
            extra_count = edited_blog_posts["blog_post_count"] - 3
            
            command_line_array.append("-m")
            command_line_array.append(f"... and {extra_count} more post(s)")
    
    subprocess.run(command_line_array, check=True)

def push_to_origin():
    subprocess.run(["git", "push", "origin", "main"], check=True)

def gather_all_blog_post_files(blog_post_folder):
    result = {
        "file_list": [],
        "missing_content_file_list": []
    }
    
    for root, dirs, files in os.walk(blog_post_folder):
        norm_root = root.replace("\\", "/")
        blog_post_folder = norm_root.removeprefix("../../")
        
        for curr_file in files:
            blog_post_file_path_str = blog_post_folder + "/" + curr_file
            result["file_list"].append(blog_post_file_path_str)
            
            content_file_path_str = "content/posts/" + blog_post_file_path_str.removeprefix("blog-posts/")
            content_file_path = Path("../../" + content_file_path_str)
            if content_file_path.is_file():
                result["file_list"].append(content_file_path_str)
            else:
                result["missing_content_file_list"].append(content_file_path_str)
    
    return result

def gather_edited_blog_posts():
    post_folder_pattern = re.compile(rf"^{re.escape(BLOG_POSTS_SOURCE_DIR)}/\d{{4}}/\d{{2}}/[^/]+$")
    
    result = {
        "blog_post_count": 0,
        "blog_post_titles": [],
        "blog_post_index_files": [],
        "blog_post_files": [],
        "missing_content_files": []
    }
    
    for root, dirs, files in os.walk(BLOG_POSTS_SOURCE_DIR):
        norm_root = root.replace("\\", "/")
        
        if not post_folder_pattern.fullmatch(norm_root):
            continue
        
        if "index.md" not in files:
            continue
        
        src_index_path = os.path.join(root, "index.md")
        
        frontmatter = extract_toml_frontmatter(src_index_path)
        if is_post_being_edited(frontmatter):
            result["blog_post_count"] = result["blog_post_count"] + 1
            result["blog_post_index_files"].append(src_index_path)
            
            result["blog_post_titles"].append(frontmatter.get("title"))
            
            blog_post_files = gather_all_blog_post_files(norm_root)
            for curr_file in blog_post_files["file_list"]:
                result["blog_post_files"].append(curr_file)
            for curr_file in blog_post_files["missing_content_file_list"]:
                result["missing_content_files"].append(curr_file)
    
    return result

def main():
    curr_branch = get_current_branch()
    if curr_branch != "main":
        print("Must be on the main branch!")
        sys.exit(1)
    
    edited_blog_posts = gather_edited_blog_posts()
    
    if len(edited_blog_posts["missing_content_files"]) > 0:
        print("Not all blog post files have been sync'ed to the /content/posts/ folder:")
        for curr_file in edited_blog_posts["missing_content_files"]:
            print(f"  {curr_file}")
        
        sys.exit(1)
    
    if edited_blog_posts["blog_post_count"] == 0:
        print("No blog posts to publish")
    
    if edited_blog_posts["blog_post_count"] > 0:
        print(f"Publishing {edited_blog_posts['blog_post_count']} post(s):")
        for curr_title in edited_blog_posts["blog_post_titles"]:
            print(f"  {curr_title}")
        
        print("Staging blog post files...")
        stage_files(edited_blog_posts["blog_post_files"])
        
        print("Rebuilding the docs folder...")
        build_hugo_docs()
        docs_changed_files = gather_hugo_docs_changed_files()
        stage_files(docs_changed_files)
        
        print("Committing blog post files...")
        commit_blog_posts(edited_blog_posts)
        
        print("Pushing to origin...")
        push_to_origin()
        
        print("Updating github-status in blog post index files:")
        for curr_blog_post_index_path in edited_blog_posts["blog_post_index_files"]:
            curr_toml = extract_toml(curr_blog_post_index_path)
            curr_toml["frontmatter"]["github-status"] = "published"
            
            print(f"  {curr_blog_post_index_path}")
            save_toml(curr_blog_post_index_path, curr_toml)

if __name__ == "__main__":
    main()
