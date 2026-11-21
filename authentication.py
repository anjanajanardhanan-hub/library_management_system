import hashlib
import secrets
import hmac
import re
import getpass
import sys
from datetime import date
from database import get_connection


# Password hashing
def hash_password(password):
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256((salt + password).encode()).hexdigest()
    return salt + "$" + hashed


def verify_password(password, stored_hash):
    try:
        salt, old_hash = stored_hash.split("$", 1)
        new_hash = hashlib.sha256((salt + password).encode()).hexdigest()
        return hmac.compare_digest(new_hash, old_hash)
    except:
        return False


# Get password from user
def get_password_input(prompt="Enter Password: "):
    if sys.stdin.isatty():
        try:
            return getpass.getpass(prompt).strip()
        except:
            pass

    return input(prompt).strip()


# Username validation
def is_valid_username(username):
    if len(username) < 3:
        return False, "Username must have at least 3 characters."

    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        return False, "Use only letters, numbers and underscores."

    return True, ""


# Email validation
def is_valid_email(email):
    pattern = r"^[\w.-]+@[\w.-]+\.[a-zA-Z]{2,}$"

    if re.match(pattern, email):
        return True, ""

    return False, "Invalid email address."


# Phone validation
def is_valid_phone(phone):
    phone = phone.replace(" ", "").replace("-", "")

    if re.match(r"^\+?[0-9]{10,15}$", phone):
        return True, ""

    return False, "Enter a valid phone number."


# Password validation
def is_valid_password(password):
    if len(password) < 6:
        return False, "Password must contain at least 6 characters."

    return True, ""


# Admin login
def admin_login():
    print("\n========== ADMIN LOGIN ==========")

    username = input("Enter Admin Username: ").strip()
    password = get_password_input("Enter Admin Password: ")

    if not username or not password:
        print("Username and password are required.")
        return None

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT user_id, username, password, role FROM users WHERE username = ? AND role = ?",
            (username, "admin")
        )

        user = cursor.fetchone()

        if user and verify_password(password, user["password"]):
            print("Admin login successful!")

            return {
                "user_id": user["user_id"],
                "username": user["username"],
                "role": user["role"]
            }

        else:
            print("Invalid username or password.")
            return None

    except Exception as e:
        print("Login error:", e)
        return None

    finally:
        conn.close()


# Member login
def member_login():
    print("\n========== MEMBER LOGIN ==========")

    username = input("Enter Member Username: ").strip()
    password = get_password_input("Enter Member Password: ")

    if not username or not password:
        print("Username and password are required.")
        return None

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT u.user_id, u.username, u.password, u.role,
                   m.member_id, m.full_name, m.email, m.phone
            FROM users u
            JOIN members m ON u.user_id = m.user_id
            WHERE u.username = ? AND u.role = ?
        """, (username, "member"))

        user = cursor.fetchone()

        if user and verify_password(password, user["password"]):
            print("Member login successful!")

            return {
                "user_id": user["user_id"],
                "username": user["username"],
                "role": user["role"],
                "member_id": user["member_id"],
                "full_name": user["full_name"],
                "email": user["email"],
                "phone": user["phone"]
            }

        else:
            print("Invalid username or password.")
            return None

    except Exception as e:
        print("Login error:", e)
        return None

    finally:
        conn.close()


# Register new member
def register_member_account(is_admin_creating=False):

    print("\n========== REGISTER NEW MEMBER ==========")

    full_name = input("Enter Full Name: ").strip()

    if len(full_name) < 2:
        print("Please enter a valid name.")
        return False

    username = input("Enter Desired Username: ").strip()

    valid, message = is_valid_username(username)

    if not valid:
        print(message)
        return False

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT user_id FROM users WHERE username = ?",
            (username,)
        )

        if cursor.fetchone():
            print("Username already exists.")
            return False

    except Exception as e:
        print("Database error:", e)
        return False

    finally:
        conn.close()

    password = get_password_input("Enter Password (minimum 6 characters): ")

    valid, message = is_valid_password(password)

    if not valid:
        print(message)
        return False

    confirm_password = get_password_input("Confirm Password: ")

    if password != confirm_password:
        print("Passwords do not match.")
        return False

    email = input("Enter Email Address: ").strip()

    valid, message = is_valid_email(email)

    if not valid:
        print(message)
        return False

    phone = input("Enter Phone Number: ").strip()

    valid, message = is_valid_phone(phone)

    if not valid:
        print(message)
        return False

    conn = get_connection()
    cursor = conn.cursor()

    try:
        hashed_password = hash_password(password)
        today = date.today().strftime("%Y-%m-%d")

        cursor.execute("""
            INSERT INTO users (username, password, role)
            VALUES (?, ?, ?)
        """, (username, hashed_password, "member"))

        user_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO members (user_id, full_name, email, phone, join_date)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, full_name, email, phone, today))

        member_id = cursor.lastrowid

        conn.commit()

        print("\nMember registered successfully!")
        print("Member ID:", member_id)
        print("Full Name:", full_name)
        print("Username:", username)
        print("Join Date:", today)

        return True

    except Exception as e:
        conn.rollback()
        print("Registration error:", e)
        return False

    finally:
        conn.close()
