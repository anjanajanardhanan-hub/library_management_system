import sqlite3
from database import get_connection, print_table
from authentication import is_valid_email, is_valid_phone, register_member_account


# 1. Register a new member
def register_member():
    register_member_account(is_admin_creating=True)


# 2. View all registered members
def view_all_members():
    print("\n--- ALL LIBRARY MEMBERS ---")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT m.member_id, m.full_name, u.username,
                   m.email, m.phone, m.join_date,
                   (SELECT COUNT(*)
                    FROM issued_books ib
                    WHERE ib.member_id = m.member_id
                    AND ib.status = 'Issued') AS active_loans
            FROM members m
            JOIN users u ON m.user_id = u.user_id
            ORDER BY m.member_id
        """)

        members = cursor.fetchall()

        headers = [
            "Member ID", "Full Name", "Username",
            "Email", "Phone", "Join Date", "Active Loans"
        ]

        rows = []

        for member in members:
            rows.append([
                member["member_id"],
                member["full_name"],
                member["username"],
                member["email"],
                member["phone"],
                member["join_date"],
                member["active_loans"]
            ])

        print_table(headers, rows)
        print("Total members:", len(members))

    except sqlite3.Error as e:
        print("Database error:", e)

    finally:
        conn.close()


# 3. Update member details
def update_member():
    print("\n--- UPDATE MEMBER DETAILS ---")

    try:
        member_id = int(input("Enter Member ID: "))
    except ValueError:
        print("Please enter a valid Member ID.")
        return

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT m.*, u.username
            FROM members m
            JOIN users u ON m.user_id = u.user_id
            WHERE m.member_id = ?
        """, (member_id,))

        member = cursor.fetchone()

        if not member:
            print("Member not found.")
            return

        print("\nCurrent Name:", member["full_name"])
        print("Current Email:", member["email"])
        print("Current Phone:", member["phone"])

        print("\nLeave a field blank to keep its current value.")

        name = input("Enter new name: ").strip()
        email = input("Enter new email: ").strip()
        phone = input("Enter new phone: ").strip()

        # Keep old details if the user enters nothing
        if not name:
            name = member["full_name"]
        elif len(name) < 2:
            print("Name must contain at least 2 characters.")
            return

        if email:
            valid, message = is_valid_email(email)

            if not valid:
                print(message)
                return
        else:
            email = member["email"]

        if phone:
            valid, message = is_valid_phone(phone)

            if not valid:
                print(message)
                return
        else:
            phone = member["phone"]

        cursor.execute("""
            UPDATE members
            SET full_name = ?, email = ?, phone = ?
            WHERE member_id = ?
        """, (name, email, phone, member_id))

        conn.commit()
        print("Member details updated successfully.")

    except sqlite3.Error as e:
        conn.rollback()
        print("Database error:", e)

    finally:
        conn.close()


# 4. Delete a member
def delete_member():
    print("\n--- DELETE MEMBER ---")

    try:
        member_id = int(input("Enter Member ID: "))
    except ValueError:
        print("Please enter a valid Member ID.")
        return

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT m.user_id, m.full_name, u.username
            FROM members m
            JOIN users u ON m.user_id = u.user_id
            WHERE m.member_id = ?
        """, (member_id,))

        member = cursor.fetchone()

        if not member:
            print("Member not found.")
            return

        # Check for books that have not been returned
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM issued_books
            WHERE member_id = ? AND status = 'Issued'
        """, (member_id,))

        active_loans = cursor.fetchone()["total"]

        if active_loans > 0:
            print("Cannot delete this member.")
            print("The member still has", active_loans, "borrowed book(s).")
            return

        # Check previous borrowing records
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM issued_books
            WHERE member_id = ?
        """, (member_id,))

        history_count = cursor.fetchone()["total"]

        if history_count > 0:
            print("This member has", history_count,
                  "past borrowing record(s).")
            print("These records will also be deleted.")

        confirm = input(
            "Are you sure you want to delete this member? (y/n): "
        ).lower()

        if confirm != "y":
            print("Deletion cancelled.")
            return

        # Delete borrowing history first
        if history_count > 0:
            cursor.execute("""
                DELETE FROM issued_books
                WHERE member_id = ?
            """, (member_id,))

        # Delete the user account
        cursor.execute("""
            DELETE FROM users
            WHERE user_id = ?
        """, (member["user_id"],))

        conn.commit()

        print("Member deleted successfully.")

    except sqlite3.Error as e:
        conn.rollback()
        print("Database error:", e)

    finally:
        conn.close()
