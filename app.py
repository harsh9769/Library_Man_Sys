from flask import Flask, redirect, render_template, request, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.db"
app.config["SECRET_KEY"] = "harsh"  # Required for session management and flashing messages

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(500), nullable=False)

class Data(db.Model):
    Sn = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(500), nullable=False)
    Contact = db.Column(db.Integer, nullable=False)
    Date = db.Column(db.Date, default=datetime.utcnow)
    Book_Name = db.Column(db.String(500), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Foreign key to User table
    user = db.relationship('User', backref=db.backref('issued_books', lazy=True))  # Relationship

    def __repr__(self):
        return f"<Books {self.Book_Name}>"

class Books(db.Model):
    Book_Sn = db.Column(db.Integer, primary_key=True)
    Book_Name = db.Column(db.String(500), nullable=False)

    def __repr__(self):
        return f"<Books {self.Book_Name}>"

@app.route("/")
def main():
    return render_template("home.html")

@app.route("/user/login", methods=["POST", "GET"])
def user_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Check if the username exists
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            flash("Login successful!", "success")
            return redirect(url_for("dash"))
        else:
            flash("Invalid username or password.", "danger")

    return render_template("user_login.html")

@app.route("/user/register", methods=["POST", "GET"])
def user_register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Check if username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already exists.", "danger")
            return redirect(url_for("user_register"))

        # Hash the password
        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")

        # Save the new user in the database
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash("User registered successfully!", "success")
        return redirect(url_for("user_login"))

    return render_template("user_register.html")

@app.route("/user/dashboard", methods=["POST", "GET"])
def dash():
    if "user_id" not in session:
        flash("Please log in to access this page.", "danger")
        return redirect(url_for("user_login"))

    all_books = Books.query.all()  # Available books
    issued_books = Data.query.filter_by(user_id=session["user_id"]).all()  # Books issued to the logged-in user
    return render_template("index.html", all_books=all_books, issued_books=issued_books)

@app.route("/user/submit", methods=["POST", "GET"])
def submit_form():
    if "user_id" not in session:
        flash("Please log in to access this page.", "danger")
        return redirect(url_for("dash"))

    if request.method == "POST":
        book_name = request.form.get("SelectedBook")
        name = request.form.get("Name")
        contact = request.form.get("Contact_No")
        action = request.form.get("action")

        if action == "submit":  # Issue Book
            if not book_name:
                flash("Please select a book.", "error")
                return redirect(url_for("dash"))

            if not name or not contact:
                flash("Name and Contact Number are required.", "error")
                return redirect(url_for("dash"))

            # Add the data to the Data table, associating the issued book with the logged-in user
            new_data = Data(Name=name, Contact=contact, Book_Name=book_name, user_id=session["user_id"])  # Use user_id from session
            db.session.add(new_data)
            db.session.commit()

            # Remove the book from the Books table
            book_to_delete = db.session.query(Books).filter_by(Book_Name=book_name).first()
            if book_to_delete:
                db.session.delete(book_to_delete)
                db.session.commit()

            flash("Book issued successfully.", "success")
            return redirect(url_for("dash"))

        elif action == "return":  # Return Book
            if not book_name:
                flash("Please select a book.", "error")
                return redirect(url_for("dash"))

            # Find the book entry in the Data table for the logged-in user
            data_entry = db.session.query(Data).filter_by(Book_Name=book_name, user_id=session["user_id"]).first()
            if data_entry:
                # Add the book back to the Books table
                returned_book = Books(Book_Name=book_name)
                db.session.add(returned_book)

                # Remove the entry from the Data table
                db.session.delete(data_entry)
                db.session.commit()

                flash("Book returned successfully.", "success")
            else:
                flash("This book is not found in the issued data.", "error")

            return redirect(url_for("dash"))

    return render_template("admin_dash.html")

@app.route("/admin/login", methods=["POST", "GET"])
def admin_login():
    if request.method == "POST":
        admin_username = request.form.get("admin_username")
        admin_password = request.form.get("admin_password")

        # Check the admin credentials (example)
        if admin_username == "admin" and admin_password == "admin":
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid admin username or password.", "danger")

    return render_template("admin_login.html")

@app.route("/admin/dashboard")
def admin_dashboard():
    if "admin_logged_in" not in session:
        flash("Admin login required.", "danger")
        return redirect(url_for("admin_login"))

    # Debug print to confirm session is active
    print(f"Admin logged in: {session.get('admin_logged_in')}")

    # Query all books and data from the Data table
    all_books = Books.query.all()
    all_data = Data.query.all()

    # Debug prints to check the queried data
    print(f"All books: {all_books}")
    print(f"All issued data: {all_data}")

    return render_template("admin_dashboard.html", all_books=all_books, all_data=all_data)


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("admin_logged_in", None)
    flash("You have been logged out.", "success")
    return redirect(url_for("main"))

if __name__ == "__main__":
    app.run(debug=True)
