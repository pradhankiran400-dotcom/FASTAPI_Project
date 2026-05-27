from fastapi import FastAPI, Request, HTTPException, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse,JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from datetime import datetime
from schemas import PostCreate, PostResponse

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
@app.get("/posts",include_in_schema=False,name="posts",)
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
    # display_posts = [
    #     {**post, "timestamp": current_time}
    #     for post in posts[start:end]
    # ]
    display_posts = []
    for post in posts[start:end]:
        naya_post = post.copy()
        naya_post["timestamp"] = current_time
        display_posts.append(naya_post)
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

@app.get("/posts/{id}",response_class=HTMLResponse,include_in_schema=False)
def get_post(id: int, request: Request):
    for post in posts:
        if post.get("id") == id:
            display_post = {
                "id" :post["id"],
                "title": post["title"],
                "content": post["content"],
                "name": post.get("name", "Guest"),
                "timestamp": post.get("timestamp", get_now_timestamp())
            }
            return templates.TemplateResponse(
                request,
                "post.html",
                {
                    "post": display_post,
                    "title": display_post["title"],
                    "views":100 #dummy number
                },
            )
    raise HTTPException(status_code=404, detail="Post not found")

@app.post("/posts",response_model = PostResponse,status_code = status.HTTP_201_CREATED)
def create_post(post: PostCreate):
    new_id = max(p["id"] for p in posts)+1 if posts else 1
    new_post = {
        "id": new_id,
        "title": post.title,
        "content": post.content,
        "name": post.name,
        "timestamp": get_now_timestamp()
    }
    posts.append(new_post)
    return new_post

@app.exception_handler(StarletteHTTPException)
def http_exception_handler(request: Request, exc: StarletteHTTPException):
    # message = (
    #     exc.detail
    #     if exc.detail
    #     else "An error occurred while processing your request."


    # )
    if exc.status_code == 404:
        message = "The page you are looking for does not exist."
    elif exc.status_code == 500:
        message = "An internal server error occurred."
    else:
        message = exc.detail if exc.detail else "An error occurred while processing your request."     
#     if request.url.path.startswith("/posts/"):
#         return JSONResponse(
#             status_code = exc.status_code,
#             content = {"detail": message}
# )
    
    return templates.TemplateResponse(
        request,
        "error.html",
        {"status_code": exc.status_code,
         "title": f"Error {exc.status_code}",
         "message": message},
        status_code=exc.status_code, #the need to set status code here is because by default it will be 200 and we want to set it to the actual error code
    )


