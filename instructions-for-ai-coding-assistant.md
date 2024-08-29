# Instructions for AI Coding Assistant to Recreate the Filament Inventory App

To recreate this Filament Inventory App, you'll need to guide the AI through the following steps:

1. Project Setup:
   - Create a new Python project
   - Set up a virtual environment
   - Install required dependencies (FastAPI, SQLAlchemy, Jinja2, etc.)

2. Database Design:
   - Design tables for Manufacturer, Filament, and Inventory
   - Implement SQLAlchemy models for these tables

3. FastAPI Application:
   - Set up the main FastAPI application
   - Implement database connection and session management
   - Create API routes for all CRUD operations

4. HTML Templates:
   - Create Jinja2 templates for all pages (index, select_manufacturer, select_filament, select_color, select_location, view_inventory)
   - Implement a base template for consistent layout

5. Static Files:
   - Create a CSS file for styling
   - Add any necessary images or icons

6. Business Logic:
   - Implement functions for selecting manufacturers, filaments, colors, and locations
   - Create inventory management logic

7. Error Handling:
   - Implement proper error handling and display error messages to users

8. Logging:
   - Set up logging to track application events and errors

9. Environment Variables:
   - Use environment variables for sensitive information like database credentials

10. Docker Configuration:
    - Create a Dockerfile for containerization
    - Set up docker-compose for easy deployment

11. Build and Deployment Script:
    - Create a script to build the Docker image and push it to a registry

12. Testing:
    - Implement unit tests for core functionality
    - Set up integration tests for API endpoints

13. Documentation:
    - Create API documentation using FastAPI's built-in Swagger UI
    - Write a README file with setup and usage instructions

14. Version Control:
    - Initialize a Git repository
    - Create a .gitignore file to exclude unnecessary files

15. Security:
    - Implement proper security measures (HTTPS, input validation, etc.)

When guiding the AI, provide detailed instructions for each component, including code snippets and explanations. Ask the AI to implement one feature at a time, and review the code after each implementation. Be sure to provide context about the filament inventory domain and any specific requirements for the application.
