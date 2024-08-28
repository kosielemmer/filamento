import os
import logging
from typing import List, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, func, sql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.exc import IntegrityError
import uvicorn

__version__ = "2.8"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Database setup
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_DATABASE = os.getenv('DB_DATABASE')

SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}"
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define SQLAlchemy models
class Manufacturer(Base):
    __tablename__ = "manufacturer"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)

class Filament(Base):
    __tablename__ = "filament"
    id = Column(Integer, primary_key=True, index=True)
    manufacturer_id = Column(Integer, ForeignKey("manufacturer.id"))
    type = Column(String)
    color_name = Column(String)
    color_hex_code = Column(String)

class Inventory(Base):
    __tablename__ = "inventory"
    id = Column(Integer, primary_key=True, index=True)
    filament_id = Column(Integer, ForeignKey("filament.id"))
    location = Column(String)
    quantity = Column(Integer)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Application is starting up")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    yield
    # Shutdown
    logger.info("Application is shutting down")

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def custom_url_for(name: str, **path_params: Any) -> str:
    return app.url_path_for(name, **path_params)

templates.env.globals["url_for"] = custom_url_for

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": __version__}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/select_manufacturer", response_class=HTMLResponse, name="select_manufacturer_get")
async def select_manufacturer_get(request: Request, db: Session = Depends(get_db)):
    try:
        logger.info("Fetching manufacturers from database")
        manufacturers = db.query(Manufacturer).order_by(Manufacturer.name).all()
        manufacturers = [{'id': m.id, 'name': m.name} for m in manufacturers]
        logger.info(f"Found {len(manufacturers)} manufacturers: {manufacturers}")
        return templates.TemplateResponse("select_manufacturer.html", {"request": request, "manufacturers": manufacturers})
    except Exception as e:
        logger.error(f"Error fetching manufacturers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching manufacturers: {str(e)}")

@app.get('/select_filament/{manufacturer_id}')
async def select_filament(request: Request, manufacturer_id: int, db: Session = Depends(get_db)):
    logger.info(f"Fetching filament types for manufacturer_id: {manufacturer_id}")
    types = db.query(Filament.type).filter(Filament.manufacturer_id == manufacturer_id).distinct().order_by(Filament.type).all()
    types = [t[0] for t in types]
    logger.info(f"Found filament types: {types}")
    return templates.TemplateResponse('select_filament_type.html', {'request': request, 'manufacturer_id': manufacturer_id, 'types': types})

@app.post('/select_filament_type/{manufacturer_id}')
async def select_filament_type_post(request: Request, manufacturer_id: int, filament_type: str = Form(...)):
    try:
        return RedirectResponse(url=f'/select_color?manufacturer_id={manufacturer_id}&filament_type={filament_type}', status_code=303)
    except Exception as e:
        logger.error(f"Error in select_filament_type_post: {str(e)}")
        return templates.TemplateResponse('error.html', {
            'request': request,
            'error': f"An error occurred: {str(e)}"
        })

@app.get('/select_color')
async def select_color_get(request: Request, manufacturer_id: int, filament_type: str, db: Session = Depends(get_db)):
    try:
        logger.info(f"Fetching colors for manufacturer_id: {manufacturer_id}, filament_type: {filament_type}")
        colors = db.query(Filament.id, Filament.color_name, Filament.color_hex_code).filter(
            Filament.manufacturer_id == manufacturer_id,
            Filament.type == filament_type
        ).order_by(Filament.color_name).all()
        logger.info(f"Found colors: {colors}")
        if not colors:
            logger.warning(f'No colors found for {filament_type} from manufacturer ID {manufacturer_id}.')
            return templates.TemplateResponse('error.html', {
                'request': request,
                'error': f'No colors found for {filament_type} from manufacturer ID {manufacturer_id}.'
            })
        return templates.TemplateResponse('select_color.html', {
            'request': request,
            'manufacturer_id': manufacturer_id,
            'filament_type': filament_type,
            'colors': colors
        })
    except Exception as e:
        logger.error(f"Error in select_color_get: {str(e)}")
        return templates.TemplateResponse('error.html', {
            'request': request,
            'error': f"An error occurred: {str(e)}"
        })

@app.post('/select_color')
async def select_color_post(request: Request, manufacturer_id: int = Form(...), filament_type: str = Form(...), filament_id: int = Form(...)):
    return RedirectResponse(url=f'/select_location/{filament_id}', status_code=303)

@app.post('/select_location/{filament_id}', name="select_location_post")
async def select_location_post(request: Request, filament_id: int, location: str = Form(...), quantity: int = Form(...), db: Session = Depends(get_db)):
    try:
        existing_item = db.query(Inventory).filter(Inventory.filament_id == filament_id, Inventory.location == location).first()
        
        if existing_item:
            existing_item.quantity += quantity
        else:
            new_item = Inventory(filament_id=filament_id, location=location, quantity=quantity)
            db.add(new_item)
        
        db.commit()
        return RedirectResponse(url=app.url_path_for('select_manufacturer'), status_code=303)
    except Exception as e:
        logger.error(f"Error in select_location: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in select_location: {str(e)}")

