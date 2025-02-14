from flask import Flask, render_template, request, redirect, url_for, jsonify
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

# MySQL Connection
db = mysql.connector.connect(
    host="localhost",
    user="shrina",  # Replace with your MySQL username
    password="shrina",  # Replace with your MySQL password
    database="intelliclaim"
)
cursor = db.cursor()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        
        cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()

        if user:
            return redirect(url_for("home"))
        else:
            return "Invalid credentials"
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        password = request.form["password"]

        try:
            cursor.execute("INSERT INTO users (name, email, phone, password) VALUES (%s, %s, %s, %s)",
                           (name, email, phone, password))
            db.commit()
            return redirect(url_for("login"))
        except Error as e:
            return f"Error: {e}"

    return render_template("signup.html")

def claim():
    if request.method == "POST":
        return "Claim submitted!"
    return render_template("claim.html")

@app.route("/about", methods=["GET", "POST"])
def about():
    return render_template("about.html")

if __name__ == "__main__":
    app.run(debug=True)
