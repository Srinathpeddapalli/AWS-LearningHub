from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import pymysql
import bcrypt
import logging

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Configure logging
logging.basicConfig(level=logging.INFO)

db_config = {
    'host': 'learnhub-8198.c5ukqgu4mk81.ap-south-1.rds.amazonaws.com',    
    'user': 'admin',
    'password': 'tanirstanir',
    'database': 'learnhub'
}

# Function to get a database connection
def get_db_connection():
    try:
        connection = pymysql.connect(**db_config)
        logging.info("Connected to the database")
        return connection
    except pymysql.MySQLError as e:
        logging.error(f"Database connection failed: {e}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

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
                    print(result[0])
                    return redirect(url_for('courses_cart', user_id=result[0]))
                
                else:
                    flash('Invalid credentials. Please try again.', 'error')
            finally:
                cursor.close()
                connection.close()

    return render_template('user_details.html')

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
                return redirect(url_for('login'))  # Redirect to login after signup
            except pymysql.MySQLError as e:
                flash('Error creating account. Email may already exist.', 'error')
                logging.error(f"Error: {e}")
            finally:
                cursor.close()
                connection.close()

    return render_template('user_details.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/courses')
def courses():
    return render_template('courses.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/user_details')
def user_details():
    return render_template('user_details.html')

@app.route('/cart')
def cart():
    return render_template('cart.html')

@app.route('/thanks')
def thanks():
    return render_template('thanks.html')

@app.route('/courses_cart', methods=['GET', 'POST'])
def courses_cart():
    if request.method == 'POST':
        user_id = session.get('user_id')

        if not user_id:
            flash('Please log in to add courses to the cart.', 'error')
            return redirect(url_for('login'))  # Redirect to login if no user session

        course_ids = request.form.getlist('course_ids')  # Get list of selected course IDs
        logging.info(f"Course IDs received: {course_ids}")

        if not course_ids:
            flash('No courses selected', 'error')
            return redirect(url_for('courses'))  # Redirect back to courses page if no courses selected

        connection = get_db_connection()  # Get database connection
        if connection:
            cursor = connection.cursor()
            try:
                for course_id in course_ids:  # Fixed: changed course_id to course_ids
                    # Check if the course is already in the cart for the user
                    cursor.execute("SELECT COUNT(*) FROM cart WHERE user_id = %s AND course_id = %s", (user_id, course_id))
                    count = cursor.fetchone()[0]

                    if count == 0:  # Only add if not already in the cart
                        cursor.execute("INSERT INTO cart (user_id, course_id) VALUES (%s, %s)", (user_id, course_id))
                        logging.info(f"Added course ID {course_id} to cart for user ID {user_id}")

                connection.commit()  
                flash('Courses added to cart!', 'success')
                return redirect(url_for('cart'))  
            except pymysql.MySQLError as e:
                logging.error(f"Database error: {e}")
                flash('Error adding courses to cart.', 'error')
            finally:
                cursor.close()
                connection.close()  
        else:
            flash('Database connection failed.', 'error')
            return redirect(url_for('courses'))
    
    # If it's a GET request, render the course cart page
    return render_template('courses_cart.html')  # Adjust this as per your requirement



# @app.route('/cart')
# def cart():
#     user_id = session.get('user_id')

#     if not user_id:
#         flash('Please log in to view your cart.', 'error')
#         return redirect(url_for('login'))  # Redirect to login if no user session

#     connection = get_db_connection()
#     if connection:
#         cursor = connection.cursor()
#         try:
#             cursor.execute("""
#                 SELECT courses.name 
#                 FROM cart 
#                 JOIN courses ON cart.course_id = courses.id 
#                 WHERE cart.user_id = %s
#             """, (user_id,))
#             courses = [course[0] for course in cursor.fetchall()]

#             return render_template('cart.html', courses=courses)
#         except Exception as e:
#             flash('Error fetching cart items. Please try again.', 'error')
#             logging.error(f"Error: {e}")
#             return redirect(url_for('index'))
#         finally:
#             cursor.close()
#             connection.close()
#     return render_template('cart.html', courses=[])  # Return an empty cart if no connection


# @app.route('/thanks', methods=['POST'])
# def thanks():
#     card_number = request.form['cardNumber']
#     expiry_date = request.form['expiryDate']
#     cvv = request.form['cvv']
    
#     # Normally, process the payment here (this is a placeholder)
    
#     user_id = session.get('user_id')  # Retrieve the user ID from the session
#     connection = get_db_connection()
    
#     if connection:
#         cursor = connection.cursor()
#         try:
#             # Fetch purchased courses for the user
#             cursor.execute("""
#                 SELECT courses.name 
#                 FROM cart 
#                 JOIN courses ON cart.course_id = courses.id 
#                 WHERE cart.user_id = %s
#             """, (user_id,))
#             courses = [course[0] for course in cursor.fetchall()]

#             return render_template('thanks.html', courses=', '.join(courses))
#         except Exception as e:
#             flash('Error processing your order. Please try again.', 'error')
#             logging.error(f"Error: {e}")
#             return redirect(url_for('index'))
#         finally:
#             cursor.close()
#             connection.close()

@app.route('/logout')
def logout():
    session.clear()  # Clear the session
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
