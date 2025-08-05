from dotenv import load_dotenv
import os
import re
import requests
from blog_manager_utils import BLOG_POSTS_SOURCE_DIR, extract_toml, save_toml

load_dotenv()

GITHUB_PAGES_BLOG_SLUG = os.getenv("GITHUB_PAGES_BLOG_SLUG")

HASHNODE_API_URL = "https://gql.hashnode.com"
HASHNODE_TOKEN = os.getenv("HASHNODE_TOKEN")
HASHNODE_HOST = os.getenv("HASHNODE_HOST")

def create_headers():
    result = {
        "Authorization": HASHNODE_TOKEN
    }
    return result

def sanitize_tag_slug(tag_slug):
    result = re.sub(r'[^A-Za-z_]', '_', tag_slug)
    return result

def is_post_unpublished(frontmatter):
    if not frontmatter:
        return False
    
    status = frontmatter.get("hashnode-status", "unpublished")
    result = status.lower() == "unpublished"
    return result

def convert_markdown_image_paths(md_content, canonicalUrl):
    def replacer(match):
        alt_text = match.group(1)
        image_rel_path = match.group(2)
        
        if image_rel_path.startswith(('http://', 'https://')):
            return match.group(0)
        
        full_url = canonicalUrl + image_rel_path
        return f'![{alt_text}]({full_url})'
    
    result = re.sub(r'!\[(.*?)\]\((.*?)\)', replacer, md_content)
    return result

def is_relative_blog_post_link(relative_path):
    parts = relative_path.rstrip("/").split("/")
    
    is_same_month_blog_post = ( len(parts) == 2 and parts[0] == ".." )
    is_diff_month_blog_post = ( len(parts) == 4 and parts[0] == ".." and parts[1] == ".." and parts[2].isdigit() and len(parts[2]) == 2 )
    id_diff_year_blog_post = ( len(parts) == 6 and parts[0] == ".." and parts[1] == ".." and parts[2] == ".." and parts[3].isdigit() and len(parts[3]) == 4 and parts[4].isdigit() and len(parts[4]) == 2 )
    
    result = is_same_month_blog_post or is_diff_month_blog_post or id_diff_year_blog_post
    return result

def convert_markdown_relative_link_paths(md_content, blog_post_path_str):
    def replacer(match):
        alt_text = match.group(1)
        link_rel_path = match.group(2).rstrip("/")
        
        if not is_relative_blog_post_link(link_rel_path):
            return match.group(0)
        
        relative_post_index_path = os.path.join(blog_post_path_str, link_rel_path, "index.md")
        
        if not os.path.exists(relative_post_index_path):
            return match.group(0)
        
        relative_post_index_toml = extract_toml(relative_post_index_path)
        relative_post_hashnode_slug = relative_post_index_toml["frontmatter"]["hashnode-slug"]
        if not relative_post_index_toml["frontmatter"]["hashnode-slug"]:
            return match.group(0)
        
        full_url = "https://" + HASHNODE_HOST + "/" + relative_post_hashnode_slug
        return f'[{alt_text}]({full_url})'
    
    result = re.sub(r'(?<!\!)\[([^\]]+)\]\((\.\./[^)]+)\)', replacer, md_content)
    return result

def convert_markdown_paths(blog_post_path_str, index_toml, canonicalUrl):
    result = "".join(index_toml["markdown_lines"])
    result = convert_markdown_image_paths(result, canonicalUrl)
    result = convert_markdown_relative_link_paths(result, blog_post_path_str)
    return result

def build_publish_ids_gql(frontmatter):
    result = "query PublishIds {\n"
    
    result = result + "  publication(host: \"" + HASHNODE_HOST + "\") {\n"
    result = result + "    id\n"
    result = result + "  }\n"
    
    if frontmatter["tags"]:
        for curr_tag_slug in frontmatter["tags"]:
            tag_as_varname = sanitize_tag_slug(curr_tag_slug)
            result = result + "  tag_" + tag_as_varname + ": tag(slug: \"" + curr_tag_slug + "\") {\n"
            result = result + "    id\n"
            result = result + "  }\n"
    
    result = result + "}"
    
    return result

def request_publish_ids(frontmatter):
    publish_ids_query = build_publish_ids_gql(frontmatter)
    
    headers = create_headers()
    payload = {
        "query": publish_ids_query
    }
    
    response = requests.post(HASHNODE_API_URL, json=payload, headers=headers)
    result = response.json()
    return result

