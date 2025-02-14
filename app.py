from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify
from flask_mysqldb import MySQL
import logging
import os

app = Flask(__name__)
app.secret_key = 'secret_key'

logging.basicConfig(level=logging.DEBUG)  # Set logging level to DEBUG
logger = logging.getLogger(__name__)


app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'Sharanya'
app.config['MYSQL_PASSWORD'] = 'ShArAnYa123!@#'
app.config['MYSQL_DB'] = 'intelliclaim'

mysql = MySQL(app)

@app.route("/")
def home():
    if 'user_id' in session:
        return render_template("index.html", user_id=session['user_id'])
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT id, email FROM users WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()
        cursor.close()

        if user:
            session['user_id'] = user[0]  # Storing user ID in session
            flash("Login successful!")
            return redirect(url_for("home", user_id=user[0]))
        else:
            flash("Invalid credentials")
            return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop('user_id', None)
    flash("You have been logged out.")
    return redirect(url_for('login'))

@app.route("/about/<int:user_id>")
def about(user_id):
    if 'user_id' in session and session['user_id'] == user_id:
        return render_template("about.html", user_id=user_id)
    else:
        flash("Unauthorized access!")
        return redirect(url_for('login'))

@app.route('/insurance-form/<int:user_id>')
def insurance_form(user_id):
    # Log the received user_id
    logger.debug(f"Received user_id: {user_id}")

    # Check if the user is logged in and the session user_id matches the route user_id
    if 'user_id' in session and session['user_id'] == user_id:
        # Log the session user_id
        logger.debug(f"Session user_id: {session['user_id']}")

        # Get the package type from the query parameter
        package = request.args.get('package')
        logger.debug(f"Received package: {package}")

        # Render the insurance form template
        return render_template('insurance-form.html', user_id=user_id, package=package)
    else:
        # Log unauthorized access attempts
        logger.warning(f"Unauthorized access attempt: session user_id = {session.get('user_id')}, route user_id = {user_id}")

        # Flash a message and redirect to the login page
        flash("Unauthorized access!")
        return redirect(url_for('login'))



from datetime import datetime  # Import datetime module

from datetime import datetime, timedelta  # Import datetime and timedelta modules
import os  # Import os module for file handling

from datetime import datetime, timedelta  # Import datetime and timedelta modules
import os  # Import os module for file handling

# Insurance form submission route
@app.route('/submit_insurance', methods=['POST'])
def submit_insurance():
    if 'user_id' not in session:
        flash("Unauthorized access!")
        return redirect(url_for('login'))

    # Extract form data
    user_id = session['user_id']
    insurance_type = request.form.get('insurance_type')
    full_name = request.form.get('name')
    email = request.form.get('email')
    phone_number = request.form.get('phone')
    car_make = request.form.get('car_make')
    car_model = request.form.get('car_model')
    car_year = request.form.get('car_year')
    car_registration = request.form.get('car_registration')
    deductible_amount = request.form.get('deductible')

    # Insert data into the database
    try:
        cursor = mysql.connection.cursor()
        query = """
        INSERT INTO insurance_details (
            user_id, insurance_type, full_name, email, phone_number, 
            car_make, car_model, car_year, car_registration, deductible_amount
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            user_id, insurance_type, full_name, email, phone_number,
            car_make, car_model, car_year, car_registration, deductible_amount
        )
        cursor.execute(query, values)
        mysql.connection.commit()
        cursor.close()

        flash("Insurance details submitted successfully!")
        return redirect(url_for('home', user_id=user_id))
    except Exception as e:
        logger.error(f"Error submitting insurance details: {e}")
        flash("An error occurred while submitting the form. Please try again.")
        return redirect(url_for('insurance_form', user_id=user_id))
    
    
if __name__ == "__main__":
    app.run(debug=True)
