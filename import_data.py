import psycopg2

def get_db_connection():
    conn = psycopg2.connect(
        host="localhost",
        database="filament_inventory",
        user="your_username",
        password="your_password"
    )
    return conn


if __name__ == '__main__':
    import_data()
    print("Data import completed successfully.")
