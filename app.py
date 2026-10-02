from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.templating import Jinja2Templates
import os
from dotenv import load_dotenv
import boto3
from fastapi.staticfiles import StaticFiles
import mysql.connector
import uuid

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
CLOUDFRONT_DOMAIN = "https://d2idgn4daty294.cloudfront.net"

DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT"))
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

print("AWS REGION:", AWS_REGION)
print("S3 BUCKET:", S3_BUCKET_NAME)

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=AWS_REGION,
    endpoint_url=f"https://s3.{AWS_REGION}.amazonaws.com"
)

def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        request = request,
        name = "index.html"
    )

@app.post("/api/posts")
async def create_post(
    content: str = Form(...),
    image: UploadFile = File(...)
):
    file_extension = os.path.splitext(image.filename)[1]
    image_key = f"{uuid.uuid4()}{file_extension}"
    
    s3.upload_fileobj(
        image.file,
        S3_BUCKET_NAME,
        image_key,
        ExtraArgs={
            "ContentType": image.content_type
        }
    )

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO posts (content, image_key)
        VALUES (%s, %s)
        """,
        (content, image_key)
    )

    conn.commit()

    cursor.close()
    conn.close()

    image_url = f"{CLOUDFRONT_DOMAIN}/{image_key}"

    return {
        "message": "發佈成功",
        "content": content,
        "image_filename": image_key,
        "image_url": image_url
    }

@app.get("/api/posts")
def get_posts():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT id, content, image_key, created_at
        FROM posts
        ORDER BY id DESC
        """
    )

    posts = cursor.fetchall()

    cursor.close()
    conn.close()

    for post in posts:
        post["image_url"] = f"{CLOUDFRONT_DOMAIN}/{post['image_key']}"

    return {"data": posts}