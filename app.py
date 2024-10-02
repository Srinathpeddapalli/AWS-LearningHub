from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import pymysql
import bcrypt
import logging
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Change this to a more secure key for production

# Configure logging
logging.basicConfig(level=logging.INFO)  # Log INFO and above levels


# Database configuration
db_config = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),  # Change this to your actual DB password
    'database': os.getenv('DB_NAME')
}

# Function to get a database connection
def get_db_connection():
    try:
        connection = pymysql.connect(**db_config)
        print("Connected to the database")
        return connection
    except pymysql.MySQLError as e:
        print(f"Database connection failed: {e}")
        return None

# Home route
@app.route('/')
def index():
    return render_template('index.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['loginEmail']
        password = request.form['loginPassword'].encode('utf-8')

        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            try:
                cursor.execute("SELECT id, password FROM users WHERE email = %s", (email,))
                result = cursor.fetchone()

                if result and bcrypt.checkpw(password, result[1].encode('utf-8')):
                    session['user_id'] = result[0]  # Store user ID in session
                    flash('Login successful!', 'success')
                    return redirect(url_for('courses_cart'))  # Redirect to cart page
                else:
                    flash('Invalid credentials. Please try again.', 'error')
            finally:
                cursor.close()
                connection.close()
        else:
            flash('Could not connect to the database.', 'error')

    return render_template('user_details.html')

# Signup route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['signupName']
        mobile = request.form['signupNumber']
        email = request.form['signupEmail']
        password = request.form['signupPassword'].encode('utf-8')
        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())

        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            try:
                cursor.execute("INSERT INTO users (name, mobile, email, password) VALUES (%s, %s, %s, %s)",
                               (name, mobile, email, hashed_password))
                connection.commit()
                flash('Account created successfully!', 'success')
                return render_template('user_details.html')
            except pymysql.MySQLError as e:
                flash('Error creating account. Email may already exist.', 'error')
                print(f"Error: {e}")
            finally:
                cursor.close()
                connection.close()
        else:
            flash('Could not connect to the database.', 'error')

    return render_template('user_details.html')

# Logout route
@app.route('/logout')
def logout():
    session.clear()  # Clear session data
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))  # Redirect to the login page

# About page
@app.route('/about')
def about():
    return render_template('about.html')

# Courses page
@app.route('/courses', methods=['GET'])
def courses():
    connection = get_db_connection()
    courses = []

    if connection:
        cursor = connection.cursor()
        try:
            # Fetch courses from the database
            cursor.execute("SELECT id, name, category, price, description FROM courses")
            courses = cursor.fetchall()  # Fetch all courses as a list of tuples
            print("called courses", courses)
        except pymysql.MySQLError as e:
            flash('Error fetching courses from the database.', 'error')
            print(f"Error: {e}")
        finally:
            cursor.close()
            connection.close()
    else:
        flash('Could not connect to the database.', 'error')

    # Pass the courses to the template
    return render_template('courses.html', courses=courses)

# Contact page
@app.route('/contact')
def contact():
    return render_template('contact.html')

# User details page
@app.route('/user_details')
def user_details():
    return render_template('user_details.html')


@app.route('/courses_cart', methods=['GET'])
def courses_cart():
    connection = get_db_connection()
    courses = []

    if connection:
        cursor = connection.cursor()
        try:
            # Fetch courses from the database
            cursor.execute("SELECT id, name, category, price, description FROM courses")
            courses = cursor.fetchall()  # Fetch all courses as a list of tuples
        except pymysql.MySQLError as e:
            flash('Error fetching courses from the database.', 'error')
            print(f"Error: {e}")
        finally:
            cursor.close()
            connection.close()
    else:
        flash('Could not connect to the database.', 'error')

    # Pass the courses to the template
    return render_template('courses_cart.html', courses=courses)


# Thank you page
@app.route('/cart')
def cart():
    return render_template('cart.html')

@app.route('/checkout', methods=['POST'])
def checkout():
    logging.info("Checkout route has been called.")  # Log when the route is accessed

    user_id = session.get('user_id')
    if not user_id:
        logging.warning("Checkout attempted without a logged-in user.")
        return jsonify({'success': False, 'message': 'User not logged in.'}), 401

    course_ids = request.json.get('course_ids')
    if not course_ids:
        logging.warning("No course IDs provided in the request.")
        return jsonify({'success': False, 'message': 'Course IDs are required.'}), 400

    logging.info(f"Course IDs received: {course_ids}")

    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        try:
            for course_id in course_ids:
                cursor.execute("INSERT INTO cart (user_id, course_id) VALUES (%s, %s)", (user_id, course_id))
            connection.commit()
            logging.info(f"Successfully added courses {course_ids} to the cart for user ID {user_id}.")
            return jsonify({'success': True, 'message': 'Congratulations! Your payment was successful, and you have successfully purchased the course!'})
        except pymysql.MySQLError as e:
            logging.error(f"Database error occurred: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500
        finally:
            cursor.close()
            connection.close()
    else:
        logging.error("Database connection failed.")
        return jsonify({'success': False, 'message': 'Could not connect to the database.'}), 500


# Assuming you've already set up your Flask app and imported necessary modules

@app.route('/orders')
def orders():
    user_id = session.get('user_id')

    if user_id is None:
        return redirect(url_for('login'))  # Redirect to login if user is not authenticated

    # Establish database connection
    connection = get_db_connection()
    
    if connection:
        cursor = connection.cursor()

        # SQL query to get order details for the specific user
        cursor.execute(
            '''
            SELECT 
                cart.id AS cart_id,
                users.id AS user_id,
                courses.name AS course_name,
                courses.category AS course_category,
                courses.price AS course_price
            FROM cart
            JOIN users ON cart.user_id = users.id
            JOIN courses ON cart.course_id = courses.id
            WHERE users.id = %s
            ''',
            (user_id,)
        )

        # Fetch all results from the executed query
        purchases = cursor.fetchall()

        # Close the cursor and connection
        cursor.close()
        connection.close()

        # Process the fetched data
        courses = [
            {
                'cart_id': purchase[0],
                'user_id': purchase[1],
                'course_name': purchase[2],
                'course_category': purchase[3],
                'course_price': purchase[4]
            } 
            for purchase in purchases
        ]

        return render_template('orders.html', courses=courses)

    return render_template('orders.html', courses=[])  # Return an empty list if connection fails


# Thank you page
@app.route('/thanks')
def thanks():
    return render_template('thanks.html')

# Main function to run the app
if __name__ == '__main__':
    app.run(debug=True)
