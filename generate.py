import math
import os
from collections import defaultdict, namedtuple
from time import time

import requests
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

User = namedtuple("User", "id name link")
Post = namedtuple("Post", "id poster_id likes body link")
RenderContext = namedtuple(
    "RenderContext", "users posts users_by_id users_to_posts likes_by_user"
)

headers = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Max-Age": "3600",
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0",  # noqa
}

pages = [
    {
        "name": "Climbing Memes",
        "page_name": "1",
        "url": "https://www.mountainproject.com/forum/topic/107806688/climbing-memes",  # noqa
    },
    {
        "name": "Climbing Memes 2.0",
        "page_name": "2",
        "url": "https://www.mountainproject.com/forum/topic/120347968/climbing-memes-20",  # noqa
    },
    {
        "name": "Climbing Memes 3.0",
        "page_name": "3",
        "url": "https://www.mountainproject.com/forum/topic/121317188/climbing-memes-30",  # noqa
    },
    {
        "name": "Climbing Memes 4.0",
        "page_name": "4",
        "url": "https://www.mountainproject.com/forum/topic/122037495/climbing-memes-40",  # noqa
    },
    {
        "name": "Climbing Memes 5.0",
        "page_name": "index",
        "url": "https://www.mountainproject.com/forum/topic/122908344/climbing-memes-50",  # noqa
    },
]


def truncate(s, n):
    if len(s) <= n:
        return s

    return f"{s[:n].strip()}..."


def get_name(post):
    ps = post.body.select("p:not(blockquote *)")
    texts = [t.getText().strip() for t in ps]
    texts = [text for text in texts if text != ""]

    return truncate(texts[0], 50) if texts else f"[{post.id}]"


def scrape_posts(starting_url, num_pages=math.inf):
    scraped_posts = []
    page_count = 0
    t_start = time()

    url = starting_url
    while url is not None and page_count < num_pages:
        req = requests.get(url, headers)
        soup = BeautifulSoup(req.content, "html.parser")

        print("=", end="")

        page_posts = soup.select(".message-row")
        scraped_posts += page_posts
        page_count += 1

        url = soup.select_one(".pagination > a:nth-of-type(4)").get("href")

    t_finish = time()
    print(
        f"\nScraped {len(scraped_posts)} posts from {page_count} pages in {t_finish - t_start} seconds"  # noqa
    )

    return scraped_posts


def get_render_context(scraped_posts):
    users = []
    posts = []
    users_by_id = {}
    users_to_posts = defaultdict(list)
    for post in scraped_posts:
        is_meme_post = (
            post.body is not None
            and len(post.body.select(".forum-img:not(blockquote *)")) > 0
        )
        if not is_meme_post:
            continue

        user_id = post.get("data-user-id")

        if user_id not in users_to_posts:
            user_name = post.get("data-user-name")

            try:
                user_link = post.select(".message-avatar > a")[1].get("href")
            except IndexError:
                user_link = ""
            user = User(user_id, user_name, user_link)
            users.append(user)
            users_by_id[user.id] = user

        post_id = post.get("id")
        post_likes = int(post.select_one(".num-likes").getText().strip())
        post_body = post.select_one(".fr-view")
        post_link = post.select_one(".permalink").get("href")
        post = Post(post_id, user_id, post_likes, post_body, post_link)
        posts.append(post)

        users_to_posts[user_id].append(post)

    likes_by_user = defaultdict(lambda: 0)
    for post in posts:
        likes_by_user[post.poster_id] += post.likes

    return RenderContext(
        users, posts, users_by_id, users_to_posts, likes_by_user
    )


def render_post(post, ctx):
    return {
        "name": get_name(post),
        "likes": post.likes,
        "link": post.link,
        "poster": ctx.users_by_id[post.poster_id].name,
    }


def render_user(user, ctx):
    likes = ctx.likes_by_user[user.id]
    posts = ctx.users_to_posts[user.id]
    num_posts = len(posts)
    return {
        "name": user.name,
        "likes": likes,
        "posts": [render_post(post_id, ctx) for post_id in posts],
        "link": user.link,
        "ratio": round(likes / num_posts, 2),
        "num_posts": num_posts,
    }


def get_user_leaderboard(ctx):
    rendered_users = [render_user(user, ctx) for user in ctx.users]
    return sorted(rendered_users, key=lambda u: u["likes"], reverse=True)


def get_user_ratio_leaderboard(ctx):
    rendered_users = [render_user(user, ctx) for user in ctx.users]
    return sorted(rendered_users, key=lambda u: u["ratio"], reverse=True)


def get_post_leaderboard(ctx):
    rendered_posts = [render_post(post, ctx) for post in ctx.posts]
    return sorted(rendered_posts, key=lambda p: p["likes"], reverse=True)


def generate_page(page):
    root = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(root, "templates")
    env = Environment(loader=FileSystemLoader(templates_dir))
    template = env.get_template("index.html")

    t_start = time()

    scraped_posts = scrape_posts(page["url"], 2)
    t_scraped = time()

    ctx = get_render_context(scraped_posts)

    filename = os.path.join(root, "www", f"{page['page_name']}.html")
    with open(filename, "w") as fh:
        fh.write(
            template.render(
                pages=pages,
                name=page["name"],
                thread_url=page["url"],
                user_leaderboard=get_user_leaderboard(ctx),
                user_ratio_leaderboard=get_user_ratio_leaderboard(ctx),
                post_leaderboard=get_post_leaderboard(ctx),
                last_updated=t_start,
            )
        )

    t_done = time()
    print(f"Rendered page in {t_done - t_scraped} seconds")  # noqa
    print(f"Total: {t_done - t_start} seconds")  # noqa


t_start = time()
for page in pages:
    print(f"generating page for {page['name']}")
    generate_page(page)
t_done = time()
print(f"All pages total: {t_done - t_start} seconds")
