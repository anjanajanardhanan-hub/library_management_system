import sqlite3
from datetime import date, timedelta
from database import get_connection, print_table


# 1. Issue a book
def issue_book():
    print("\n--- ISSUE A BOOK ---")

    try:
        member_id = int(input("Enter Member ID: "))
        book_id = int(input("Enter Book ID: "))
    except ValueError:
        print("Please enter valid numeric IDs.")
        return

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Check whether the member exists
        cursor.execute(
            "SELECT * FROM members WHERE member_id = ?",
            (member_id,)
        )
        member = cursor.fetchone()

        if not member:
            print("Member not found.")
            return

        # Check whether the book exists
        cursor.execute(
            "SELECT * FROM books WHERE book_id = ?",
            (book_id,)
        )
        book = cursor.fetchone()

        if not book:
            print("Book not found.")
            return

        if book["available_copies"] <= 0:
            print("No copies are available.")
            return

        # Check whether the member already has this book
        cursor.execute("""
            SELECT * FROM issued_books
            WHERE member_id = ? AND book_id = ? AND status = 'Issued'
        """, (member_id, book_id))

        existing_loan = cursor.fetchone()

        if existing_loan:
            print("This member already has this book.")
            answer = input("Issue another copy? (y/n): ").lower()

            if answer != "y":
                print("Issue cancelled.")
                return

        # Set issue date and due date
        today = date.today()
        issue_date = today.isoformat()
        due_date = (today + timedelta(days=14)).isoformat()

        # Save the borrowing record
        cursor.execute("""
            INSERT INTO issued_books
            (book_id, member_id, issue_date, due_date, return_date, status)
            VALUES (?, ?, ?, ?, NULL, 'Issued')
        """, (book_id, member_id, issue_date, due_date))

        issue_id = cursor.lastrowid

        # Reduce available book copies
        cursor.execute("""
            UPDATE books
            SET available_copies = available_copies - 1
            WHERE book_id = ?
        """, (book_id,))

        conn.commit()

        print("\nBook issued successfully!")
        print("Issue ID:", issue_id)
        print("Book:", book["title"])
        print("Member:", member["full_name"])
        print("Issue Date:", issue_date)
        print("Due Date:", due_date)

    except sqlite3.Error as e:
        conn.rollback()
        print("Database error:", e)

    finally:
        conn.close()


# 2. Return a book
def return_book():
    print("\n--- RETURN A BOOK ---")

    try:
        issue_id = int(input("Enter Issue ID: "))
    except ValueError:
        print("Please enter a valid Issue ID.")
        return

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT ib.*, b.title
            FROM issued_books ib
            JOIN books b ON ib.book_id = b.book_id
            WHERE ib.issue_id = ?
        """, (issue_id,))

        record = cursor.fetchone()

        if not record:
            print("Issue record not found.")
            return

        if record["status"] == "Returned":
            print("This book has already been returned.")
            return

        today = date.today()
        return_date = today.isoformat()
        due_date = date.fromisoformat(record["due_date"])

        days_overdue = (today - due_date).days

        # Update the issue record
        cursor.execute("""
            UPDATE issued_books
            SET return_date = ?, status = 'Returned'
            WHERE issue_id = ? AND status = 'Issued'
        """, (return_date, issue_id))

        # Increase available copies
        cursor.execute("""
            UPDATE books
            SET available_copies = available_copies + 1
            WHERE book_id = ?
        """, (record["book_id"],))

        conn.commit()

        print("\nBook returned successfully!")
        print("Book:", record["title"])
        print("Return Date:", return_date)

        if days_overdue > 0:
            print("Overdue by", days_overdue, "days.")
        else:
            print("Book returned on time.")

    except sqlite3.Error as e:
        conn.rollback()
        print("Database error:", e)

    finally:
        conn.close()


# 3. View all currently issued books
def view_all_issued_books():
    print("\n--- CURRENTLY ISSUED BOOKS ---")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT ib.issue_id, b.title, m.full_name,
                   m.phone, ib.issue_date, ib.due_date
            FROM issued_books ib
            JOIN books b ON ib.book_id = b.book_id
            JOIN members m ON ib.member_id = m.member_id
            WHERE ib.status = 'Issued'
            ORDER BY ib.due_date
        """)

        records = cursor.fetchall()
        headers = [
            "Issue ID", "Book", "Member", "Phone",
            "Issue Date", "Due Date", "Status"
        ]

        rows = []
        today = date.today()

        for record in records:
            due_date = date.fromisoformat(record["due_date"])
            days_left = (due_date - today).days

            if days_left < 0:
                status = f"Overdue ({-days_left} days)"
            elif days_left == 0:
                status = "Due Today"
            else:
                status = f"{days_left} days left"

            rows.append([
                record["issue_id"],
                record["title"],
                record["full_name"],
                record["phone"],
                record["issue_date"],
                record["due_date"],
                status
            ])

        print_table(headers, rows)
        print("Total issued books:", len(records))

    except sqlite3.Error as e:
        print("Database error:", e)

    finally:
        conn.close()