def build_publish_post_gql():
    result = "mutation PublishPost($input: PublishPostInput!) {\n"
    result = result + "  publishPost(input: $input) {\n"
    result = result + "    post {\n"
    result = result + "      id\n"
    result = result + "      slug\n"
    result = result + "    }\n"
    result = result + "  }\n"
    result = result + "}"
    
    return result

def build_publish_post_variables(blog_post_path_str, index_toml, publish_ids_response):
    canonicalUrl = "https://ryantherileyman.github.io/" + GITHUB_PAGES_BLOG_SLUG + "/posts/" + blog_post_path_str.removeprefix("../../blog-posts/") + "/"
    converted_md = convert_markdown_paths(blog_post_path_str, index_toml, canonicalUrl)
    result = {
        "input": {
            "publicationId": publish_ids_response["publication"]["id"],
            "title": index_toml["frontmatter"]["title"],
            "publishedAt": index_toml["frontmatter"]["date"],
            "originalArticleURL": canonicalUrl,
            "metaTags": {
                "title": index_toml["frontmatter"]["title"]
            },
            "contentMarkdown": converted_md
        }
    }
    
    if index_toml["frontmatter"]["description"]:
        result["input"]["metaTags"]["description"] = index_toml["frontmatter"]["description"]
    
    if index_toml["frontmatter"]["images"] and len(index_toml["frontmatter"]["images"]) > 0:
        result["input"]["metaTags"]["image"] = canonicalUrl + index_toml["frontmatter"]["images"][0]
    
    if index_toml["frontmatter"]["hashnode-cover-image"]:
        result["input"]["coverImageOptions"] = {
            "coverImageURL": canonicalUrl + index_toml["frontmatter"]["hashnode-cover-image"]
        }
    
    if index_toml["frontmatter"]["tags"]:
        tags = []
        
        for curr_tag_slug in index_toml["frontmatter"]["tags"]:
            tag_as_varname = "tag_" + sanitize_tag_slug(curr_tag_slug)
            if publish_ids_response[tag_as_varname]:
                curr_tag_obj = {
                    "id": publish_ids_response[tag_as_varname]["id"]
                }
                tags.append(curr_tag_obj)
        
        result["input"]["tags"] = tags
    
    return result

def request_publish_post(blog_post_path_str, index_toml, publish_ids_response):
    headers = create_headers()
    payload = {
        "query": build_publish_post_gql(),
        "variables": build_publish_post_variables(blog_post_path_str, index_toml, publish_ids_response)
    }
    
    response = requests.post(HASHNODE_API_URL, json=payload, headers=headers)
    result = response.json()
    return result

def update_blog_post_frontmatter(src_index_path, index_toml, publish_post_response):
    index_toml["frontmatter"]["hashnode-status"] = "published"
    index_toml["frontmatter"]["hashnode-slug"] = publish_post_response["publishPost"]["post"]["slug"]
    
    save_toml(src_index_path, index_toml)

def publish_blog_post(blog_post_root):
    src_index_path = os.path.join(blog_post_root, "index.md")
    
    index_toml = extract_toml(src_index_path)
    if is_post_unpublished(index_toml["frontmatter"]):
        print(f"Will publish post: {src_index_path}")
        
        print("  Retrieving necessary data from Hashnode...")
        publish_ids_response = request_publish_ids(index_toml["frontmatter"])
        if "errors" in publish_ids_response:
            print("Error attempting to retrieve publication ID:")
            print(publish_ids_response["errors"])
            return
        
        print("  Publishing post...")
        publish_post_response = request_publish_post(blog_post_root, index_toml, publish_ids_response["data"])
        if "errors" in publish_post_response:
            print("Error attempting to publish post:")
            print(publish_post_response["errors"])
            return
        
        print(f"Success!  Updating hashnode-related frontmatter in {src_index_path}")
        update_blog_post_frontmatter(src_index_path, index_toml, publish_post_response["data"])

def main():
    post_folder_pattern = re.compile(rf"^{re.escape(BLOG_POSTS_SOURCE_DIR)}/\d{{4}}/\d{{2}}/[^/]+$")
    
    for root, dirs, files in os.walk(BLOG_POSTS_SOURCE_DIR):
        norm_root = root.replace("\\", "/")
        
        if not post_folder_pattern.fullmatch(norm_root):
            continue
        
        if "index.md" not in files:
            continue
        
        publish_blog_post(norm_root)

if __name__ == "__main__":
    main()
