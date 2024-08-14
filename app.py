from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, abort
from werkzeug.exceptions import HTTPException
import os
import psycopg2
from psycopg2 import sql
import logging
import re
import ipaddress

def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', '192.168.1.12'),
        database=os.getenv('DB_DATABASE', 'filamento'),
        user=os.getenv('DB_USER', 'filamento'),
        password=os.getenv('DB_PASSWORD', 'filamento')
    )
    return conn

app = Flask(__name__)

# Remove secret key for open access

# Remove error handling and logging for open access

def is_allowed_ip(ip):
    allowed_network = ipaddress.IPv4Network('192.168.1.0/24')
    return ipaddress.IPv4Address(ip) in allowed_network

@app.before_request
def restrict_access():
    client_ip = request.remote_addr
    if not is_allowed_ip(client_ip):
        abort(403)  # Forbidden


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/select_manufacturer')
def select_manufacturer():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM manufacturer ORDER BY name;")
    manufacturers = cur.fetchall()
    manufacturers = [{'id': m[0], 'name': m[1]} for m in manufacturers]
    cur.close()
    conn.close()
    return render_template('select_manufacturer.html', manufacturers=manufacturers)

@app.route('/select_filament/<int:manufacturer_id>')
def select_filament(manufacturer_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT type FROM filament WHERE manufacturer_id = %s ORDER BY type;", (manufacturer_id,))
    types = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('select_filament_type.html', manufacturer_id=manufacturer_id, types=types)

@app.route('/select_filament_type/<int:manufacturer_id>', methods=['GET', 'POST'])
def select_filament_type(manufacturer_id):
    if request.method == 'POST':
        filament_type = request.form['filament_type']
        return redirect(url_for('select_color', manufacturer_id=manufacturer_id, filament_type=filament_type))
    else:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT type FROM filament WHERE manufacturer_id = %s ORDER BY type;", (manufacturer_id,))
        types = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('select_filament_type.html', manufacturer_id=manufacturer_id, types=types)

@app.route('/select_shelf', methods=['GET', 'POST'])
def select_shelf():
    if request.method == 'POST':
        manufacturer_id = request.form.get('manufacturer_id', type=int)
        filament_type = request.form.get('filament_type')
        color_name = request.form.get('color_name')
        color_hex_code = request.form.get('color_hex_code')
        shelf = request.form.get('shelf')
        return redirect(url_for('select_position', manufacturer_id=manufacturer_id, filament_type=filament_type, color_name=color_name, color_hex_code=color_hex_code, shelf=shelf))
    else:
        manufacturer_id = request.args.get('manufacturer_id', type=int)
        filament_type = request.args.get('filament_type')
        color_name = request.args.get('color_name')
        color_hex_code = request.args.get('color_hex_code')
        return render_template('select_shelf.html', manufacturer_id=manufacturer_id, filament_type=filament_type, color_name=color_name, color_hex_code=color_hex_code)

@app.route('/select_color', methods=['GET', 'POST'])
def select_color():
    if request.method == 'POST':
        manufacturer_id = request.form.get('manufacturer_id', type=int)
        filament_type = request.form.get('filament_type')
        filament_id = request.form.get('filament_id')
        return redirect(url_for('select_location', filament_id=filament_id))
    else:
        manufacturer_id = request.args.get('manufacturer_id', type=int)
        filament_type = request.args.get('filament_type')
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, color_name, color_hex_code FROM filament WHERE manufacturer_id = %s AND type = %s ORDER BY color_name;", (manufacturer_id, filament_type))
        colors = cur.fetchall()
        cur.close() 
        conn.close()
        if not colors:
            flash('No colors found for this filament type.', 'warning')
        return render_template('select_color.html', manufacturer_id=manufacturer_id, filament_type=filament_type, colors=colors)
    except Exception as e:
        flash(f"Error in select_color: {str(e)}", 'error')
        return redirect(url_for('select_filament', manufacturer_id=manufacturer_id))

@app.route('/select_location/<int:filament_id>', methods=['GET', 'POST'])
def select_location(filament_id):
    try:
        if request.method == 'POST':
            location = request.form.get('location')
            quantity = request.form.get('quantity', 1)
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
            flash('Inventory item added successfully.', 'success')
            return redirect(url_for('index'))
        else:
            # Fetch current inventory status
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
                return render_template('select_location.html', 
                                       filament_id=filament_id,
                                       manufacturer_id=manufacturer_id, 
                                       filament_type=filament_type, 
                                       color_name=color_name, 
                                       color_hex_code=color_hex_code,
                                       occupied_locations=occupied_locations)
            else:
                flash('Filament not found.', 'error')
                return redirect(url_for('select_manufacturer'))
    except Exception as e:
        app.logger.error(f"Error in select_location: {str(e)}")
        return render_template('error.html', error=f"Error in select_location: {str(e)}"), 500

@app.route('/parse_barcode', methods=['POST'])
def parse_barcode():
    barcode = request.form.get('barcode', '')
    # Assuming the barcode format is: SHELF-POSITION
    # For example: A-01
    pattern = r'^([A-Z])-(\d{2})$'
    match = re.match(pattern, barcode)
    if match:
        shelf, position = match.groups()
        location = f"{shelf}-{position}"
        return jsonify({'success': True, 'location': location})
    else:
        return jsonify({'success': False, 'error': 'Invalid barcode format'})

@app.route('/select_position/<int:manufacturer_id>/<filament_type>/<color_name>/<color_hex_code>/<int:shelf>')
def select_position(manufacturer_id, filament_type, color_name, color_hex_code, shelf):
    try:
        return render_template('select_position.html', 
                               manufacturer_id=manufacturer_id, 
                               filament_type=filament_type, 
                               color_name=color_name, 
                               color_hex_code=color_hex_code, 
                               shelf=shelf)
    except Exception as e:
        # Log the error for debugging
        app.logger.error(f"Error in select_position: {str(e)}")
        # Redirect to select_location with all necessary parameters
        return redirect(url_for('select_location', 
                                manufacturer_id=manufacturer_id, 
                                filament_type=filament_type, 
                                color_name=color_name, 
                                color_hex_code=color_hex_code))

@app.route('/add_inventory', methods=['POST'])
def add_inventory():
    manufacturer_id = request.form['manufacturer_id']
    filament_type = request.form['filament_type']
    color_name = request.form['color_name']
    color_hex_code = request.form['color_hex_code']
    location = request.form['location']
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        sql.SQL("INSERT INTO inventory (manufacturer_id, filament_type, color_name, color_hex_code, location) VALUES (%s, %s, %s, %s, %s)"),
        (manufacturer_id, filament_type, color_name, color_hex_code, location)
    )
    conn.commit()
    cur.close()
    conn.close()
    
    flash('Success', 'success')
    return redirect(url_for('select_manufacturer'))

