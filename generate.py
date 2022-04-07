from collections import defaultdict, namedtuple
import os
from time import time

from jinja2 import Environment, FileSystemLoader
import requests
from bs4 import BeautifulSoup

User = namedtuple("User", "id name link")
Post = namedtuple("Post", "id poster_id likes body link")

headers = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Max-Age": "3600",
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0",  # noqa
}

scraped_posts = []
page_count = 0
t_start = time()

url = "https://www.mountainproject.com/forum/topic/122037495/climbing-memes-40"  # noqa
while url is not None:
    req = requests.get(url, headers)
    soup = BeautifulSoup(req.content, "html.parser")

    page_posts = soup.select(".message-row")
    scraped_posts += page_posts
    page_count += 1

    url = soup.select_one(".pagination > a:nth-of-type(4)").get("href")

t_scraped = time()
print(
    f"Scraped {len(scraped_posts)} posts from {page_count} pages in {t_scraped - t_start} seconds"  # noqa
)

users = []
posts = []
users_by_id = {}
users_to_posts = defaultdict(list)
for post in scraped_posts:
    is_meme_post = len(post.body.select(".forum-img:not(blockquote *)")) > 0
    if not is_meme_post:
        continue

    user_id = post.get("data-user-id")
    if user_id not in users_to_posts:
        user_name = post.get("data-user-name")
        user_link = post.select(".message-avatar > a")[1].get("href")
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


def truncate(s, n):
    if len(s) <= n:
        return s

    return f"{s[:n].strip()}..."


def get_name(post):
    ps = post.body.select("p:not(blockquote *)")
    texts = [t.getText().strip() for t in ps]
    texts = [text for text in texts if text != ""]

    return truncate(texts[0], 50) if texts else f"[{post.id}]"


def render_post(post):
    return {
        "name": get_name(post),
        "likes": post.likes,
        "link": post.link,
        "poster": users_by_id[post.poster_id].name,
    }


def render_user(user):
    likes = likes_by_user[user.id]
    posts = users_to_posts[user.id]
    num_posts = len(posts)
    return {
        "name": user.name,
        "likes": likes,
        "posts": [render_post(post_id) for post_id in posts],
        "link": user.link,
        "ratio": round(likes / num_posts, 2),
        "num_posts": num_posts,
    }


rendered_users = [render_user(user) for user in users]
user_leaderboard = sorted(
    rendered_users, key=lambda u: u["likes"], reverse=True
)
user_ratio_leaderboard = sorted(
    rendered_users, key=lambda u: u["ratio"], reverse=True
)

rendered_posts = [render_post(post) for post in posts]
post_leaderboard = sorted(
    rendered_posts, key=lambda p: p["likes"], reverse=True
)

# Load templates
root = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(root, "templates")
env = Environment(loader=FileSystemLoader(templates_dir))
template = env.get_template("index.html")


filename = os.path.join(root, "www", "index.html")
with open(filename, "w") as fh:
    fh.write(
        template.render(
            user_leaderboard=user_leaderboard,
            user_ratio_leaderboard=user_ratio_leaderboard,
            post_leaderboard=post_leaderboard,
            last_updated=t_start,
        )
    )

t_done = time()
print(f"Rendered page in {t_done - t_scraped} seconds")  # noqa
print(f"Total: {t_done - t_start} seconds")  # noqa
