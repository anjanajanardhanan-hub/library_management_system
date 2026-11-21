import os
import sqlite3
from datetime import date, timedelta

from database import get_connection, init_db, DB_NAME
from authentication import (
    hash_password,
    verify_password,
    is_valid_email,
    is_valid_phone,
    is_valid_username
)


def run_tests():

    print("\n--- LIBRARY MANAGEMENT SYSTEM TESTS ---")

    # 1. Check database creation
    init_db()

    assert os.path.exists(DB_NAME), "Database file not found!"
    print("Test 1 passed: Database created.")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # 2. Check foreign keys
        cursor.execute("PRAGMA foreign_keys")
        result = cursor.fetchone()[0]

        assert result == 1, "Foreign keys are not enabled!"
        print("Test 2 passed: Foreign keys enabled.")

        # 3. Check admin account
        cursor.execute(
            "SELECT * FROM users WHERE username = ?",
            ("admin",)
        )

        admin = cursor.fetchone()

        assert admin is not None, "Admin account not found!"
        assert admin["role"] == "admin"
        assert verify_password("Admin@123", admin["password"])

        print("Test 3 passed: Admin login details verified.")

        # 4. Check input validation
        assert is_valid_email("test@example.com")[0]
        assert not is_valid_email("wrong-email")[0]

        assert is_valid_phone("9876543210")[0]
        assert not is_valid_phone("123")[0]

        assert is_valid_username("valid_user123")[0]
        assert not is_valid_username("ab")[0]

        print("Test 4 passed: Input validation.")

        # 5. Check sample books
        cursor.execute("SELECT COUNT(*) FROM books")
        book_count = cursor.fetchone()[0]

        assert book_count >= 8, "Sample books are missing!"
        print("Test 5 passed: Sample books found.")

        # 6. Add a test book
        test_isbn = "978-9999999999"

        cursor.execute(
            "DELETE FROM books WHERE isbn = ?",
            (test_isbn,)
        )

        cursor.execute("""
            INSERT INTO books
            (title, author, category, isbn, total_copies, available_copies)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            "Test Book",
            "Test Author",
            "Testing",
            test_isbn,
            3,
            3
        ))

        test_book_id = cursor.lastrowid
        conn.commit()

        print("Test 6 passed: Book added.")

        # 7. Create a test member
        test_username = "test_member_99"

        cursor.execute(
            "DELETE FROM users WHERE username = ?",
            (test_username,)
        )

        password = hash_password("Test@12345")

        cursor.execute("""
            INSERT INTO users (username, password, role)
            VALUES (?, ?, ?)
        """, (test_username, password, "member"))

        user_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO members
            (user_id, full_name, email, phone, join_date)
            VALUES (?, ?, ?, ?, ?)
        """, (
            user_id,
            "Test Member",
            "test.member@example.com",
            "9988776655",
            str(date.today())
        ))

        member_id = cursor.lastrowid
        conn.commit()

        print("Test 7 passed: Member created.")

        # 8. Issue the test book
        cursor.execute("""
            SELECT available_copies
            FROM books
            WHERE book_id = ?
        """, (test_book_id,))

        available = cursor.fetchone()["available_copies"]

        assert available == 3

        issue_date = date.today()
        due_date = issue_date + timedelta(days=14)

        cursor.execute("""
            INSERT INTO issued_books
            (book_id, member_id, issue_date, due_date, return_date, status)
            VALUES (?, ?, ?, ?, NULL, 'Issued')
        """, (
            test_book_id,
            member_id,
            issue_date.isoformat(),
            due_date.isoformat()
        ))

        issue_id = cursor.lastrowid

        cursor.execute("""
            UPDATE books
            SET available_copies = available_copies - 1
            WHERE book_id = ?
        """, (test_book_id,))

        conn.commit()

        cursor.execute("""
            SELECT available_copies
            FROM books
            WHERE book_id = ?
        """, (test_book_id,))

        available = cursor.fetchone()["available_copies"]

        assert available == 2
        print("Test 8 passed: Book issued and copies reduced.")

        # 9. Check active loans
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM issued_books
            WHERE member_id = ? AND status = 'Issued'
        """, (member_id,))

        active_loans = cursor.fetchone()["total"]

        assert active_loans > 0
        print("Test 9 passed: Active loan detected.")

        # 10. Return the test book
        return_date = date.today().isoformat()

        cursor.execute("""
            UPDATE issued_books
            SET return_date = ?, status = 'Returned'
            WHERE issue_id = ?
        """, (return_date, issue_id))

        cursor.execute("""
            UPDATE books
            SET available_copies = available_copies + 1
            WHERE book_id = ?
        """, (test_book_id,))

        conn.commit()

        cursor.execute("""
            SELECT available_copies
            FROM books
            WHERE book_id = ?
        """, (test_book_id,))

        available = cursor.fetchone()["available_copies"]

        assert available == 3
        print("Test 10 passed: Book returned and copies restored.")

        # 11. Check returned status
        cursor.execute("""
            SELECT status, return_date
            FROM issued_books
            WHERE issue_id = ?
        """, (issue_id,))

        record = cursor.fetchone()

        assert record["status"] == "Returned"
        assert record["return_date"] == return_date

        print("Test 11 passed: Return details verified.")

    finally:
        # Close the database connection
        conn.close()

    print("\nAll 11 tests passed successfully!")


if __name__ == "__main__":
    run_tests()