@app.route('/add_inventory_item', methods=['POST'])
def add_inventory_item():
    try:
        manufacturer_id = request.form['manufacturer_id']
        filament_type = request.form['filament_type']
        color_name = request.form['color_name']
        color_hex_code = request.form['color_hex_code']
        location = request.form['location']

        # Debug logging
        app.logger.debug(f"Received values: manufacturer_id={manufacturer_id}, filament_type={filament_type}, color_name={color_name}, color_hex_code={color_hex_code}, location={location}")
        
        # Additional debug logging to check the exact value of color_hex_code
        app.logger.debug(f"Color hex code received: {color_hex_code}")

        # Debug logging
        app.logger.debug(f"Received values: manufacturer_id={manufacturer_id}, filament_type={filament_type}, color_name={color_name}, color_hex_code={color_hex_code}, location={location}")

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

        # Debug logging
        app.logger.debug(f"Inserted into database: manufacturer_id={manufacturer_id}, filament_type={filament_type}, color_name={color_name}, color_hex_code={color_hex_code}, location={location}")

        flash('Success', 'success')
        return redirect(url_for('select_manufacturer'))
    except Exception as e:
        app.logger.error(f"Error adding inventory item: {str(e)}")
        flash(f"Error adding inventory item: {str(e)}", 'error')
        return redirect(url_for('select_manufacturer'))

@app.route('/view_inventory')
def view_inventory():
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

    # Debug: Print color information
    for item in inventory:
        print(f"Color: {item[2]}, Hex: {item[3]}")
    
    return render_template('view_inventory.html', inventory=inventory)

@app.route('/data_maintenance')
def data_maintenance():
    return render_template('data_maintenance.html')

@app.route('/manage_manufacturers', methods=['GET', 'POST'])
def manage_manufacturers():
    conn = get_db_connection()
    cur = conn.cursor()
    
    if request.method == 'POST':
        new_manufacturer = request.form['manufacturer_name']
        cur.execute("INSERT INTO manufacturer (name) VALUES (%s)", (new_manufacturer,))
        conn.commit()
        flash('New manufacturer added successfully!', 'success')
    
    cur.execute("SELECT * FROM manufacturer ORDER BY name")
    manufacturers = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('manage_manufacturers.html', manufacturers=manufacturers)

@app.route('/manage_filaments', methods=['GET', 'POST'])
def manage_filaments():
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        manufacturer_id = request.form['manufacturer_id']
        filament_type = request.form['filament_type']
        color_name = request.form['color_name']
        color_hex_code = request.form['color_hex_code']

        # Check for duplication
        cur.execute("SELECT * FROM filament WHERE manufacturer_id = %s AND type = %s AND color_name = %s", 
                    (manufacturer_id, filament_type, color_name))
        existing_filament = cur.fetchone()

        if existing_filament:
            flash('This filament already exists!', 'warning')
        else:
            cur.execute("INSERT INTO filament (manufacturer_id, type, color_name, color_hex_code) VALUES (%s, %s, %s, %s)",
                        (manufacturer_id, filament_type, color_name, color_hex_code))
            conn.commit()
            flash('New filament added successfully!', 'success')

    cur.execute("SELECT id, name FROM manufacturer ORDER BY name")
    manufacturers = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('manage_filaments.html', manufacturers=manufacturers)

@app.route('/manage_colors', methods=['GET', 'POST'])
def manage_colors():
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        manufacturer_id = request.form['manufacturer_id']
        filament_type = request.form['filament_type']
        color_name = request.form['color_name']
        color_hex_code = request.form['color_hex_code']

        # Check for duplication
        cur.execute("SELECT * FROM filament WHERE manufacturer_id = %s AND type = %s AND color_name = %s", 
                    (manufacturer_id, filament_type, color_name))
        existing_color = cur.fetchone()

        if existing_color:
            flash('This color already exists for the selected manufacturer and filament type!', 'warning')
        else:
            cur.execute("INSERT INTO filament (manufacturer_id, type, color_name, color_hex_code) VALUES (%s, %s, %s, %s)",
                        (manufacturer_id, filament_type, color_name, color_hex_code))
            conn.commit()
            flash('New color added successfully!', 'success')

    cur.execute("SELECT id, name FROM manufacturer ORDER BY name")
    manufacturers = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('manage_colors.html', manufacturers=manufacturers)

@app.route('/get_filament_types/<int:manufacturer_id>')
def get_filament_types(manufacturer_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT type FROM filament WHERE manufacturer_id = %s ORDER BY type", (manufacturer_id,))
    filament_types = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return jsonify(filament_types)

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
    print(f"Access the application at: http://{host_ip}:5000")
    app.run(host=host_ip, port=5000)
