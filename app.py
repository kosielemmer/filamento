from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from werkzeug.exceptions import HTTPException
import os
import psycopg2
from psycopg2 import sql

def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', '192.168.1.12'),
        database=os.getenv('DB_DATABASE', 'filamento'),
        user=os.getenv('DB_USER', 'filamento'),
        password=os.getenv('DB_PASSWORD', 'filamento')
    )
    return conn

app = Flask(__name__)

# Set a secret key for the application
app.secret_key = 'your_secret_key_here'  # Replace with a strong, random secret key

@app.errorhandler(Exception)
def handle_exception(e):
    # pass through HTTP errors
    if isinstance(e, HTTPException):
        return e
    # now you're handling non-HTTP exceptions only
    return render_template("error.html", error=str(e)), 500


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
    return render_template('select_filament.html', manufacturer_id=manufacturer_id, types=types)

@app.route('/select_filament_type/<int:manufacturer_id>')
def select_filament_type(manufacturer_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT type FROM filament WHERE manufacturer_id = %s ORDER BY type;", (manufacturer_id,))
    types = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('select_filament_type.html', manufacturer_id=manufacturer_id, types=types)

@app.route('/select_color/<int:manufacturer_id>')
def select_color(manufacturer_id):
    filament_type = request.args.get('filament_type')
    shelf = request.args.get('shelf')
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT color_name, color_hex_code FROM filament WHERE manufacturer_id = %s AND type = %s ORDER BY color_name;", (manufacturer_id, filament_type))
        colors = cur.fetchall()
        cur.close() 
        conn.close()
        if not colors:
            flash('No colors found for this filament type.', 'warning')
        return render_template('select_color.html', manufacturer_id=manufacturer_id, filament_type=filament_type, colors=colors, shelf=shelf)
    except Exception as e:
        flash(f"Error in select_color: {str(e)}", 'error')
        return redirect(url_for('select_filament', manufacturer_id=manufacturer_id))

@app.route('/select_location/<int:manufacturer_id>/<filament_type>/<color_name>/<color_hex_code>/<int:shelf>')
def select_location(manufacturer_id, filament_type, color_name, color_hex_code, shelf):
    try:
        return render_template('select_location.html', manufacturer_id=manufacturer_id, filament_type=filament_type, color_name=color_name, color_hex_code=color_hex_code, shelf=shelf)
    except Exception as e:
        return render_template('error.html', error=f"Error in select_location: {str(e)}"), 500

@app.route('/select_position/<int:manufacturer_id>/<filament_type>/<color_name>/<color_hex_code>/<int:shelf>')
def select_position(manufacturer_id, filament_type, color_name, color_hex_code, shelf):
    try:
        return render_template('select_position.html', manufacturer_id=manufacturer_id, filament_type=filament_type, color_name=color_name, color_hex_code=color_hex_code, shelf=shelf)
    except Exception as e:
        return render_template('error.html', error=f"Error in select_position: {str(e)}"), 500

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

@app.route('/view_inventory')
def view_inventory():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT m.name, i.filament_type, i.color_name, i.color_hex_code, i.location 
        FROM inventory i 
        JOIN manufacturer m ON i.manufacturer_id = m.id 
        ORDER BY m.name, i.filament_type, i.color_name;
    """)
    inventory = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('view_inventory.html', inventory=inventory)

if __name__ == '__main__':
    app.run(debug=True)
