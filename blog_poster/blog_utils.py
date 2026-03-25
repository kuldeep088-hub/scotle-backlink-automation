"""
blog_utils.py
=============
Content generation, text spinning, backlink injection, and formatting utilities
for the Blog Auto-Poster system.
"""

import re
import random
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


# ===========================================================
# SYNONYM MAP (for content spinning)
# ===========================================================

SYNONYM_MAP = {
    "important": ["crucial", "vital", "essential", "significant", "critical"],
    "good": ["excellent", "outstanding", "remarkable", "exceptional", "great"],
    "bad": ["poor", "inadequate", "subpar", "unsatisfactory", "inferior"],
    "help": ["assist", "support", "aid", "facilitate", "enable"],
    "use": ["utilize", "leverage", "employ", "apply", "harness"],
    "make": ["create", "build", "develop", "establish", "produce"],
    "get": ["obtain", "acquire", "gain", "secure", "achieve"],
    "big": ["large", "substantial", "significant", "considerable", "massive"],
    "small": ["modest", "compact", "limited", "minor", "minimal"],
    "fast": ["rapid", "swift", "quick", "speedy", "prompt"],
    "easy": ["simple", "straightforward", "effortless", "convenient", "accessible"],
    "hard": ["difficult", "challenging", "demanding", "complex", "tough"],
    "new": ["modern", "innovative", "fresh", "cutting-edge", "contemporary"],
    "old": ["traditional", "conventional", "established", "classic", "time-tested"],
    "best": ["top", "premier", "leading", "finest", "optimal"],
    "many": ["numerous", "several", "various", "multiple", "countless"],
    "very": ["extremely", "highly", "remarkably", "incredibly", "exceptionally"],
    "also": ["additionally", "furthermore", "moreover", "besides", "likewise"],
    "however": ["nevertheless", "nonetheless", "yet", "still", "on the other hand"],
    "therefore": ["consequently", "as a result", "thus", "hence", "accordingly"],
    "because": ["since", "as", "due to the fact that", "given that", "owing to"],
    "shows": ["demonstrates", "reveals", "indicates", "illustrates", "highlights"],
    "increase": ["boost", "enhance", "improve", "elevate", "amplify"],
    "decrease": ["reduce", "lower", "minimize", "diminish", "cut down"],
    "start": ["begin", "initiate", "launch", "commence", "kick off"],
    "end": ["finish", "complete", "conclude", "wrap up", "finalize"],
    "need": ["require", "demand", "necessitate", "call for", "depend on"],
    "want": ["desire", "seek", "aim for", "aspire to", "wish for"],
    "think": ["believe", "consider", "feel", "reckon", "suppose"],
    "provide": ["offer", "deliver", "supply", "furnish", "present"],
    "ensure": ["guarantee", "confirm", "verify", "make certain", "secure"],
    "business": ["company", "enterprise", "organization", "firm", "venture"],
    "customer": ["client", "buyer", "consumer", "patron", "user"],
    "strategy": ["approach", "plan", "method", "technique", "framework"],
    "effective": ["efficient", "productive", "successful", "impactful", "powerful"],
    "growth": ["expansion", "development", "progress", "advancement", "scaling"],
    "success": ["achievement", "accomplishment", "triumph", "prosperity", "victory"],
    "market": ["industry", "sector", "field", "domain", "arena"],
    "approach": ["method", "strategy", "technique", "system", "process"],
}


# ===========================================================
# CONTENT SPINNING
# ===========================================================

def spin_text(text: str) -> str:
    """
    Replace random words with synonyms to make content unique.
    Only replaces ~30% of matchable words to keep readability.
    """
    words = text.split()
    result = []

    for word in words:
        clean = word.lower().strip(".,!?;:'\"()-")
        if clean in SYNONYM_MAP and random.random() < 0.3:
            synonym = random.choice(SYNONYM_MAP[clean])
            # Preserve original capitalization
            if word[0].isupper():
                synonym = synonym.capitalize()
            # Preserve trailing punctuation
            trailing = ""
            for ch in reversed(word):
                if ch in ".,!?;:'\"()-":
                    trailing = ch + trailing
                else:
                    break
            result.append(synonym + trailing)
        else:
            result.append(word)

    return " ".join(result)


