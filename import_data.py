import psycopg2

def get_db_connection():
    conn = psycopg2.connect(
        host="localhost",
        database="filament_inventory",
        user="your_username",
        password="your_password"
    )
    return conn

def import_data():
    conn = get_db_connection()
    cur = conn.cursor()

    # Clear existing data
    cur.execute('TRUNCATE TABLE filament CASCADE;')
    cur.execute('TRUNCATE TABLE manufacturer CASCADE;')

    # Import manufacturers
    manufacturers = set()
    with open('filaments.txt', 'r') as f:
        for line in f:
            manufacturer = line.strip().split(',')[0]
            manufacturers.add(manufacturer)

    for manufacturer in manufacturers:
        cur.execute('INSERT INTO manufacturer (name) VALUES (%s) RETURNING id;', (manufacturer,))
        manufacturer_id = cur.fetchone()[0]

    # Create tables if they don't exist
    cur.execute('''
        CREATE TABLE IF NOT EXISTS manufacturer (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) UNIQUE NOT NULL
        );
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS filament (
            id SERIAL PRIMARY KEY,
            manufacturer_id INTEGER REFERENCES manufacturer(id),
            type VARCHAR(50) NOT NULL,
            color_name VARCHAR(50) NOT NULL,
            color_hex_code CHAR(7) NOT NULL
        );
    ''')

    # Import filaments
    with open('filaments.txt', 'r') as f:
        for line in f:
            manufacturer, filament_type, color_name, color_hex_code = line.strip().split(',')
            cur.execute('SELECT id FROM manufacturer WHERE name = %s;', (manufacturer,))
            manufacturer_id = cur.fetchone()[0]
            cur.execute('''
                INSERT INTO filament (manufacturer_id, type, color_name, color_hex_code)
                VALUES (%s, %s, %s, %s);
            ''', (manufacturer_id, filament_type, color_name, color_hex_code))

    conn.commit()
    cur.close()
    conn.close()

if __name__ == '__main__':
    import_data()
    print("Data import completed successfully.")
