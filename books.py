import sqlite3
from database import get_connection, print_table


# Add a new book
def add_book():
    print("\n========== ADD NEW BOOK ==========")

    title = input("Enter Book Title: ").strip()
    author = input("Enter Author Name: ").strip()
    category = input("Enter Category: ").strip()
    isbn = input("Enter ISBN: ").strip()

    if not title or not author or not category or not isbn:
        print("All book details are required.")
        return

    try:
        total_copies = int(input("Enter Total Copies: "))

        if total_copies <= 0:
            print("Copies must be greater than zero.")
            return

    except ValueError:
        print("Please enter a valid number.")
        return

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT book_id FROM books WHERE isbn = ?",
            (isbn,)
        )

        if cursor.fetchone():
            print("This ISBN already exists.")
            return

        cursor.execute("""
            INSERT INTO books
            (title, author, category, isbn, total_copies, available_copies)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (title, author, category, isbn, total_copies, total_copies))

        conn.commit()

        print("Book added successfully!")
        print("Book ID:", cursor.lastrowid)

    except sqlite3.Error as e:
        print("Database error:", e)

    finally:
        conn.close()


# View all books
def view_all_books():
    print("\n========== ALL BOOKS ==========")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT book_id, title, author, category, isbn,
                   total_copies, available_copies
            FROM books
            ORDER BY book_id
        """)

        books_list = cursor.fetchall()

        headers = ["ID", "Title", "Author", "Category",
                   "ISBN", "Total", "Available"]

        rows = [
            [b["book_id"], b["title"], b["author"], b["category"],
             b["isbn"], b["total_copies"], b["available_copies"]]
            for b in books_list
        ]

        print_table(headers, rows)
        print("Total books:", len(books_list))

    except sqlite3.Error as e:
        print("Error:", e)

    finally:
        conn.close()


