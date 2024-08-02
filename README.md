Filament Inventory Application
==============================

## Overview

This application is designed to manage a filament inventory for 3D printing. It interfaces with a PostgreSQL database and provides a web interface for users to interact with the inventory. The application is written in Python and uses Flask as the web framework.

## Features

1. **Manufacturer Selection**: Users can select a manufacturer from a list, which is populated from the database.
2. **Filament Selection**: Based on the selected manufacturer, users can pick a filament type and color. The available options are read from the database.
3. **Location Selection**: Users can pick a storage location for the filament, which includes options for shelf number (1-8), side (left or right), and position (front or back). This is presented in a grid format.
4. **View Inventory**: Users can view the entire inventory, which includes details such as manufacturer, filament type, color, and storage location.
5. **Add Inventory**: Users can add new inventory items by selecting the manufacturer, filament type, color, and location.

## Database Structure

The application uses two main tables within the PostgreSQL database:

- **Manufacturer**: Contains `id` (primary key) and `name` of the filament manufacturers.
- **Filament**: Contains `id` (primary key), `manufacturer_id` (foreign key), `type`, `color_name`, and `color_hex_code`.

There is a many-to-one relationship from Filament to Manufacturer, indicated by the `manufacturer_id` foreign key.

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
