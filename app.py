from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify
from flask_mysqldb import MySQL
import logging
import os
import re
from werkzeug.utils import secure_filename
import MySQLdb.cursors
import uuid
import google.generativeai as genai
from dotenv import load_dotenv


app = Flask(__name__)
app.secret_key = 'secret_key'

logging.basicConfig(level=logging.DEBUG)  # Set logging level to DEBUG
logger = logging.getLogger(__name__)


app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'Sharanya'
app.config['MYSQL_PASSWORD'] = 'ShArAnYa123!@#'
app.config['MYSQL_DB'] = 'intelliclaim'

mysql = MySQL(app)

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Initialize chatbot model
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

# Define AI assistant instructions (without encoding conversion)
clean_instruction = """
You are an AI assistant for IntelliClaim, an AI-powered car damage assessment and insurance claims system.
You help users with:
- Car damage assessment: Guide users on uploading images, describing damages, and getting AI-based repair cost estimates.
- Insurance claim process: Explain steps to file a claim, required documents, and expected processing time.
- Policy information: Answer questions about car insurance policies, coverage options, and terms.
- Damage severity estimation: Provide insights on minor, moderate, and severe damages based on AI predictions.
- Customer support: Assist with FAQs, troubleshooting, and directing users to human agents if needed.

Guidelines:
- Be clear, professional, and concise in responses.
- Provide step-by-step guidance for processes.
- Redirect users to official support if unsure.
- Do not make final claim decisions or request sensitive personal data.
"""

# Initialize AI model
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash-8b",
    generation_config=generation_config,
    system_instruction=clean_instruction  # Use plain string
)


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

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        # Basic validation
        if not name or not email or not phone or not password or not confirm_password:
            flash("All fields are required!", "error")
            return redirect(url_for("signup"))

        if password != confirm_password:
            flash("Passwords do not match!", "error")
            return redirect(url_for("signup"))

        # Validate email format
        if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email):
            flash("Invalid email format!", "error")
            return redirect(url_for("signup"))

        # Validate phone number format (10 digits)
        if not re.match(r"^\d{10}$", phone):
            flash("Phone number must be 10 digits!", "error")
            return redirect(url_for("signup"))

        # Check if the email already exists in the database
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT email FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash("Email already registered. Please use a different email.", "error")
            cursor.close()
            return redirect(url_for("signup"))

        # Insert the new user into the database
        try:
            cursor.execute(
                "INSERT INTO users (name, email, phone, password) VALUES (%s, %s, %s, %s)",
                (name, email, phone, password)
            )
            mysql.connection.commit()
            flash("Signup successful! Please log in.", "success")
            cursor.close()
            return redirect(url_for("login"))
        except Exception as e:
            mysql.connection.rollback()
            flash("An error occurred during signup. Please try again.", "error")
            cursor.close()
            return redirect(url_for("signup"))

    return render_template("signup.html")

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

@app.route("/claim_step1/<int:user_id>")
def claim_step1(user_id):
    # Check if the user is logged in
    if 'user_id' not in session or session['user_id'] != user_id:
        flash("Unauthorized access!")
        return redirect(url_for('login'))

    try:
        # Fetch cars associated with the user
        cursor = mysql.connection.cursor()
        query = """
        SELECT id, car_registration, car_make, insurance_type 
        FROM insurance_details 
        WHERE user_id = %s
        """
        cursor.execute(query, (user_id,))
        cars = cursor.fetchall()  # Fetch all rows
        cursor.close()

        # Log the fetched cars for debugging
        logger.debug(f"Fetched cars for user_id {user_id}: {cars}")

        # Render the template with the cars data
        return render_template("claim_step1.html", user_id=user_id, cars=cars)
    except Exception as e:
        logger.error(f"Error fetching cars for user_id {user_id}: {e}")
        flash("An error occurred while fetching your cars. Please try again.")
        return redirect(url_for('home', user_id=user_id))
    
@app.route("/claim_step2/<int:car_id>")
def claim_step2(car_id):
    # Check if the user is logged in
    if 'user_id' not in session:
        flash("Unauthorized access!")
        return redirect(url_for('login'))

    user_id = session['user_id']

    try:
        # Fetch the specific car details using car_id and user_id
        cursor = mysql.connection.cursor()
        query = """
        SELECT id, car_registration, car_make, car_model, car_year, insurance_type, deductible_amount 
        FROM insurance_details 
        WHERE id = %s AND user_id = %s
        """
        cursor.execute(query, (car_id, user_id))
        car = cursor.fetchone()  # Fetch a single row
        cursor.close()

        # Log the fetched car for debugging
        logger.debug(f"Fetched car for car_id {car_id} and user_id {user_id}: {car}")

        if car:
            # Render the template with the car details
            return render_template("claim_step2.html", user_id=user_id, car=car)
        else:
            flash("Car not found or unauthorized access!")
            return redirect(url_for('claim_step1', user_id=user_id))
    except Exception as e:
        logger.error(f"Error fetching car details for car_id {car_id}: {e}")
        flash("An error occurred while fetching car details. Please try again.")
        return redirect(url_for('claim_step1', user_id=user_id))


@app.route("/submit_claim", methods=["POST"])
def submit_claim():
    if 'user_id' not in session:
        flash("Unauthorized access!")
        return redirect(url_for('login'))

    user_id = session['user_id']
    car_id = request.form.get("car_id")  # Get car_id from the form
    damage_description = request.form.get("damage_description")
    damage_cause = request.form.get("damage_cause")
    damaged_parts = request.form.getlist("damaged_parts")  # Get list of damaged parts
    damage_images = request.files.getlist("damage_images")

    try:
        # Generate a unique claim_id (folder name)
        claim_id = str(uuid.uuid4())

        # Create a folder for the claim images
        claim_folder = os.path.join("uploads", claim_id)
        os.makedirs(claim_folder, exist_ok=True)

        # Save the uploaded images
        for image in damage_images:
            if image.filename != "":
                filename = secure_filename(image.filename)
                image.save(os.path.join(claim_folder, filename))

        # Insert claim details into the database
        cursor = mysql.connection.cursor()
        query = """
        INSERT INTO claims (car_id, user_id, damage_description, damage_cause, damaged_parts)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (car_id, user_id, damage_description, damage_cause, json.dumps(damaged_parts)))
        mysql.connection.commit()
        cursor.close()

        flash("Claim submitted successfully!")
        return redirect(url_for('claim_step3', user_id=user_id))
    except Exception as e:
        logger.error(f"Error submitting claim: {e}")
        flash("An error occurred while submitting your claim. Please try again.")
        return redirect(url_for('claim_step2', car_id=car_id))  # Pass car_id here
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


@app.route("/claim_step3")
def claim_step3():
    if 'user_id' not in session:
        flash("Unauthorized access!")
        return redirect(url_for('login'))

    return render_template("claim_step3.html")

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
    
@app.route("/chat", methods=["POST"])
def chat():
    """Handles incoming chat messages from the frontend and returns AI-generated responses."""
    data = request.json
    user_message = data.get("message", "")

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    chat_session = model.start_chat(history=[])
    response = chat_session.send_message(user_message)
    return jsonify({"response": response.text})
    
    
if __name__ == "__main__":
    app.run(debug=True)
