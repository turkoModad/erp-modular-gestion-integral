import uvicorn
from fastapi import FastAPI
import os


app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8010))
    uvicorn.run("main:app", host="127.0.0.1", port=port, reload=True)    