# 4. View overdue books
def view_overdue_books():
    print("\n--- OVERDUE BOOKS ---")

    today = date.today()
    today_str = today.isoformat()

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT ib.issue_id, b.title, m.full_name,
                   m.phone, ib.due_date
            FROM issued_books ib
            JOIN books b ON ib.book_id = b.book_id
            JOIN members m ON ib.member_id = m.member_id
            WHERE ib.status = 'Issued' AND ib.due_date < ?
            ORDER BY ib.due_date
        """, (today_str,))

        records = cursor.fetchall()

        headers = [
            "Issue ID", "Book", "Member",
            "Phone", "Due Date", "Days Overdue"
        ]

        rows = []

        for record in records:
            due_date = date.fromisoformat(record["due_date"])
            days_late = (today - due_date).days

            rows.append([
                record["issue_id"],
                record["title"],
                record["full_name"],
                record["phone"],
                record["due_date"],
                days_late
            ])

        if records:
            print_table(headers, rows)
        else:
            print("There are no overdue books.")

        print("Total overdue books:", len(records))

    except sqlite3.Error as e:
        print("Database error:", e)

    finally:
        conn.close()


# 5. View complete borrowing history
def view_borrowing_history():
    print("\n--- COMPLETE BORROWING HISTORY ---")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT ib.issue_id, b.title, m.full_name,
                   ib.issue_date, ib.due_date,
                   ib.return_date, ib.status
            FROM issued_books ib
            JOIN books b ON ib.book_id = b.book_id
            JOIN members m ON ib.member_id = m.member_id
            ORDER BY ib.issue_id DESC
        """)

        records = cursor.fetchall()

        headers = [
            "Issue ID", "Book", "Member",
            "Issue Date", "Due Date", "Return Date", "Status"
        ]

        rows = []

        for record in records:
            return_date = record["return_date"]

            if not return_date:
                return_date = "Not Returned"

            rows.append([
                record["issue_id"],
                record["title"],
                record["full_name"],
                record["issue_date"],
                record["due_date"],
                return_date,
                record["status"]
            ])

        print_table(headers, rows)
        print("Total records:", len(records))

    except sqlite3.Error as e:
        print("Database error:", e)

    finally:
        conn.close()


# 6. View books borrowed by a particular member
def view_member_borrowed_books(member_id):
    print("\n--- MY BORROWED BOOKS ---")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT ib.issue_id, b.title, b.author, b.isbn,
                   ib.issue_date, ib.due_date
            FROM issued_books ib
            JOIN books b ON ib.book_id = b.book_id
            WHERE ib.member_id = ? AND ib.status = 'Issued'
            ORDER BY ib.due_date
        """, (member_id,))

        records = cursor.fetchall()

        headers = [
            "Issue ID", "Title", "Author", "ISBN",
            "Issue Date", "Due Date", "Timeline"
        ]

        rows = []
        today = date.today()

        for record in records:
            due_date = date.fromisoformat(record["due_date"])
            days_left = (due_date - today).days

            if days_left < 0:
                timeline = f"Overdue ({-days_left} days)"
            elif days_left == 0:
                timeline = "Due Today"
            else:
                timeline = f"{days_left} days left"

            rows.append([
                record["issue_id"],
                record["title"],
                record["author"],
                record["isbn"],
                record["issue_date"],
                record["due_date"],
                timeline
            ])

        if records:
            print_table(headers, rows)
        else:
            print("You have no currently borrowed books.")

    except sqlite3.Error as e:
        print("Database error:", e)

    finally:
        conn.close()


# 7. View personal borrowing history
def view_member_borrowing_history(member_id):
    print("\n--- MY BORROWING HISTORY ---")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT ib.issue_id, b.title, b.author,
                   ib.issue_date, ib.due_date,
                   ib.return_date, ib.status
            FROM issued_books ib
            JOIN books b ON ib.book_id = b.book_id
            WHERE ib.member_id = ?
            ORDER BY ib.issue_id DESC
        """, (member_id,))

        records = cursor.fetchall()

        headers = [
            "Issue ID", "Title", "Author",
            "Issue Date", "Due Date", "Return Date", "Status"
        ]

        rows = []

        for record in records:
            return_date = record["return_date"]

            if not return_date:
                return_date = "Still Borrowed"

            rows.append([
                record["issue_id"],
                record["title"],
                record["author"],
                record["issue_date"],
                record["due_date"],
                return_date,
                record["status"]
            ])

        if records:
            print_table(headers, rows)
        else:
            print("You have no borrowing history.")

    except sqlite3.Error as e:
        print("Database error:", e)

    finally:
        conn.close()
