import sys
from database import init_db
from authentication import admin_login, member_login, register_member_account
import books
import members
import borrowing


def print_banner(title):
    print("\n" + "=" * 60)
    print(title.center(60))
    print("=" * 60)


def admin_dashboard(admin_session):

    while True:
        print_banner("ADMIN CONTROL PANEL")

        print("1. Add Book")
        print("2. View All Books")
        print("3. Search Book")
        print("4. Update Book")
        print("5. Delete Book")
        print("6. Register Member")
        print("7. View Members")
        print("8. Issue Book")
        print("9. Return Book")
        print("10. View Issued Books")
        print("11. View Overdue Books")
        print("12. View Borrowing History")
        print("13. Logout")

        choice = input("Enter your choice: ")

        try:
            if choice == "1":
                books.add_book()

            elif choice == "2":
                books.view_all_books()

            elif choice == "3":
                books.search_books()

            elif choice == "4":
                books.update_book()

            elif choice == "5":
                books.delete_book()

            elif choice == "6":
                members.register_member()

            elif choice == "7":
                members.view_all_members()

            elif choice == "8":
                borrowing.issue_book()

            elif choice == "9":
                borrowing.return_book()

            elif choice == "10":
                borrowing.view_all_issued_books()

            elif choice == "11":
                borrowing.view_overdue_books()

            elif choice == "12":
                borrowing.view_borrowing_history()

            elif choice == "13":
                print("Admin logged out successfully.")
                break

            else:
                print("Invalid choice. Please try again.")

        except Exception as e:
            print("Error:", e)

        input("Press Enter to continue...")


def member_dashboard(member_session):

    while True:
        print_banner("MEMBER DASHBOARD")

        print("1. View Available Books")
        print("2. Search Books")
        print("3. View My Borrowed Books")
        print("4. View My Borrowing History")
        print("5. Logout")

        choice = input("Enter your choice: ")

        try:
            if choice == "1":
                books.view_available_books()

            elif choice == "2":
                books.search_books()

            elif choice == "3":
                borrowing.view_member_borrowed_books(
                    member_session["member_id"]
                )

            elif choice == "4":
                borrowing.view_member_borrowing_history(
                    member_session["member_id"]
                )

            elif choice == "5":
                print("You have logged out successfully.")
                break

            else:
                print("Invalid choice. Please try again.")

        except Exception as e:
            print("Error:", e)

        input("Press Enter to continue...")


def main_menu():

    while True:
        print_banner("LIBRARY MANAGEMENT SYSTEM")

        print("1. Admin Login")
        print("2. Member Registration")
        print("3. Member Login")
        print("4. Exit")

        choice = input("Enter your choice: ")

        if choice == "1":
            admin = admin_login()

            if admin:
                admin_dashboard(admin)

        elif choice == "2":
            register_member_account(is_admin_creating=False)

        elif choice == "3":
            member = member_login()

            if member:
                member_dashboard(member)

        elif choice == "4":
            print("Thank you for using the Library Management System!")
            sys.exit(0)

        else:
            print("Invalid choice. Please try again.")


def main():

    try:
        init_db()
        main_menu()

    except KeyboardInterrupt:
        print("\nProgram stopped.")
        sys.exit(0)

    except Exception as e:
        print("Something went wrong:", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
