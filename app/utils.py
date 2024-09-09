import re

import markdown
from flask import current_app
from lxml import html, etree
from lxml.html.clean import Cleaner


def str2bool(v):
    if v is not None:
        return v.lower() in ("yes", "true", "t", "1")
    else:
        return False


def is_valid_email(email) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$'
    return re.match(pattern, email) is not None


def is_valid_username(username) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+$'
    return re.match(pattern, username) is not None


def sanitize(dirty_html):
    return Cleaner(
        scripts=False,
        javascript=False,
        comments=True,
        style=False,
        links=True,
        meta=True,
        page_structure=True,
        embedded=False,
        frames=False,
        forms=False,
        kill_tags=False,
        safe_attrs_only=True,
        # remove_unknown_tags=True,
        allow_tags=['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                    'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                    'h1', 'h2', 'h3', 'p'],
        remove_tags=('span', 'font', 'div')
    ).clean_html(dirty_html)


def sanitize_html(value):
    cleaned_html = sanitize(markdown.markdown(value, output_format='html'))
    root = html.fromstring(cleaned_html)
    formatted = html.tostring(root, pretty_print=True).strip().decode('utf-8')
    current_app.logger.info(f'{value} formatted HTML: {formatted}')
    return formatted


def sanitize_text(value):
    return etree.tostring(value, pretty_print=True).strip().decode('utf-8')
