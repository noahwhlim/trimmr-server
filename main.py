import os
import random
import string
from fastapi import FastAPI;
from fastapi import Request;
from azure.cosmos import CosmosClient, exceptions;
from dotenv import load_dotenv;

from fastapi.middleware.cors import CORSMiddleware


load_dotenv()

def connectdb_read():
    COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
    COSMOS_KEY = os.getenv("COSMOS_KEY_READ")
    DATABASE_NAME = os.getenv("DATABASE_NAME")
    CONTAINER_NAME = os.getenv("CONTAINER_NAME")

    client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)

    try:
        # Connect to the database and container
        database = client.get_database_client(DATABASE_NAME)
        container = database.get_container_client(CONTAINER_NAME)
        return container
    except Exception as e:
            # Catch any other exceptions
            print("Error" + str(e))
            return None

def connectdb_write():
    COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
    COSMOS_KEY = os.getenv("COSMOS_KEY_WRITE")
    DATABASE_NAME = os.getenv("DATABASE_NAME")
    CONTAINER_NAME = os.getenv("CONTAINER_NAME")

    client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)

    try:
        # Connect to the database and container
        database = client.get_database_client(DATABASE_NAME)
        container = database.get_container_client(CONTAINER_NAME)
        return container
    except Exception as e:
            # Catch any other exceptions
            print("Error" + str(e))
            return None

container_read = connectdb_read();
container_write = connectdb_write();
app = FastAPI();
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# logging to debug CORS
@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    print(f"Response status: {response.status_code}")
    return response

@app.post("/generate")
async def generate(request: Request):
    body = await request.json()
    long_url = body.get("long_url")
    
    if not long_url:
        return {"error": "long_url is required"}
    
    short = ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
    # while short exist in db, regenerate
    check_query = 'SELECT * FROM c WHERE c.id = "' + short + '"'
    items = list(container_read.query_items(query=check_query))
    
    while (len(items)) != 0:
        short = ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
        items = list(container_read.query_items(query=check_query))
    
    lower_long_url = long_url.lower()
    # # assign short:item to db
    new_item = {"id": short,
    "original_url": lower_long_url}
    container_write.create_item(body=new_item)
    # return "www.trimmr.io/" + short

    return new_item
    
@app.get("/getall")
def getall():
    try:
        # Query the container
        query = "SELECT * FROM c"
        items = list(container_read.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        # return {"status": "success", "count": len(items), "items": items}
        return {"original_urls": [item["original_url"] for item in items]}


    except Exception as e:
        # Catch any other exceptions
        return {"status": "error", "message": str(e)}

@app.get("/{id}")
def reroute(id):
    # check if id exist in db
    query = 'SELECT * FROM c WHERE c.id = "' + id + '"'
    items = list(container_read.query_items(query=query))
    
    if len(items) == 1:
        return {"original_url": items[0]["original_url"]}
