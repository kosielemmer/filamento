import os
import logging
import re
from typing import List, Any
import socket
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, func, sql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
import uvicorn

__version__ = "2.7"

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
SQLALCHEMY_DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_DATABASE')}"
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db_connection():
    return engine.connect()

# Define SQLAlchemy models
from sqlalchemy import Column, Integer, String, Sequence

class Manufacturer(Base):
    __tablename__ = "manufacturer"
    id = Column(Integer, Sequence('manufacturer_id_seq'), primary_key=True, index=True)
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
templates.env.globals["url_for"] = app.url_path_for

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

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": __version__}

@app.get('/select_filament/{manufacturer_id}')
async def select_filament(request: Request, manufacturer_id: int, db: Session = Depends(get_db)):
    logger.info(f"Fetching filament types for manufacturer_id: {manufacturer_id}")
    types = db.query(Filament.type).filter(Filament.manufacturer_id == manufacturer_id).distinct().order_by(Filament.type).all()
    types = [t[0] for t in types]
    logger.info(f"Found filament types: {types}")
    return templates.TemplateResponse('select_filament_type.html', {'request': request, 'manufacturer_id': manufacturer_id, 'types': types})

@app.get('/select_filament_type/{manufacturer_id}')
async def select_filament_type_get(request: Request, manufacturer_id: int, db: Session = Depends(get_db)):
    types = db.query(Filament.type).filter(Filament.manufacturer_id == manufacturer_id).distinct().order_by(Filament.type).all()
    types = [t[0] for t in types]
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

@app.get('/select_shelf')
async def select_shelf_get(request: Request, manufacturer_id: int, filament_type: str, color_name: str, color_hex_code: str):
    return templates.TemplateResponse('select_shelf.html', {
        'request': request,
        'manufacturer_id': manufacturer_id,
        'filament_type': filament_type,
        'color_name': color_name,
        'color_hex_code': color_hex_code
    })

@app.post('/select_shelf')
async def select_shelf_post(
    request: Request,
    manufacturer_id: int = Form(...),
    filament_type: str = Form(...),
    color_name: str = Form(...),
    color_hex_code: str = Form(...),
    shelf: str = Form(...)
):
    return RedirectResponse(
        url=f'/select_position/{manufacturer_id}/{filament_type}/{color_name}/{color_hex_code}/{shelf}',
        status_code=303
    )

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

@app.get('/select_filament/{manufacturer_id}')
async def select_filament(request: Request, manufacturer_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT type FROM filament WHERE manufacturer_id = %s ORDER BY type;", (manufacturer_id,))
    types = cur.fetchall()
    cur.close()
    conn.close()
    return templates.TemplateResponse('select_filament_type.html', {'request': request, 'manufacturer_id': manufacturer_id, 'types': types})

from fastapi.responses import RedirectResponse

templates = Jinja2Templates(directory="templates")

@app.post('/select_location/{filament_id}', name="select_location_post")
async def select_location_post(request: Request, filament_id: int, location: str = Form(...), quantity: int = Form(...)):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if the filament already exists in the inventory at the given location
        cur.execute("SELECT id, quantity FROM inventory WHERE filament_id = %s AND location = %s", (filament_id, location))
        existing_item = cur.fetchone()
        
        if existing_item:
            # Update the quantity if the item already exists
            new_quantity = existing_item[1] + int(quantity)
            cur.execute("UPDATE inventory SET quantity = %s WHERE id = %s", (new_quantity, existing_item[0]))
        else:
            # Insert a new item if it doesn't exist
            cur.execute("INSERT INTO inventory (filament_id, location, quantity) VALUES (%s, %s, %s)", (filament_id, location, quantity))
        
        conn.commit()
        cur.close()
        conn.close()
        return RedirectResponse(url=app.url_path_for('select_manufacturer'), status_code=303)
    except Exception as e:
        logger.error(f"Error in select_location: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in select_location: {str(e)}")

@app.get('/select_location/{filament_id}', name="select_location_get")
async def select_location_get(request: Request, filament_id: int):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT location, SUM(quantity) FROM inventory GROUP BY location")
        occupied_locations = {row[0]: row[1] for row in cur.fetchall()}
        
        # Fetch filament details
        cur.execute("SELECT manufacturer_id, type, color_name, color_hex_code FROM filament WHERE id = %s", (filament_id,))
        filament = cur.fetchone()
        cur.close()
        conn.close()

        if filament:
            manufacturer_id, filament_type, color_name, color_hex_code = filament
            return templates.TemplateResponse('select_location.html', {
                'request': request,
                'filament_id': filament_id,
                'manufacturer_id': manufacturer_id,
                'filament_type': filament_type,
                'color_name': color_name,
                'color_hex_code': color_hex_code,
                'occupied_locations': occupied_locations
            })
        else:
            return RedirectResponse(url=app.url_path_for('select_manufacturer'), status_code=303)
    except Exception as e:
        logger.error(f"Error in select_location: {str(e)}")
        return templates.TemplateResponse('error.html', {'request': request, 'error': f"Error in select_location: {str(e)}"})

@app.get('/select_position/{manufacturer_id}/{filament_type}/{color_name}/{color_hex_code}/{shelf}')
async def select_position(request: Request, manufacturer_id: int, filament_type: str, color_name: str, color_hex_code: str, shelf: int):
    try:
        return templates.TemplateResponse('select_position.html', {
            'request': request,
            'manufacturer_id': manufacturer_id,
            'filament_type': filament_type,
            'color_name': color_name,
            'color_hex_code': color_hex_code,
            'shelf': shelf
        })
    except Exception as e:
        app.logger.error(f"Error in select_position: {str(e)}")
        return RedirectResponse(url=app.url_path_for('select_location', manufacturer_id=manufacturer_id, filament_type=filament_type, color_name=color_name, color_hex_code=color_hex_code), status_code=303)

@app.post('/add_inventory')
async def add_inventory(
    manufacturer_id: int = Form(...),
    filament_type: str = Form(...),
    color_name: str = Form(...),
    color_hex_code: str = Form(...),
    location: str = Form(...)
):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        sql.SQL("INSERT INTO inventory (manufacturer_id, filament_type, color_name, color_hex_code, location) VALUES (%s, %s, %s, %s, %s)"),
        (manufacturer_id, filament_type, color_name, color_hex_code, location)
    )
    conn.commit()
    cur.close()
    conn.close()
    
    return RedirectResponse(url=app.url_path_for('select_manufacturer'), status_code=303)

