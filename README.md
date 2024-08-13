Filament Inventory Application
==============================

## Overview

This application is designed to manage a filament inventory for 3D printing. It interfaces with a PostgreSQL database and provides a web interface for users to interact with the inventory. The application is written in Python and uses Flask as the web framework.


## Ground rules
1. Be brief
2. Diffs only
3. No dropdowns or text entry - use well-spaced buttons only
4. 8 shelves, each with 4 positions (Left Front, Left Back, Right Front, Right Back)
5. Never remove files from chat


## Features

1. **Manufacturer Selection**: Users can select a manufacturer from a list, which is populated from the database.
2. **Filament Selection**: Based on the selected manufacturer, users can pick a filament type and color. The available options are read from the database.
4. **View Inventory**: Users can view the entire inventory, which includes details such as manufacturer, filament type, color, and storage location.
5. **Add Inventory**: Users can add new inventory items by selecting the manufacturer, filament type, color, and location.

## Database Structure

The application uses two main tables within the PostgreSQL database:

- **Manufacturer**: Contains `id` (primary key) and `name` of the filament manufacturers.
- **Filament**: Contains `id` (primary key), `manufacturer_id` (foreign key), `type`, `color_name`, and `color_hex_code`.
- **Inventory**: Contains `id` (primary key), `manufacturer_id` (foreign key), `filament_type`, `color_name`, `color_hex_code`, and `location`.

There is a many-to-one relationship from Filament to Manufacturer, indicated by the `manufacturer_id` foreign key.

## Database Setup

To set up the necessary tables in your PostgreSQL database, use the following SQL commands:

```sql
-- Create Manufacturer table
CREATE TABLE IF NOT EXISTS manufacturer (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

-- Create Filament table
CREATE TABLE IF NOT EXISTS filament (
    id SERIAL PRIMARY KEY,
    manufacturer_id INTEGER REFERENCES manufacturer(id),
    type VARCHAR(50) NOT NULL,
    color_name VARCHAR(50) NOT NULL,
    color_hex_code CHAR(7) NOT NULL
);

-- Alter Inventory table
ALTER TABLE inventory
DROP COLUMN manufacturer_id,
DROP COLUMN filament_type,
DROP COLUMN color_name,
DROP COLUMN color_hex_code,
ADD COLUMN filament_id INTEGER REFERENCES filament(id);

-- Create Inventory table (new structure)
CREATE TABLE IF NOT EXISTS inventory (
    id SERIAL PRIMARY KEY,
    filament_id INTEGER REFERENCES filament(id),
    location VARCHAR(50),
    quantity INTEGER DEFAULT 1
);
```

These commands will create the Manufacturer, Filament, and Inventory tables with the appropriate relationships between them.

## Configuration

The application requires a configuration file to connect to the database and the Spoolman API for exporting data.

## Usage

To run the application, ensure that you have Python and Flask installed, and then execute the `app.py` script. The web interface can be accessed via a web browser.

## Customization

The application's appearance can be customized with basic CSS. It includes classes for large, medium, small, and red buttons to suit various design preferences.

## Export to Spoolman

The application can export data to the Spoolman app using the Spoolman API, although the details of this functionality are not specified in the history provided.

## Development Notes

The application is currently in development, and features such as authentication and more detailed export functionality may be added in the future.

## Disclaimer

This README is based on the provided `.aider.chat.history.md` file and summarizes the application's requirements and functionality as understood from the chat history.