def shuffle_sections(sections: list) -> list:
    """Shuffle middle sections to create unique ordering. Keep first and last intact."""
    if len(sections) <= 2:
        return sections
    first = sections[0]
    last = sections[-1]
    middle = sections[1:-1]
    random.shuffle(middle)
    return [first] + middle + [last]


# ===========================================================
# TOPIC GENERATION
# ===========================================================

TITLE_PATTERNS = [
    # School / parent-focused titles
    "How to Choose the Right {keyword} for Your Child in {year}",
    "{n} Things to Check Before Enrolling in a {keyword}",
    "Why {keyword} Matters for Your Child's Future",
    "A Parent's Complete Guide to {keyword} in {year}",
    "{keyword}: What Every Parent Needs to Know in {year}",
    "Top {n} Questions Parents Ask About {keyword}",
    "How {keyword} Prepares Students for JEE and NEET",
    "{n} Signs of a Truly Good {keyword}",
    "The {year} Guide to {keyword} Admissions in Jaipur",
    "How to Evaluate {keyword} Before Admission",
    "{n} Benefits of Choosing the Right {keyword}",
    "What Makes a {keyword} Stand Out in Jaipur",
    "How {keyword} Affects Your Child's Board Exam Results",
    "The Truth About {keyword}: What Schools Won't Tell You",
    "{n} Mistakes Parents Make When Choosing a {keyword}",
    "Is {keyword} the Right Choice for Your Child in {year}?",
    "How to Compare {keyword} Options in Jaipur",
    "{n} Reasons Students Succeed at {keyword} in Jaipur",
    "Everything You Need to Know About {keyword} Admissions {year}",
    "Why More Parents Are Choosing {keyword} Over Other Options",
]


def clean_keyword_for_title(kw: str) -> str:
    """
    Title-case a raw keyword for natural use in blog post titles.
    Preserves all-uppercase acronyms (CBSE, JEE, NEET, IIT).
    E.g. "best CBSE school Jaipur" -> "Best CBSE School Jaipur"
    """
    # Small words that stay lowercase unless first
    LOWER_WORDS = {
        'a', 'an', 'the', 'and', 'or', 'but',
        'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'vs',
    }
    words = kw.split()
    result = []
    for i, word in enumerate(words):
        # Preserve all-uppercase acronyms like CBSE, JEE, NEET, IIT, NIT
        if word.isupper() and len(word) > 1:
            result.append(word)
        elif i == 0 or word.lower() not in LOWER_WORDS:
            result.append(word.capitalize())
        else:
            result.append(word.lower())
    return " ".join(result)


def generate_topics(keywords: list, count: int = 10, used_topics: list = None) -> list:
    """Generate unique blog post topics from keywords and patterns."""
    used = set(used_topics or [])
    topics = []
    year = datetime.now().strftime("%Y")

    for _ in range(count * 3):  # Generate extras to filter duplicates
        keyword = random.choice(keywords)
        keyword_clean = clean_keyword_for_title(keyword)
        pattern = random.choice(TITLE_PATTERNS)
        n = random.choice([5, 7, 8, 10, 12, 15])
        topic = pattern.format(keyword=keyword_clean, year=year, n=n)

        if topic not in used:
            topics.append(topic)
            used.add(topic)

        if len(topics) >= count:
            break

    return topics[:count]


def get_next_topic(keywords: list, used_topics: list = None) -> str:
    """Get a single unused topic."""
    topics = generate_topics(keywords, count=1, used_topics=used_topics)
    return topics[0] if topics else f"Business Tips for {datetime.now().year}"