# View books that are available
def view_available_books():
    print("\n========== AVAILABLE BOOKS ==========")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT book_id, title, author, category, isbn, available_copies
            FROM books
            WHERE available_copies > 0
            ORDER BY title
        """)

        books_list = cursor.fetchall()

        headers = ["ID", "Title", "Author", "Category",
                   "ISBN", "Available Copies"]

        rows = [
            [b["book_id"], b["title"], b["author"], b["category"],
             b["isbn"], b["available_copies"]]
            for b in books_list
        ]

        print_table(headers, rows)

    except sqlite3.Error as e:
        print("Error:", e)

    finally:
        conn.close()


# Search books
def search_books():
    print("\n========== SEARCH BOOKS ==========")
    print("1. Search by Title")
    print("2. Search by Author")
    print("3. Search by Category")
    print("4. Search by ISBN")
    print("5. Back")

    choice = input("Enter your choice: ").strip()

    columns = {
        "1": "title",
        "2": "author",
        "3": "category",
        "4": "isbn"
    }

    if choice == "5":
        return

    if choice not in columns:
        print("Invalid choice.")
        return

    search_value = input("Enter search text: ").strip()

    if not search_value:
        print("Search text cannot be empty.")
        return

    column = columns[choice]

    conn = get_connection()
    cursor = conn.cursor()

    try:
        query = f"""
            SELECT book_id, title, author, category, isbn,
                   total_copies, available_copies
            FROM books
            WHERE {column} LIKE ?
            ORDER BY book_id
        """

        cursor.execute(query, ("%" + search_value + "%",))
        results = cursor.fetchall()

        headers = ["ID", "Title", "Author", "Category",
                   "ISBN", "Total", "Available"]

        rows = [
            [b["book_id"], b["title"], b["author"], b["category"],
             b["isbn"], b["total_copies"], b["available_copies"]]
            for b in results
        ]

        print("Search results:", len(results))
        print_table(headers, rows)

    except sqlite3.Error as e:
        print("Search error:", e)

    finally:
        conn.close()


# View one book's details
def view_book_details():
    print("\n========== BOOK DETAILS ==========")

    try:
        book_id = int(input("Enter Book ID: "))
    except ValueError:
        print("Enter a valid Book ID.")
        return

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT * FROM books WHERE book_id = ?",
            (book_id,)
        )

        book = cursor.fetchone()

        if not book:
            print("Book not found.")
            return

        print("\nBook ID:", book["book_id"])
        print("Title:", book["title"])
        print("Author:", book["author"])
        print("Category:", book["category"])
        print("ISBN:", book["isbn"])
        print("Total Copies:", book["total_copies"])
        print("Available Copies:", book["available_copies"])

        issued = book["total_copies"] - book["available_copies"]
        print("Currently Issued:", issued)

        cursor.execute("""
            SELECT issue_id, member_id, issue_date, due_date
            FROM issued_books
            WHERE book_id = ? AND status = 'Issued'
        """, (book_id,))

        loans = cursor.fetchall()

        if loans:
            print("\nCurrent Borrowing Records:")

            headers = ["Issue ID", "Member ID", "Issue Date", "Due Date"]
            rows = [
                [loan["issue_id"], loan["member_id"],
                 loan["issue_date"], loan["due_date"]]
                for loan in loans
            ]

            print_table(headers, rows)
        else:
            print("No active borrowing records.")

    except sqlite3.Error as e:
        print("Error:", e)

    finally:
        conn.close()


# Update book details
def update_book():
    print("\n========== UPDATE BOOK ==========")

    try:
        book_id = int(input("Enter Book ID: "))
    except ValueError:
        print("Invalid Book ID.")
        return

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT * FROM books WHERE book_id = ?",
            (book_id,)
        )

        book = cursor.fetchone()

        if not book:
            print("Book not found.")
            return

        issued = book["total_copies"] - book["available_copies"]

        print("Leave blank to keep the old value.")

        title = input("New Title: ").strip() or book["title"]
        author = input("New Author: ").strip() or book["author"]
        category = input("New Category: ").strip() or book["category"]
        isbn = input("New ISBN: ").strip() or book["isbn"]

        if isbn != book["isbn"]:
            cursor.execute(
                "SELECT book_id FROM books WHERE isbn = ? AND book_id != ?",
                (isbn, book_id)
            )

            if cursor.fetchone():
                print("This ISBN is already used by another book.")
                return

        copies = input("New Total Copies: ").strip()

        if copies:
            try:
                total = int(copies)

                if total < issued:
                    print("Cannot reduce copies below the number currently issued.")
                    return

                if total < 0:
                    print("Copies cannot be negative.")
                    return

                available = total - issued

            except ValueError:
                print("Enter a valid number.")
                return

        else:
            total = book["total_copies"]
            available = book["available_copies"]

        cursor.execute("""
            UPDATE books
            SET title = ?, author = ?, category = ?, isbn = ?,
                total_copies = ?, available_copies = ?
            WHERE book_id = ?
        """, (title, author, category, isbn, total, available, book_id))

        conn.commit()
        print("Book updated successfully!")

    except sqlite3.Error as e:
        conn.rollback()
        print("Update error:", e)

    finally:
        conn.close()


# Delete a book
def delete_book():
    print("\n========== DELETE BOOK ==========")

    try:
        book_id = int(input("Enter Book ID: "))
    except ValueError:
        print("Invalid Book ID.")
        return

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT * FROM books WHERE book_id = ?",
            (book_id,)
        )

        book = cursor.fetchone()

        if not book:
            print("Book not found.")
            return

        cursor.execute("""
            SELECT COUNT(*) FROM issued_books
            WHERE book_id = ? AND status = 'Issued'
        """, (book_id,))

        active_loans = cursor.fetchone()[0]

        if active_loans > 0:
            print("Cannot delete this book. Some copies are still borrowed.")
            return

        cursor.execute("""
            SELECT COUNT(*) FROM issued_books
            WHERE book_id = ?
        """, (book_id,))

        history = cursor.fetchone()[0]

        if history > 0:
            print("This book has previous borrowing records.")
            print("Deleting it will also delete those records.")

        confirm = input("Are you sure you want to delete? (y/n): ").lower()

        if confirm != "y":
            print("Deletion cancelled.")
            return

        # Remove old borrowing records before deleting the book
        if history > 0:
            cursor.execute(
                "DELETE FROM issued_books WHERE book_id = ?",
                (book_id,)
            )

        cursor.execute(
            "DELETE FROM books WHERE book_id = ?",
            (book_id,)
        )

        conn.commit()
        print("Book deleted successfully!")

    except sqlite3.Error as e:
        conn.rollback()
        print("Delete error:", e)

    finally:
        conn.close()
