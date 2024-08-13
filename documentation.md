# Filament Inventory Application Documentation

## Overview

This application is designed to manage a filament inventory for 3D printing. It interfaces with a PostgreSQL database and provides a web interface for users to interact with the inventory. The application is written in Python and uses Flask as the web framework.

## Key Files and Their Purposes

### Python Files

1. `app.py`
   - Main application file
   - Contains all route definitions and core logic
   - Handles database connections and queries

2. `import_data.py`
   - Currently not in use for data import
   - Retained for potential future use or reference

### HTML Templates

1. `base.html`
   - Base template that all other templates extend
   - Contains the basic HTML structure, CSS link, and common JavaScript

2. `index.html`
   - Home page of the application
   - Provides links to add inventory and view inventory

3. `select_manufacturer.html`
   - Displays buttons for selecting a manufacturer

4. `select_filament_type.html`
   - Shows filament types for the selected manufacturer

5. `select_color.html`
   - Presents color options for the selected filament type

6. `select_location.html`
   - Displays a grid of shelves and positions for inventory placement

7. `view_inventory.html`
   - Shows the current inventory in a table format
   - Includes sorting and filtering functionality

8. `error.html`
   - Generic error page for displaying error messages

### CSS File

1. `static/style.css`
   - Contains all the styling for the application

### Configuration Files

1. `.env`
   - Contains environment variables for database connection

### Other Files

1. `README.md`
   - Provides an overview of the application, setup instructions, and other relevant information

## Workflow

1. User starts at the home page (`index.html`)
2. To add inventory:
   - Select manufacturer (`select_manufacturer.html`)
   - Choose filament type (`select_filament_type.html`)
   - Pick a color (`select_color.html`)
   - Select a location (`select_location.html`)
3. To view inventory:
   - Navigate to the inventory page (`view_inventory.html`)
   - Use built-in sorting and filtering options


## Database Structure

The application uses a PostgreSQL database with the following main tables:

1. Manufacturer
2. Filament
3. Inventory

Detailed table structures can be found in the README.md file.

## Future Improvements

1. Integrate with external inventory management systems

For more detailed information about setup, configuration, and usage, please refer to the README.md file in the repository.