@app.get('/select_location/{filament_id}', name="select_location_get")
async def select_location_get(request: Request, filament_id: int, db: Session = Depends(get_db)):
    try:
        occupied_locations = db.query(Inventory.location, func.sum(Inventory.quantity)).group_by(Inventory.location).all()
        occupied_locations = {loc: qty for loc, qty in occupied_locations}
        
        filament = db.query(Filament).filter(Filament.id == filament_id).first()
        
        if filament:
            return templates.TemplateResponse('select_location.html', {
                'request': request,
                'filament_id': filament_id,
                'manufacturer_id': filament.manufacturer_id,
                'filament_type': filament.type,
                'color_name': filament.color_name,
                'color_hex_code': filament.color_hex_code,
                'occupied_locations': occupied_locations
            })
        else:
            return RedirectResponse(url=app.url_path_for('select_manufacturer'), status_code=303)
    except Exception as e:
        logger.error(f"Error in select_location: {str(e)}")
        return templates.TemplateResponse('error.html', {'request': request, 'error': f"Error in select_location: {str(e)}"})

@app.get('/view_inventory')
async def view_inventory(request: Request, db: Session = Depends(get_db)):
    inventory = db.query(
        Manufacturer.name,
        Filament.type,
        Filament.color_name,
        Filament.color_hex_code,
        Inventory.location,
        Inventory.quantity
    ).join(Filament, Inventory.filament_id == Filament.id
    ).join(Manufacturer, Filament.manufacturer_id == Manufacturer.id
    ).order_by(Manufacturer.name, Filament.type, Filament.color_name).all()

    return templates.TemplateResponse('view_inventory.html', {'request': request, 'inventory': inventory})

@app.get('/data_maintenance')
async def data_maintenance(request: Request):
    return templates.TemplateResponse('data_maintenance.html', {'request': request})

@app.get('/manage_manufacturers', name="manage_manufacturers")
async def manage_manufacturers_get(request: Request, db: Session = Depends(get_db)):
    manufacturers = db.query(Manufacturer).order_by(Manufacturer.name).all()
    return templates.TemplateResponse('manage_manufacturers.html', {'request': request, 'manufacturers': manufacturers, 'error': None})

@app.post('/manage_manufacturers')
async def manage_manufacturers_post(request: Request, manufacturer_name: str = Form(...), db: Session = Depends(get_db)):
    try:
        new_manufacturer = Manufacturer(name=manufacturer_name)
        db.add(new_manufacturer)
        db.commit()
    except IntegrityError:
        db.rollback()
        return templates.TemplateResponse('manage_manufacturers.html', {
            'request': request, 
            'manufacturers': db.query(Manufacturer).order_by(Manufacturer.name).all(),
            'error': 'A manufacturer with this name already exists.'
        })
    except Exception as e:
        db.rollback()
        return templates.TemplateResponse('manage_manufacturers.html', {
            'request': request, 
            'manufacturers': db.query(Manufacturer).order_by(Manufacturer.name).all(),
            'error': f'An error occurred: {str(e)}'
        })
    
    manufacturers = db.query(Manufacturer).order_by(Manufacturer.name).all()
    return templates.TemplateResponse('manage_manufacturers.html', {'request': request, 'manufacturers': manufacturers})

@app.get('/manage_filaments', name="manage_filaments")
async def manage_filaments_get(request: Request, db: Session = Depends(get_db)):
    manufacturers = db.query(Manufacturer).order_by(Manufacturer.name).all()
    return templates.TemplateResponse('manage_filaments.html', {'request': request, 'manufacturers': manufacturers})

@app.post('/manage_filaments')
async def manage_filaments_post(
    request: Request,
    manufacturer_id: int = Form(...),
    filament_type: str = Form(...),
    color_name: str = Form(...),
    color_hex_code: str = Form(...),
    db: Session = Depends(get_db)
):
    existing_filament = db.query(Filament).filter(
        Filament.manufacturer_id == manufacturer_id,
        Filament.type == filament_type,
        Filament.color_name == color_name
    ).first()

    if not existing_filament:
        new_filament = Filament(
            manufacturer_id=manufacturer_id,
            type=filament_type,
            color_name=color_name,
            color_hex_code=color_hex_code
        )
        db.add(new_filament)
        db.commit()

    manufacturers = db.query(Manufacturer.id, Manufacturer.name).order_by(Manufacturer.name).all()
    return templates.TemplateResponse('manage_filaments.html', {'request': request, 'manufacturers': manufacturers})

@app.get('/get_filament_types/{manufacturer_id}')
async def get_filament_types(manufacturer_id: int, db: Session = Depends(get_db)):
    filament_types = db.query(Filament.type).filter(Filament.manufacturer_id == manufacturer_id).distinct().order_by(Filament.type).all()
    filament_types = [t[0] for t in filament_types]
    return JSONResponse(content=filament_types)

@app.get("/version")
async def get_version():
    return JSONResponse(content={"version": __version__})

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8090, log_level="info")
