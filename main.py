from fastapi import Depends, FastAPI, Request, HTTPException, Form, status
from typing import Annotated
from fastapi.responses import HTMLResponse, RedirectResponse,JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session

import models
from database import Base, engine, get_db
from schemas import PostCreate, PostResponse, UserResponse, PostUpdate, UserUpdate

Base.metadata.create_all(bind=engine) #to create the tables in the database based on the models defined in models.py

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static") #first is the url path and second is the directory where the static files are located
app.mount("/media", StaticFiles(directory="media"), name="media") #for profile pictures
templates = Jinja2Templates(directory="templates")

def get_now_timestamp():
    return datetime.now().strftime("%b %d, %Y %I:%M %p")

@app.get("/", name="home")
@app.get("/posts", name="posts")
def home(request: Request,db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post))
    posts = result.scalars().all()
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
    display_posts = posts[start:end]
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

@app.post("/users",
          response_model = UserResponse,
          status_code = status.HTTP_201_CREATED)
def create_user(username: Annotated[str, Form()], email: Annotated[str, Form()],db: Session = Depends(get_db)):
    result = db.execute(select(models.User).where(models.User.username == username))
    existing_user = result.scalars().first()
    if existing_user:
        return RedirectResponse(url="/?error=username_exists", status_code=status.HTTP_303_SEE_OTHER)
    result = db.execute(select(models.User).where(models.User.email == email))
    existing_email = result.scalars().first()
    if existing_email:
        return RedirectResponse(url="/?error=email_exists", status_code=status.HTTP_303_SEE_OTHER)
    new_user = models.User(username=username, email=email)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
    
@app.get("/users/{user_id}",response_model=UserResponse)
def get_user(user_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/posts/{id}", response_class=HTMLResponse)
def get_post(id: int, request: Request,db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post).where(models.Post.id == id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
 
    return templates.TemplateResponse(
        request,
        "post.html",
        {
            "post": post,
            "title": post.title,
            "views": 100,  # dummy number
        },
    )

@app.get("/users/{user_id}/posts", response_class=HTMLResponse)
def user_post_page(
    requests : Request,
    user_id : int,
    db: Annotated[Session, Depends(get_db)]
):
    result = db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    result = db.execute(select(models.Post).where(models.Post.user_id == user_id))
    posts = result.scalars().all()
    return templates.TemplateResponse(
        requests,
        "user_posts.html",
        {
            "posts": posts,
            "title": f"{user.username}'s Posts",
            "user": user
        },
    )


@app.post("/posts",response_model = PostResponse,status_code = status.HTTP_201_CREATED)
def create_post(post: PostCreate, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.id == post.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
 
    new_post = models.Post(
        title=post.title,
        content=post.content,
        user_id=post.user_id,
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post

@app.put("/posts/{id}", response_model=PostResponse)
def update_post(id: int, post_update: PostUpdate, db: Annotated[Session, Depends(get_db)]):
    # Fetch the post from the database
    result = db.execute(select(models.Post).where(models.Post.id == id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # If the post is being reassigned to a different user, verify the new user exists
    if post_update.user_id != post.user_id:
        result = db.execute(select(models.User).where(models.User.id == post_update.user_id))
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
    post.title = post_update.title
    post.content = post_update.content
    post.user_id = post_update.user_id
    
    db.commit()
    db.refresh(post)
    return post

@app.patch("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_update: UserUpdate, db: Annotated[Session, Depends(get_db)]):
    # Fetch the user from the database
    result = db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if the username is being updated, and if so, check for uniqueness collisions
    if user_update.username is not None and user_update.username != user.username:
        result = db.execute(select(models.User).where(models.User.username == user_update.username))
        existing_user = result.scalars().first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")

    # Check if the email is being updated, and if so, check for uniqueness collisions
    if user_update.email is not None and user_update.email != user.email:
        result = db.execute(select(models.User).where(models.User.email == user_update.email))
        existing_email = result.scalars().first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already exists")

    # Update fields if provided
    if user_update.username is not None:
        user.username = user_update.username
    if user_update.email is not None:
        user.email = user_update.email
    if user_update.image_file is not None:
        user.image_file = user_update.image_file

    db.commit()
    db.refresh(user)
    return user

@app.delete("/posts/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post).where(models.Post.id == id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    db.delete(post)
    db.commit()
    return None

@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    return None

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




