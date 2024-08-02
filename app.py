from flask import Flask, render_template, request, redirect, url_for, jsonify
import psycopg2
import requests

app = Flask(__name__)

# Database connection
def get_db_connection():
    conn = psycopg2.connect(
        host="192.168.1.12",
        database="filamento",
        user="filamento",
        password="filamento"
    )
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/select_manufacturer')
def select_manufacturer():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM manufacturer ORDER BY name;")
    manufacturers = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('select_manufacturer.html', manufacturers=manufacturers)

@app.route('/select_filament/<int:manufacturer_id>')
def select_filament(manufacturer_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT type FROM filament WHERE manufacturer_id = %s ORDER BY type;", (manufacturer_id,))
    types = cur.fetchall()
    cur.execute("SELECT DISTINCT color_name, color_hex_code FROM filament WHERE manufacturer_id = %s ORDER BY color_name;", (manufacturer_id,))
    colors = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('select_filament.html', manufacturer_id=manufacturer_id, types=types, colors=colors)

@app.route('/select_location/<int:manufacturer_id>/<filament_type>/<color_name>')
def select_location(manufacturer_id, filament_type, color_name):
    return render_template('select_location.html', manufacturer_id=manufacturer_id, filament_type=filament_type, color_name=color_name)

@app.route('/add_inventory', methods=['POST'])
def add_inventory():
    manufacturer_id = request.form['manufacturer_id']
    filament_type = request.form['filament_type']
    color_name = request.form['color_name']
    location = request.form['location']
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        sql.SQL("INSERT INTO inventory (manufacturer_id, filament_type, color_name, location) VALUES (%s, %s, %s, %s)"),
        (manufacturer_id, filament_type, color_name, location)
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
        SELECT m.name, i.filament_type, i.color_name, i.location 
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