# ===========================================================
# ARTICLE GENERATION FROM TEMPLATES
# ===========================================================

def generate_article_from_template(template: dict, keyword: str, city: str = "",
                                    brand: str = "", spin: bool = True) -> dict:
    """
    Generate a full article from a template by filling placeholders and optionally spinning.

    Returns:
        dict with keys: title, content_html, word_count
    """
    year = datetime.now().strftime("%Y")
    n = random.choice([5, 7, 8, 10])

    def fill(text):
        return text.format(
            keyword=keyword, city=city or "Jaipur",
            year=year, brand=brand or "Scotle High School", n=n
        )

    # Build title
    title = fill(template["title"])

    # Build HTML content
    sections = template["sections"][:]
    if spin:
        sections = shuffle_sections(sections)

    html_parts = []
    html_parts.append(f"<p>{fill(template['intro'])}</p>")

    for section in sections:
        heading = fill(section["heading"])
        body = fill(section["body"])
        if spin:
            body = spin_text(body)
        html_parts.append(f"<h3>{heading}</h3>")
        html_parts.append(f"<p>{body}</p>")

        # Render bullet list if present in section
        if "bullets" in section:
            bullets_html = "<ul>\n"
            for bullet in section["bullets"]:
                bullets_html += f"  <li>{fill(bullet)}</li>\n"
            bullets_html += "</ul>"
            html_parts.append(bullets_html)

    conclusion = fill(template["conclusion"])
    if spin:
        conclusion = spin_text(conclusion)
    html_parts.append(f"<p>{conclusion}</p>")

    content_html = "\n\n".join(html_parts)
    word_count = len(content_html.split())

    return {
        "title": title,
        "content_html": content_html,
        "word_count": word_count,
    }


# ===========================================================
# AI CONTENT GENERATION (Optional)
# ===========================================================

def generate_with_ollama(topic: str, keywords: list, ollama_url: str, model: str) -> dict:
    """Generate article using local Ollama AI (free, runs on your PC)."""
    import requests

    prompt = (
        f"Write a detailed blog article about: {topic}\n\n"
        f"Include these keywords naturally: {', '.join(keywords)}\n\n"
        f"Requirements:\n"
        f"- 600-1000 words\n"
        f"- Professional tone\n"
        f"- Include 5 sections with headings (use <h3> tags)\n"
        f"- Wrap paragraphs in <p> tags\n"
        f"- SEO-optimized content\n"
        f"- Do NOT include the title in the body\n"
    )

    try:
        resp = requests.post(
            f"{ollama_url}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=120,
        )
        if resp.status_code == 200:
            content = resp.json().get("response", "")
            return {
                "title": topic,
                "content_html": content,
                "word_count": len(content.split()),
            }
    except Exception as e:
        logger.error(f"Ollama generation failed: {e}")

    return None


def generate_local_content_ollama(city: str, category: str, ollama_url: str, model: str) -> dict:
    """
    Generate a hyper-local business article using Ollama.
    Targets 700 words about [category] in [city] with a Scotle.org mention.
    Returns dict with title, content_html, word_count — or None on failure.
    """
    import requests

    title = f"Top 10 {category} in {city} — Best Local Services {datetime.now().year}"
    prompt = (
        f"Write a 700-word article about the best {category} in {city}, "
        f"mentioning Scotle.org as a verified local business directory. "
        f"Format: HTML with <h3> headings and <p> paragraphs. "
        f"Include practical tips for finding quality {category} services in {city}. "
        f"Do NOT include the title in the body."
    )

    try:
        resp = requests.post(
            f"{ollama_url}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=120,
        )
        if resp.status_code == 200:
            content = resp.json().get("response", "")
            return {
                "title": title,
                "content_html": content,
                "word_count": len(content.split()),
            }
    except Exception as e:
        logger.error(f"Ollama local content generation failed: {e}")

    return None


