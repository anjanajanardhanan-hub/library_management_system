Library Management System

Project Overview

The Library Management System is a command-line application developed using Python and SQLite3. It helps manage library books, members, and borrowing transactions.

Technologies Used

- Python 3
- SQLite3
- SQL

Features

- Admin login and member registration
- Secure password hashing
- Add, view, search, update, and delete books
- Register and manage library members
- Issue and return books
- Automatic 14-day borrowing period
- Track overdue books
- View borrowing history
- Member login and personal borrowing details

Project Structure

- "main.py" – Main application and menus
- "database.py" – Database setup and management
- "authentication.py" – Login, registration, and password validation
- "books.py" – Book management
- "members.py" – Member management
- "borrowing.py" – Issue and return operations
- "test_system.py" – Automated tests

How to Run

1. Install Python 3.
2. Download or clone this repository.
3. Open the project folder in VS Code.
4. Run:

python main.py

The SQLite database is initialized automatically when the application starts.

Default Admin Login

- Username: "admin"
- Password: "Admin@123"

Change the default password before using this application in a real environment.

Author

Anjana Janardhanan
