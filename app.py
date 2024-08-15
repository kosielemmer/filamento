from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import psycopg2
from psycopg2 import sql
import logging
import re
from typing import List

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', '192.168.1.12'),
        database=os.getenv('DB_DATABASE', 'filamento'),
        user=os.getenv('DB_USER', 'filamento'),
        password=os.getenv('DB_PASSWORD', 'filamento')
    )
    return conn

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Add this line to make the static files available
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/select_manufacturer", response_class=HTMLResponse)
async def select_manufacturer(request: Request):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM manufacturer ORDER BY name;")
    manufacturers = cur.fetchall()
    manufacturers = [{'id': m[0], 'name': m[1]} for m in manufacturers]
    cur.close()
    conn.close()
    return templates.TemplateResponse("select_manufacturer.html", {"request": request, "manufacturers": manufacturers})

@app.get('/select_filament/{manufacturer_id}')
async def select_filament(request: Request, manufacturer_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT type FROM filament WHERE manufacturer_id = %s ORDER BY type;", (manufacturer_id,))
    types = cur.fetchall()
    cur.close()
    conn.close()
    return templates.TemplateResponse('select_filament_type.html', {'request': request, 'manufacturer_id': manufacturer_id, 'types': types})

@app.get('/select_filament_type/{manufacturer_id}')
async def select_filament_type_get(request: Request, manufacturer_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT type FROM filament WHERE manufacturer_id = %s ORDER BY type;", (manufacturer_id,))
    types = cur.fetchall()
    cur.close()
    conn.close()
    return templates.TemplateResponse('select_filament_type.html', {'request': request, 'manufacturer_id': manufacturer_id, 'types': types})

@app.post('/select_filament_type/{manufacturer_id}')
async def select_filament_type_post(request: Request, manufacturer_id: int, filament_type: str = Form(...)):
    try:
        return RedirectResponse(url=f'/select_color?manufacturer_id={manufacturer_id}&filament_type={filament_type}', status_code=303)
    except Exception as e:
        app.logger.error(f"Error in select_filament_type_post: {str(e)}")
        return templates.TemplateResponse('error.html', {
            'request': request,
            'error': f"An error occurred: {str(e)}"
        })

@app.get('/select_filament_type/{manufacturer_id}')
async def select_filament_type_get(request: Request, manufacturer_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT type FROM filament WHERE manufacturer_id = %s ORDER BY type;", (manufacturer_id,))
    types = cur.fetchall()
    cur.close()
    conn.close()
    return templates.TemplateResponse('select_filament_type.html', {'request': request, 'manufacturer_id': manufacturer_id, 'types': types})

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
async def select_color_get(request: Request, manufacturer_id: int, filament_type: str):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, color_name, color_hex_code FROM filament WHERE manufacturer_id = %s AND type = %s ORDER BY color_name;", (manufacturer_id, filament_type))
        colors = cur.fetchall()
        cur.close() 
        conn.close()
        if not colors:
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
        return RedirectResponse(url=app.url_path_for('index'), status_code=303)
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
async def view_inventory(request: Request):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT m.name, f.type, f.color_name, f.color_hex_code, i.location 
        FROM inventory i 
        JOIN filament f ON i.filament_id = f.id
        JOIN manufacturer m ON f.manufacturer_id = m.id 
        ORDER BY m.name, f.type, f.color_name;
    """)
    inventory = cur.fetchall()
    cur.close()
    conn.close()

    return templates.TemplateResponse('view_inventory.html', {'request': request, 'inventory': inventory})

@app.get('/data_maintenance')
async def data_maintenance(request: Request):
    return templates.TemplateResponse('data_maintenance.html', {'request': request})

@app.get('/manage_manufacturers')
async def manage_manufacturers_get(request: Request):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM manufacturer ORDER BY name")
    manufacturers = cur.fetchall()
    cur.close()
    conn.close()
    return templates.TemplateResponse('manage_manufacturers.html', {'request': request, 'manufacturers': manufacturers})

@app.post('/manage_manufacturers')
async def manage_manufacturers_post(request: Request, manufacturer_name: str = Form(...)):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO manufacturer (name) VALUES (%s)", (manufacturer_name,))
    conn.commit()
    cur.execute("SELECT * FROM manufacturer ORDER BY name")
    manufacturers = cur.fetchall()
    cur.close()
    conn.close()
    return templates.TemplateResponse('manage_manufacturers.html', {'request': request, 'manufacturers': manufacturers})

@app.get('/manage_filaments')
async def manage_filaments_get(request: Request):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM manufacturer ORDER BY name")
    manufacturers = cur.fetchall()
    cur.close()
    conn.close()
    return templates.TemplateResponse('manage_filaments.html', {'request': request, 'manufacturers': manufacturers})

@app.post('/manage_filaments')
async def manage_filaments_post(
    request: Request,
    manufacturer_id: int = Form(...),
    filament_type: str = Form(...),
    color_name: str = Form(...),
    color_hex_code: str = Form(...)
):
    conn = get_db_connection()
    cur = conn.cursor()

    # Check for duplication
    cur.execute("SELECT * FROM filament WHERE manufacturer_id = %s AND type = %s AND color_name = %s", 
                (manufacturer_id, filament_type, color_name))
    existing_filament = cur.fetchone()

    if not existing_filament:
        cur.execute("INSERT INTO filament (manufacturer_id, type, color_name, color_hex_code) VALUES (%s, %s, %s, %s)",
                    (manufacturer_id, filament_type, color_name, color_hex_code))
        conn.commit()

    cur.execute("SELECT id, name FROM manufacturer ORDER BY name")
    manufacturers = cur.fetchall()

    cur.close()
    conn.close()

    return templates.TemplateResponse('manage_filaments.html', {'request': request, 'manufacturers': manufacturers})

@app.get('/manage_colors')
async def manage_colors_get(request: Request):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM manufacturer ORDER BY name")
    manufacturers = cur.fetchall()
    cur.close()
    conn.close()
    return templates.TemplateResponse('manage_colors.html', {'request': request, 'manufacturers': manufacturers})

@app.post('/manage_colors')
async def manage_colors_post(
    request: Request,
    manufacturer_id: int = Form(...),
    filament_type: str = Form(...),
    color_name: str = Form(...),
    color_hex_code: str = Form(...)
):
    conn = get_db_connection()
    cur = conn.cursor()

    # Check for duplication
    cur.execute("SELECT * FROM filament WHERE manufacturer_id = %s AND type = %s AND color_name = %s", 
                (manufacturer_id, filament_type, color_name))
    existing_color = cur.fetchone()

    if not existing_color:
        cur.execute("INSERT INTO filament (manufacturer_id, type, color_name, color_hex_code) VALUES (%s, %s, %s, %s)",
                    (manufacturer_id, filament_type, color_name, color_hex_code))
        conn.commit()

    cur.execute("SELECT id, name FROM manufacturer ORDER BY name")
    manufacturers = cur.fetchall()

    cur.close()
    conn.close()

    return templates.TemplateResponse('manage_colors.html', {'request': request, 'manufacturers': manufacturers})

@app.get('/get_filament_types/{manufacturer_id}')
async def get_filament_types(manufacturer_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT type FROM filament WHERE manufacturer_id = %s ORDER BY type", (manufacturer_id,))
    filament_types = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return JSONResponse(content=filament_types)

import uvicorn
import socket

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

if __name__ == '__main__':
    host_ip = get_ip()
    print(f"WSL IP Address: {host_ip}")
    print(f"Uvicorn running on http://{host_ip}:8000")
    print("\nTo access the application from your Windows host or other devices on your network:")
    print("1. Open PowerShell as Administrator on your Windows host")
    print("2. Run the following command to set up port forwarding:")
    print(f"   netsh interface portproxy add v4tov4 listenport=8000 listenaddress=0.0.0.0 connectport=8000 connectaddress={host_ip}")
    print("3. Access the application using your Windows host's IP address:")
    print("   http://<Windows_Host_IP>:8000")
    print("\nTo remove the port forwarding when you're done:")
    print("   netsh interface portproxy delete v4tov4 listenport=8000 listenaddress=0.0.0.0")
    uvicorn.run(app, host="0.0.0.0", port=8000)
