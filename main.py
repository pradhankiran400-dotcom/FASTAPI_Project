from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static") #first is the url path and second is the directory where the static files are located

templates = Jinja2Templates(directory="templates")

def get_now_timestamp():
    return datetime.now().strftime("%b %d, %Y %I:%M %p")

posts : list[dict] = [
    {
        "id": 1,
        "title": "First Post",
        "content": "This is the content of the first post",
        "name": "Kiran",
        "timestamp": get_now_timestamp()
    },
    {
        "id": 2,
        "title": "Second Post",
        "content": "This is the content of the second post",
        "name" : "Rahul"
    },
    {
        "id": 3,
        "title": "Third Post",
        "content": "This is the content of the third post",
        "name": "Priya"
    }

]

@app.get("/",include_in_schema=False,name="home")
@app.get("/posts",include_in_schema=False,name="posts")
def home(request: Request):
    page_size = 5
    page = int(request.query_params.get("page_no", 1) or 1)
    total_posts = len(posts)
    start = (page - 1) * page_size
    end = start + page_size

    if start >= total_posts:
        page = 1
        start = 0
        end = page_size

    current_time = datetime.now().strftime("%b %d, %Y %I:%M %p")
    display_posts = [
        {**post, "timestamp": current_time}
        for post in posts[start:end]
    ]
    next_page = page + 1 if end < total_posts else 1
    show_refresh = total_posts > page_size

    return templates.TemplateResponse(
        request,
        "home.html",
        {
            "posts": display_posts,
            "title": "HOME🏠",
            "next_page": next_page,
            "show_refresh": show_refresh,
            "base_path": request.url.path,
        },
    )

@app.get("/posts/{id}")
def get_post(id: int, request: Request):
    for post in posts:
        if post.get("id") == id:
            display_post = {**post, "timestamp": post.get("timestamp") or get_now_timestamp()}
            return templates.TemplateResponse(
                request,
                "post.html",
                {
                    "post": display_post,
                    "title": display_post["title"],
                },
            )
    raise HTTPException(status_code=404, detail="Post not found")
