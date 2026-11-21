import sqlite3
import os
from datetime import date, timedelta


DB_NAME = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "library.db")


# Connect to database
def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


# Create database tables
def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'member'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            book_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            category TEXT NOT NULL,
            isbn TEXT UNIQUE NOT NULL,
            total_copies INTEGER NOT NULL,
            available_copies INTEGER NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS members (
            member_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            join_date TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
            ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS issued_books (
            issue_id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            member_id INTEGER NOT NULL,
            issue_date TEXT NOT NULL,
            due_date TEXT NOT NULL,
            return_date TEXT,
            status TEXT NOT NULL CHECK(status IN ('Issued', 'Returned')),
            FOREIGN KEY(book_id) REFERENCES books(book_id),
            FOREIGN KEY(member_id) REFERENCES members(member_id)
        )
    """)

    conn.commit()
    conn.close()


# Create default admin account
def seed_default_admin():
    from authentication import hash_password

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT user_id FROM users WHERE username = ?",
        ("admin",)
    )

    if cursor.fetchone() is None:
        password = hash_password("Admin@123")

        cursor.execute("""
            INSERT INTO users (username, password, role)
            VALUES (?, ?, ?)
        """, ("admin", password, "admin"))

    conn.commit()
    conn.close()


# Add sample books and members
def seed_sample_data():
    from authentication import hash_password

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM books")

    if cursor.fetchone()[0] == 0:

        books_list = [
            ("Introduction to Algorithms", "Thomas H. Cormen",
             "Computer Science", "978-0262033848", 5, 4),
            ("Clean Code", "Robert C. Martin",
             "Software Engineering", "978-0132350884", 4, 3),
            ("Design Patterns", "Erich Gamma et al.",
             "Software Engineering", "978-0201633610", 3, 3),
            ("Artificial Intelligence: A Modern Approach", "Stuart Russell",
             "Artificial Intelligence", "978-0136042594", 4, 4),
            ("Database System Concepts", "Abraham Silberschatz",
             "Database Systems", "978-0073523323", 5, 5),
            ("Python Crash Course", "Eric Matthes",
             "Programming", "978-1593279288", 6, 6),
            ("The Pragmatic Programmer", "David Thomas & Andrew Hunt",
             "Software Engineering", "978-0135957059", 4, 4),
            ("Computer Networks", "Andrew S. Tanenbaum",
             "Networking", "978-0132126953", 3, 3)
        ]

        cursor.executemany("""
            INSERT INTO books
            (title, author, category, isbn, total_copies, available_copies)
            VALUES (?, ?, ?, ?, ?, ?)
        """, books_list)

    cursor.execute("SELECT COUNT(*) FROM members")

    if cursor.fetchone()[0] == 0:

        today = date.today().strftime("%Y-%m-%d")

        members_list = [
            ("john_doe", "John Doe", "john.doe@example.com", "9876543210"),
            ("jane_smith", "Jane Smith", "jane.smith@example.com", "9876543211")
        ]

        for username, name, email, phone in members_list:

            password = hash_password("Member@123")

            cursor.execute("""
                INSERT INTO users (username, password, role)
                VALUES (?, ?, ?)
            """, (username, password, "member"))

            user_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO members
                (user_id, full_name, email, phone, join_date)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, name, email, phone, today))

        # Add sample borrowing records
        cursor.execute("SELECT member_id FROM members WHERE email = ?",
                       ("john.doe@example.com",))
        john = cursor.fetchone()

        cursor.execute("SELECT member_id FROM members WHERE email = ?",
                       ("jane.smith@example.com",))
        jane = cursor.fetchone()

        if john and jane:
            issue_date = (date.today() - timedelta(days=4)
                          ).strftime("%Y-%m-%d")
            due_date = (date.today() + timedelta(days=10)).strftime("%Y-%m-%d")

            cursor.execute("""
                INSERT INTO issued_books
                (book_id, member_id, issue_date, due_date, status)
                VALUES (?, ?, ?, ?, ?)
            """, (1, john["member_id"], issue_date, due_date, "Issued"))

            old_issue = (date.today() - timedelta(days=20)
                         ).strftime("%Y-%m-%d")
            old_due = (date.today() - timedelta(days=6)).strftime("%Y-%m-%d")

            cursor.execute("""
                INSERT INTO issued_books
                (book_id, member_id, issue_date, due_date, status)
                VALUES (?, ?, ?, ?, ?)
            """, (2, jane["member_id"], old_issue, old_due, "Issued"))

    conn.commit()
    conn.close()


# Initialize database
def init_db():
    create_tables()
    seed_default_admin()
    seed_sample_data()


# Display data in table format
def print_table(headers, rows, max_col_width=35):

    if not rows:
        print("No records found.")
        return

    data = []

    for row in rows:
        values = []

        for item in row:
            value = str(item) if item is not None else "N/A"

            if len(value) > max_col_width:
                value = value[:max_col_width - 3] + "..."

            values.append(value)

        data.append(values)

    widths = []

    for i in range(len(headers)):
        max_length = max(len(str(headers[i])),
                         max(len(row[i]) for row in data))
        widths.append(max_length)

    border = "+" + "+".join("-" * (w + 2) for w in widths) + "+"

    print(border)

    header = "|"

    for i in range(len(headers)):
        header += " " + str(headers[i]).center(widths[i]) + " |"

    print(header)
    print(border)

    for row in data:
        line = "|"

        for i in range(len(row)):
            line += " " + row[i].ljust(widths[i]) + " |"

        print(line)

    print(border)


if __name__ == "__main__":
    init_db()
    print("Database created successfully!")
