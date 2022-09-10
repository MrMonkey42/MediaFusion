import json
import logging
from pathlib import Path

from fastapi import FastAPI, Request, Response, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import database
import schemas
import scrap
import utils

logging.basicConfig(format='%(levelname)s::%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="resources"), name="static")
BASE_PATH = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=str(BASE_PATH / "resources"))

with open("manifest.json") as file:
    manifest = json.load(file)


@app.on_event("startup")
async def init_db():
    await database.init()


@app.get("/")
async def get_home(request: Request):
    return TEMPLATES.TemplateResponse(
        "home.html",
        {
            "request": request, "name": manifest.get("name"), "version": manifest.get("version"),
            "description": manifest.get("description"), "gives": [
            "Tamil Movies", "Malayalam Movies", "Telugu Movies", "Hindi Movies", "Kannada Movies", "English Movies",
            "Dubbed Movies"
        ],
            "logo": "static/tamilblasters.png"
        },
    )


@app.get("/manifest.json")
async def get_manifest(response: Response):
    response.headers.update({
        "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "*"
    })
    return manifest


@app.get("/catalog/movie/{catalog_id}.json", response_model=schemas.Movie)
@app.get("/catalog/movie/{catalog_id}/skip={skip}.json", response_model=schemas.Movie)
async def get_catalog(response: Response, catalog_id: str, skip: int = 0):
    response.headers.update({
        "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "*"
    })
    movies = schemas.Movie()
    movies.metas.extend(await utils.get_movies_meta(catalog_id, skip))
    return movies


@app.get("/meta/movie/{meta_id}.json")
async def get_meta(meta_id: str, response: Response):
    response.headers.update({
        "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "*"
    })
    return await utils.get_movie_meta(meta_id)


@app.get("/stream/movie/{video_id}.json", response_model=schemas.Streams)
async def get_stream(video_id: str, response: Response):
    response.headers.update({
        "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "*"
    })
    streams = schemas.Streams()
    streams.streams.extend(await utils.get_movie_streams(video_id))
    return streams


@app.post("/scraper")
async def run_scraper(
        background_tasks: BackgroundTasks,
        language: str = "tamil", video_type: str = "hdrip", pages: int = 1, start_page: int = 1,
        is_scrape_home: bool = False,
):
    background_tasks.add_task(scrap.run_scraper, language, video_type, pages, start_page, is_scrape_home)
    return {"message": "Scraping in background..."}