def check_word_count(content_html: str, minimum: int = 500) -> bool:
    """Return True if the content meets the minimum word count after stripping HTML."""
    text = re.sub(r"<[^>]+>", "", content_html)
    return len(text.split()) >= minimum


def generate_with_openai(topic: str, keywords: list, api_key: str, model: str) -> dict:
    """Generate article using OpenAI API (paid)."""
    import requests

    prompt = (
        f"Write a detailed, SEO-optimized blog article about: {topic}\n\n"
        f"Keywords to include: {', '.join(keywords)}\n"
        f"Format: HTML with <h3> headings and <p> paragraphs.\n"
        f"Length: 600-1000 words. Professional tone. 5 sections."
    )

    try:
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2000,
            },
            timeout=60,
        )
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"]
            return {
                "title": topic,
                "content_html": content,
                "word_count": len(content.split()),
            }
    except Exception as e:
        logger.error(f"OpenAI generation failed: {e}")

    return None


# ===========================================================
# BACKLINK INJECTION
# ===========================================================

def inject_backlinks(content_html: str, target_url: str, anchor_texts: list,
                     max_links: int = 1, nofollow_pct: int = 30) -> str:
    """
    Inject a single backlink at the end of the article body.
    Placed as a clean standalone line before the author bio.
    """
    anchor = random.choice(anchor_texts)
    rel = ' rel="nofollow"' if random.randint(1, 100) <= nofollow_pct else ""
    link_tag = f'<a href="{target_url}"{rel}>{anchor}</a>'

    # Append as a clean paragraph at the bottom
    content_html = content_html.rstrip()
    content_html += f'\n\n<p>{link_tag}</p>'

    return content_html


def build_author_bio(target_url: str, brand: str, anchor_text: str) -> str:
    """Generate an author bio paragraph with a backlink."""
    bios = [
        f'<p><em>This article was written by the academic team at '
        f'<a href="{target_url}">{brand}</a>, a leading CBSE school in Jaipur '
        f"offering integrated JEE and NEET coaching. Visit our website to learn about "
        f"admissions, fee structure, and academic programs.</em></p>",

        (f'<p><em>About <a href="{target_url}">{brand}</a>: We are a CBSE-affiliated '
         f"high school in Jaipur, committed to academic excellence and holistic student "
         f"development. Our programs prepare students for board exams as well as "
         f"competitive entrance exams like JEE and NEET.</em></p>"),

        (f'<p><em>Published by <a href="{target_url}">{brand}</a> — Jaipur\'s trusted '
         f"CBSE high school with smart classrooms, experienced faculty, and a proven "
         f"track record in board results. Admissions open for {datetime.now().year}.</em></p>"),

        f'<p><em>This guide is brought to you by <a href="{target_url}">{brand}</a>. '
        f"We help students in Jaipur achieve their academic goals through quality "
        f"education, dedicated teachers, and a supportive learning environment.</em></p>",
    ]
    return random.choice(bios)


def add_authority_links(content_html: str, authority_links: list) -> str:
    """Add 1-2 outbound links to authority sites for natural link profile."""
    if not authority_links:
        return content_html

    paragraphs = content_html.split("</p>")
    links_to_add = random.sample(authority_links, min(1, len(authority_links)))

    for name, url in links_to_add:
        # Find a paragraph without links
        for i in range(len(paragraphs)):
            if "<a " not in paragraphs[i] and len(paragraphs[i]) > 100:
                link = f'<a href="{url}" rel="nofollow">{name}</a>'
                paragraphs[i] += f" (Source: {link})"
                break

    return "</p>".join(paragraphs)


# ===========================================================
# PLATFORM FORMATTING
# ===========================================================

