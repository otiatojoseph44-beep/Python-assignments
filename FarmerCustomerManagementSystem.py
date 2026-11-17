import sqlite3
import os

# ==========================================
# 1. DATABASE LOGIC (Keep this for Tkinter)
# ==========================================
class Database:
    def __init__(self, db_name="farm_market.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # Users table: stores farmers and buyers
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('farmer', 'buyer')),
                phone TEXT NOT NULL
            )
        ''')
        # Products table: stores the items for sale
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                farmer_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price REAL NOT NULL,
                description TEXT,
                quantity INTEGER NOT NULL,
                location TEXT NOT NULL,
                is_available INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (farmer_id) REFERENCES users (id)
            )
        ''')
        self.conn.commit()

    # --- User Methods ---
    def register_user(self, username, password, role, phone):
        try:
            self.cursor.execute(
                "INSERT INTO users (username, password, role, phone) VALUES (?, ?, ?, ?)",
                (username, password, role, phone)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False # Username already exists

    def login_user(self, username, password):
        self.cursor.execute(
            "SELECT id, username, role, phone FROM users WHERE username=? AND password=?",
            (username, password)
        )
        return self.cursor.fetchone()

    # --- Product Methods ---
    def add_product(self, farmer_id, name, category, price, description, quantity, location):
        self.cursor.execute('''
            INSERT INTO products (farmer_id, name, category, price, description, quantity, location)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (farmer_id, name, category, price, description, quantity, location))
        self.conn.commit()

    def get_all_products(self, filter_location=None, filter_category=None, search_term=None):
        query = "SELECT p.id, p.name, p.category, p.price, p.quantity, p.location, p.description, u.username, u.phone " \
                "FROM products p JOIN users u ON p.farmer_id = u.id WHERE p.is_available = 1"
        params = []

        if filter_location:
            query += " AND p.location LIKE ?"
            params.append(f"%{filter_location}%")
        if filter_category:
            query += " AND p.category LIKE ?"
            params.append(f"%{filter_category}%")
        if search_term:
            query += " AND (p.name LIKE ? OR p.description LIKE ?)"
            params.extend([f"%{search_term}%", f"%{search_term}%"])

        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def get_farmer_products(self, farmer_id):
        self.cursor.execute(
            "SELECT id, name, category, price, quantity, location, is_available FROM products WHERE farmer_id=?",
            (farmer_id,)
        )
        return self.cursor.fetchall()

    def update_product_status(self, product_id, is_available):
        self.cursor.execute(
            "UPDATE products SET is_available=? WHERE id=?",
            (is_available, product_id)
        )
        self.conn.commit()


# ==========================================
# 2. CONSOLE UI (Replace this with Tkinter later)
# ==========================================
class ConsoleApp:
    def __init__(self):
        self.db = Database()
        self.current_user = None # Will hold (id, username, role, phone)

    def run(self):
        print("\n" + "="*40)
        print("  WELCOME TO KENYA FARM MARKETPLACE")
        print("="*40)
        
        while True:
            if not self.current_user:
                self.show_auth_menu()
            else:
                if self.current_user[2] == 'farmer':
                    self.show_farmer_menu()
                else:
                    self.show_buyer_menu()

    # --- Input Validation Helpers ---
    def get_valid_text(self, prompt, allow_empty=False):
        while True:
            val = input(prompt).strip()
            if val or allow_empty:
                return val
            print("Hint: This field cannot be empty. Please try again.")

    def get_valid_number(self, prompt, num_type=float, min_val=0):
        while True:
            val = input(prompt).strip()
            try:
                num = num_type(val)
                if num >= min_val:
                    return num
                print(f"Hint: Please enter a number greater than or equal to {min_val}.")
            except ValueError:
                print(f"Hint: Invalid input. Please enter a valid {'decimal' if num_type==float else 'whole'} number.")

    def get_valid_choice(self, prompt, choices):
        while True:
            val = input(prompt).strip()
            if val in choices:
                return val
            print(f"Hint: Invalid choice. Please select from {choices}.")

    # --- Authentication Menus ---
    def show_auth_menu(self):
        print("\n--- MAIN MENU ---")
        print("1. Login")
        print("2. Register")
        print("3. Exit")
        choice = self.get_valid_choice("Select option (1-3): ", ['1', '2', '3'])

        if choice == '1':
            self.login()
        elif choice == '2':
            self.register()
        elif choice == '3':
            print("Goodbye! Asante sana!")
            exit()

    def register(self):
        print("\n--- REGISTER ---")
        username = self.get_valid_text("Choose a username: ")
        password = self.get_valid_text("Choose a password: ")
        role = self.get_valid_choice("Are you a (f)armer or (b)uyer? (f/b): ", ['f', 'b'])
        role = 'farmer' if role == 'f' else 'buyer'
        
        print("Hint: Enter a valid Kenyan phone number (e.g., 0712345678) for contact.")
        phone = self.get_valid_text("Phone number: ")

        if self.db.register_user(username, password, role, phone):
            print("Registration successful! Please login.")
        else:
            print("Error: Username already exists. Please try another.")

    def login(self):
        print("\n--- LOGIN ---")
        username = self.get_valid_text("Username: ")
        password = self.get_valid_text("Password: ")
        
        user = self.db.login_user(username, password)
        if user:
            self.current_user = user
            print(f"Welcome back, {user[1]}! (Role: {user[2]})")
        else:
            print("Error: Invalid username or password.")

    # --- Farmer Menu ---
    def show_farmer_menu(self):
        print("\n--- FARMER DASHBOARD ---")
        print("1. Add New Product")
        print("2. View My Products")
        print("3. Update Product Availability")
        print("4. Logout")
        choice = self.get_valid_choice("Select option (1-4): ", ['1', '2', '3', '4'])

        if choice == '1':
            self.add_product()
        elif choice == '2':
            self.view_my_products()
        elif choice == '3':
            self.update_product_status()
        elif choice == '4':
            self.current_user = None

    def add_product(self):
        print("\n--- ADD PRODUCT ---")
        print("Hint: Common categories in Kenya: Maize, Tomatoes, Dairy, Poultry, Avocados, Sukuma Wiki, etc.")
        name = self.get_valid_text("Product name: ")
        category = self.get_valid_text("Category: ")
        
        print("Hint: Price should be in KES (Kenya Shillings).")
        price = self.get_valid_number("Price per unit (KES): ", float, 1.0)
        
        description = self.get_valid_text("Description (optional): ", allow_empty=True)
        
        print("Hint: Enter quantity in standard units (e.g., kg, liters, pieces).")
        quantity = self.get_valid_number("Quantity available: ", int, 1)
        
        print("Hint: Enter your County or Town (e.g., Nairobi, Kiambu, Nakuru, Eldoret, Mombasa).")
        location = self.get_valid_text("Location: ")

        self.db.add_product(self.current_user[0], name, category, price, description, quantity, location)
        print("Product added successfully!")

    def view_my_products(self):
        products = self.db.get_farmer_products(self.current_user[0])
        print("\n--- MY PRODUCTS ---")
        if not products:
            print("You haven't added any products yet.")
            return
        
        print(f"{'ID':<5} | {'Name':<15} | {'Category':<12} | {'Price':<8} | {'Qty':<5} | {'Status':<10}")
        print("-" * 65)
        for p in products:
            status = "Available" if p[6] == 1 else "Sold/Unavailable"
            print(f"{p[0]:<5} | {p[1]:<15} | {p[2]:<12} | {p[3]:<8.2f} | {p[4]:<5} | {status:<10}")

    def update_product_status(self):
        self.view_my_products()
        products = self.db.get_farmer_products(self.current_user[0])
        if not products: return

        print("\nUpdate Availability:")
        prod_id = self.get_valid_number("Enter Product ID to update: ", int, 1)
        
        # Check if product belongs to this farmer
        valid_ids = [p[0] for p in products]
        if prod_id not in valid_ids:
            print("Error: Invalid Product ID.")
            return

        status = self.get_valid_choice("Is it (1) Available or (2) Sold/Unavailable? (1/2): ", ['1', '2'])
        is_available = 1 if status == '1' else 0
        self.db.update_product_status(prod_id, is_available)
        print("Product status updated!")

    # --- Buyer Menu ---
    def show_buyer_menu(self):
        print("\n--- BUYER DASHBOARD ---")
        print("1. View All Available Products")
        print("2. Search / Filter Products")
        print("3. Logout")
        choice = self.get_valid_choice("Select option (1-3): ", ['1', '2', '3'])

        if choice == '1':
            self.view_products()
        elif choice == '2':
            self.search_products()
        elif choice == '3':
            self.current_user = None

    def display_products(self, products):
        if not products:
            print("No products found matching your criteria.")
            return

        print(f"\n{'ID':<4} | {'Product':<12} | {'Category':<10} | {'Price':<8} | {'Qty':<5} | {'Location':<10} | {'Farmer':<10} | {'Phone':<12}")
        print("-" * 95)
        for p in products:
            # p: id, name, category, price, quantity, location, description, username, phone
            print(f"{p[0]:<4} | {p[1]:<12} | {p[2]:<10} | {p[3]:<8.2f} | {p[4]:<5} | {p[5]:<10} | {p[7]:<10} | {p[8]:<12}")
        print("\nHint: To make a deal, note the Farmer's name and call their Phone number directly!")

    def view_products(self):
        products = self.db.get_all_products()
        print("\n--- ALL AVAILABLE PRODUCTS ---")
        self.display_products(products)

    def search_products(self):
        print("\n--- SEARCH & FILTER ---")
        print("Hint: Leave blank and press Enter to skip a filter.")
        search_term = self.get_valid_text("Search by name or description: ", allow_empty=True)
        location = self.get_valid_text("Filter by Location (e.g., Nairobi): ", allow_empty=True)
        category = self.get_valid_text("Filter by Category (e.g., Maize): ", allow_empty=True)

        products = self.db.get_all_products(
            filter_location=location if location else None,
            filter_category=category if category else None,
            search_term=search_term if search_term else None
        )
        print("\n--- SEARCH RESULTS ---")
        self.display_products(products)


# ==========================================
# 3. RUN THE APP
# ==========================================
if __name__ == "__main__":
    # Clear screen (works on Windows and Mac/Linux)
    os.system('cls' if os.name == 'nt' else 'clear')
    app = ConsoleApp()
    app.run()