@app.post('/add_inventory_item')
async def add_inventory_item(
    manufacturer_id: int = Form(...),
    filament_type: str = Form(...),
    color_name: str = Form(...),
    color_hex_code: str = Form(...),
    location: str = Form(...)
):
    try:
        # Debug logging
        app.logger.debug(f"Received values: manufacturer_id={manufacturer_id}, filament_type={filament_type}, color_name={color_name}, color_hex_code={color_hex_code}, location={location}")
        
        # Additional debug logging to check the exact value of color_hex_code
        app.logger.debug(f"Color hex code received: {color_hex_code}")

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO inventory (manufacturer_id, filament_type, color_name, color_hex_code, location) VALUES (%s, %s, %s, %s, %s)",
            (manufacturer_id, filament_type, color_name, color_hex_code, location)
        )
        conn.commit()
        cur.close()
        conn.close()

        # Debug logging
        app.logger.debug(f"Inserted into database: manufacturer_id={manufacturer_id}, filament_type={filament_type}, color_name={color_name}, color_hex_code={color_hex_code}, location={location}")

        return RedirectResponse(url=app.url_path_for('select_manufacturer'), status_code=303)
    except Exception as e:
        app.logger.error(f"Error adding inventory item: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error adding inventory item: {str(e)}")

@app.get('/view_inventory')
async def view_inventory(request: Request, db: Session = Depends(get_db)):
    inventory = db.query(
        Manufacturer.name,
        Filament.type,
        Filament.color_name,
        Filament.color_hex_code,
        Inventory.location
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

from sqlalchemy.exc import IntegrityError

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
    # Check for duplication
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

@app.get('/manage_colors', name="manage_colors_get")
async def manage_colors_get(request: Request, db: Session = Depends(get_db)):
    manufacturers = db.query(Manufacturer).order_by(Manufacturer.name).all()
    return templates.TemplateResponse('manage_colors.html', {'request': request, 'manufacturers': manufacturers})

@app.post('/manage_colors')
async def manage_colors_post(
    request: Request,
    manufacturer_id: int = Form(...),
    filament_type: str = Form(...),
    color_name: str = Form(...),
    color_hex_code: str = Form(...),
    db: Session = Depends(get_db)
):
    # Check for duplication
    existing_color = db.query(Filament).filter(
        Filament.manufacturer_id == manufacturer_id,
        Filament.type == filament_type,
        Filament.color_name == color_name
    ).first()

    if not existing_color:
        new_color = Filament(
            manufacturer_id=manufacturer_id,
            type=filament_type,
            color_name=color_name,
            color_hex_code=color_hex_code
        )
        db.add(new_color)
        db.commit()

    manufacturers = db.query(Manufacturer.id, Manufacturer.name).order_by(Manufacturer.name).all()
    return templates.TemplateResponse('manage_colors.html', {'request': request, 'manufacturers': manufacturers})

@app.get('/get_filament_types/{manufacturer_id}')
async def get_filament_types(manufacturer_id: int, db: Session = Depends(get_db)):
    filament_types = db.query(Filament.type).filter(Filament.manufacturer_id == manufacturer_id).distinct().order_by(Filament.type).all()
    filament_types = [t[0] for t in filament_types]
    return JSONResponse(content=filament_types)

@app.get("/version")
async def get_version():
    return JSONResponse(content={"version": __version__})

import uvicorn
import socket

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Try to get a non-local IP
        s.connect(('8.8.8.8', 80))
        IP = s.getsockname()[0]
    except Exception:
        # If that fails, fall back to local IP detection
        try:
            IP = socket.gethostbyname(socket.gethostname())
        except Exception:
            IP = '127.0.0.1'
    finally:
        s.close()
    return IP

if __name__ == '__main__':
    host_ip = get_ip()
    port = 8090
    print(f"Attempting to start server on {host_ip}:{port}")
    try:
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
        print(f"\nServer started successfully!")
        print(f"Local access URL: http://localhost:{port}")
        print(f"Network access URL: http://{host_ip}:{port}")
        print("\nTo access the application from other devices on your network:")
        print(f"1. Make sure they are connected to the same network")
        print(f"2. Open a web browser and go to: http://{host_ip}:{port}")
        print("\nPress CTRL+C to stop the server.")
    except OSError as e:
        print(f"Unable to start server on port {port}. Error: {e}")
        print("Please ensure the port is not in use and try again.")
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel

app = FastAPI()

# Setup templates
templates = Jinja2Templates(directory="templates")

# Setup static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Database setup (replace with your actual database URL)
DATABASE_URL = "postgresql://user:password@localhost/dbname"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Root route
@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Add more routes and functionality here

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