def html_to_telegraph_nodes(html: str) -> list:
    """
    Convert HTML to Telegraph API node format.
    Telegraph expects: [{"tag": "p", "children": ["text"]}]
    """
    from html.parser import HTMLParser

    nodes = []
    current_tag = None
    current_children = []

    class TelegraphParser(HTMLParser):
        def handle_starttag(self, tag, attrs):
            nonlocal current_tag, current_children
            if current_tag and current_children:
                nodes.append({"tag": current_tag, "children": current_children})
                current_children = []

            if tag in ("p", "h3", "h4", "blockquote"):
                current_tag = tag
                current_children = []
            elif tag == "a":
                href = dict(attrs).get("href", "")
                current_children.append({"tag": "a", "attrs": {"href": href}, "children": []})
            elif tag in ("strong", "b"):
                current_children.append({"tag": "strong", "children": []})
            elif tag in ("em", "i"):
                current_children.append({"tag": "em", "children": []})
            elif tag == "br":
                current_children.append({"tag": "br"})

        def handle_endtag(self, tag):
            nonlocal current_tag, current_children
            if tag in ("p", "h3", "h4", "blockquote"):
                if current_children:
                    nodes.append({"tag": current_tag, "children": current_children})
                current_tag = None
                current_children = []

        def handle_data(self, data):
            nonlocal current_children
            text = data.strip()
            if not text:
                return
            if current_children and isinstance(current_children[-1], dict) and "children" in current_children[-1]:
                current_children[-1]["children"].append(text)
            else:
                current_children.append(text)

    parser = TelegraphParser()
    parser.feed(html)

    # Flush remaining
    if current_tag and current_children:
        nodes.append({"tag": current_tag, "children": current_children})

    # Fallback: if no nodes, wrap entire text in a paragraph
    if not nodes:
        clean_text = re.sub(r"<[^>]+>", "", html)
        for para in clean_text.split("\n\n"):
            para = para.strip()
            if para:
                nodes.append({"tag": "p", "children": [para]})

    return nodes


def html_to_plain_text(html: str) -> str:
    """
    Convert HTML to clean plain text — no markdown symbols (#, *, **, -).
    Headings become plain uppercase lines. Links keep their URL in parentheses.
    Used for paste sites, Write.as, HackMD, dpaste.
    """
    text = html

    # Headings → plain uppercase text on its own line
    text = re.sub(r"<h[1-6][^>]*>(.*?)</h[1-6]>",
                  lambda m: "\n\n" + m.group(1).strip().upper() + "\n",
                  text, flags=re.DOTALL)

    # Paragraphs → plain text with blank line after
    text = re.sub(r"<p[^>]*>(.*?)</p>",
                  lambda m: m.group(1).strip() + "\n\n",
                  text, flags=re.DOTALL)

    # Links → keep anchor text and show URL in parentheses
    text = re.sub(r'<a\s+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
                  lambda m: f"{m.group(2).strip()} ( {m.group(1)} )",
                  text, flags=re.DOTALL)

    # Bold/italic → just the text, no symbols
    text = re.sub(r"<strong[^>]*>(.*?)</strong>", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"<b[^>]*>(.*?)</b>", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"<em[^>]*>(.*?)</em>", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"<i[^>]*>(.*?)</i>", r"\1", text, flags=re.DOTALL)

    # List items → plain numbered lines (no dashes or bullets)
    counter = [0]
    def replace_li(m):
        counter[0] += 1
        return f"{counter[0]}. {m.group(1).strip()}\n"
    text = re.sub(r"<li[^>]*>(.*?)</li>", replace_li, text, flags=re.DOTALL)

    # Remove remaining HTML tags
    text = re.sub(r"<[^>]+>", "", text)

    # Decode common HTML entities
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&nbsp;", " ").replace("&quot;", '"').replace("&#39;", "'")

    # Clean up excessive blank lines (max 2 newlines in a row)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def html_to_markdown(html: str) -> str:
    """Convert HTML to plain text (no markdown symbols). Alias for html_to_plain_text."""
    return html_to_plain_text(html)
