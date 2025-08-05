+++
date = "2025-08-05T12:35:00-05:00"
draft = false
title = "Static Website Generation using Jinja2 Templates"
show_description = false
description = "An introduction to using Jinja2 templates in Python for static website generation."
images = [ "python-jinja2-templates-post-og-image",]
tags = [ "python", "web-development", "static-website",]
hashnode-cover-image = "python-jinja2-templates-post-cover-image.jpg"
github-status = "published"
hashnode-status = "published"
hashnode-slug = "static-website-generation-using-jinja2-templates"
+++
Welcome!

About a month ago, I started my journey converting all of the web pages on the [Exploring Winnipeg Parks](https://www.exploringwinnipegparks.ca/) website from being coded manually, to being generated automatically via Python scripts.  I started with the web pages that follow a common template, such as individual pages for parks.  Today, even the home page and about page are generated via scripts.

The templating library I chose is [Jinja2](https://jinja.palletsprojects.com/).  The current version as of this writing is 3.1, which requires Python 3.7 or later.

While Jinja2 is often used to generate static websites, it can be used to generate any type of text file.

This blog post is intended to act as a primer for developers who are at least somewhat familiar with Python, but are new to the Jinja2 templating library.

## Installation

Assuming you have Python installed, and have set up a virtual environment for your project, installing Jinja2 is quite simple:
```
pip install Jinja2
pip freeze >requirements.txt
```

If you're new to Python, take a look at my [Introduction to Python](../../07/intro-to-python/) post for an explanation of virtual environments and managing dependencies.

## File and Folder Structure

In my own use case, each web page that I want to generate has its own JSON file containing the page's structured data.  Each type of page has its own Jinja2 template.  I personally like to ensure that my Python project and the root of the website are in completely different folder locations.

Let's say you're creating a static website with a home page, and product pages.  You might consider using a folder structure that looks something like the following:
```
/python/
└── website-builder/
    ├── build_home_page.py
    ├── build_product_page.py
    ├── build_website.py
    ├── product-data/
    │   ├── sku_1001.json
    │   ├── sku_1002.json
    │   └── sku_1003.json
    └── templates/
        ├── home.html
        └── product_page.html
/website/
├── index.html
└── products/
    ├── sku_1001.html
    ├── sku_1002.html
    └── sku_1003.html
```

In the above example, the `build_product_page.py` script would use the `product_page.html` template, using one of the JSON files found in the `python/website-builder/product-data/` folder.  This would build the corresponding HTML file under `/website/products/`.

**Sample Project:**  If you're looking for help getting started with Jinja2, I've created a simple Python project using Jinja2 in my companion [Python Tutorials repository](https://github.com/ryantherileyman/riley-python-tutorials) on GitHub.  The "product-website-with-jinja" folder is the project's root.

## Basic Python Script Pattern

A Python script to generate HTML pages from a Jinja2 template will generally follow these steps:
1. Initialize the template environment.
2. Assemble the data for this webpage.
3. Render the HTML output using the appropriate template.
4. Save the HTML file.

At its most basic, this looks something like the following:
```
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader("templates"))

template_data = {} # Load from a JSON file or database, for some given ID

product_template = env.get_template("product_page.html")
product_html = product_template.render(**template_data)

# TODO Save the HTML to a file
```

The `product_template.render(**template_data)` call has two asterisk characters here, which may be confusing syntax for new Python developers.  What this is actually doing is [unpacking](https://docs.python.org/3/tutorial/controlflow.html#tut-unpacking-arguments) `template_data` into individual variables, and passing those in to the `render` function, which accepts multiple arguments.  In Python, a single leading asterisk unpacks iterable data, such as lists.  A double leading asterisk unpacks mappings, such as dictionaries.

## Sources of Structured Template Data - JSON vs. Databases

I find JSON to be a great alternative to storing structured data for very small teams or indie projects, or in cases where there are at most a few hundred items to track.  If you're looking at building something larger, or have more than 2 or 3 people on your development team, you'll probably want to use a database like [MySQL](https://www.mysql.com/) instead.

Python has native support for reading and writing JSON files with the built-in `json` library.  If you find yourself wanting to control the order of properties when saving JSON files, you can use the third-party [ruamel.yaml](https://yaml.dev/doc/ruamel.yaml/) library instead.

If you're looking to use a database as the source of your structured data, Python has native support for [SQLite](https://sqlite.org/index.html) with the `sqlite3` library.  Third-party libraries are available for most popular database systems.

## Outputting Template Data Values

Most of the text in your Jinja2 template will be output as-is.  To output the value of a template data value, place it inside double curly-brace delimiters like so:
```
<h1>{{ product_name }}</h1>
```

It's quite common for template data to be contained inside a dictionary object, possibly nested several layers deep.  Use the period character to dereference the dictionary object.  It's also possible for template data values to contain special characters such as the ampersand, greater-than, or less-than character.  To prevent these characters from interfering with your HTML code, or in other contexts such as JavaScript or URLs, Jinja2 provides a number of filters that can be used to escape data values.

The full list of filters is available in the Jinja2 documentation, and you can create your own filters.  But there are a few common filters I'd like to mention for HTML pages:
- `escape` is used to deal with text inside an HTML tag or HTML attribute value.
- `tojson` will serialize values to a JSON string.  This can be used to safely output string values in JavaScript code blocks.
- `urlencode` will convert special characters into their UTF-8 percent form.  This can be used to safely output query-string parameter values.

```
<script type="text/javascript">
    let description = {{ product_data.description | to_json }};
</script>

<h1>{{ product_data.name | escape }}</h1>

<img src="get_product_image.php?color={{ product_data.default_color_string | urlencode }}">
```

## Control Structures

Jinja2 provides a number of control structures for scenarios such as conditional output, or looping over lists of items.  Control structures are delimited within `{% %}` blocks.  Otherwise, they more or less work the way a programmer would expect:
```
{% if product_data.has_color_options %}
{% for curr_color_option in product_data.color_options %}
<div class="product-color-option">
    <input type="radio" id="{{ curr_color_option.color_slug | escape }}" name="{{ curr_color_option.color_string | escape }}"/>
    <label for="{{ curr_color_option.color_slug | escape }}">{{ curr_color_option.color_label | escape }}</label>
</div>
{% endfor %}
{% endif %}
```

## Controlling Whitespace

Once you introduce control structures into your HTML code, you'll find the output may have a lot of extra whitespace, typically in the form of empty lines.  If you add a leading dash to a control structure, it will strip all whitespace before it.  If you add a trailing dash, it will strip all whitespace after it.  To strip all internal whitespace, the above example can be modified to the following:
```
{% if product_data.has_color_options -%}
{%- for curr_color_option in product_data.color_options -%}
<div class="product-color-option">
    <input type="radio" id="{{ curr_color_option.color_slug | escape }}" name="{{ curr_color_option.color_string | escape }}"/>
    <label for="{{ curr_color_option.color_slug | escape }}">{{ curr_color_option.color_label | escape }}</label>
</div>
{%- endfor -%}
{%- endif %}
```

# Conclusion

There's a whole lot more to know about Jinja2, such as template inheritance, blocks, and extensions.  This blog post was only intended as an introduction or primer, to help developers new to Jinja2 get acquainted with it.

The only aspect of Jinja2 that I struggled a little bit with during the development of my website project was controlling whitespace.  When you come from a place where you're manually editing hundreds of HTML pages, and trying to automate their generation, it's helpful to be able to tell at-a-glance if a file has changed (in Git) because the content is actually different, versus because it's now being generated automatically.  If you're starting out a new project using a templating library, precise whitespace control will likely be less important.

**Sample Project:** Take a look at my [Python Tutorials repository](https://github.com/ryantherileyman/riley-python-tutorials) on GitHub for a sample project using Jinja2.  The "product-website-with-jinja" folder is the project's root.
