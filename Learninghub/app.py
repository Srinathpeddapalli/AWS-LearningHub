from flask import Flask, render_template, request, redirect, url_for, flash, session
import pymysql
import bcrypt
import logging

app = Flask(__name__)
app.secret_key = "supersecretkey"

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Password',  # Change this to your actual DB password
    'database': 'dummy'
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
                    return redirect(url_for('courses_cart'))  # Redirect to cart page
                else:
                    flash('Invalid credentials. Please try again.', 'error')
            finally:
                cursor.close()
                connection.close()
        else:
            flash('Could not connect to the database.', 'error')

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

@app.route('/courses_cart')
def courses_cart():
    return render_template('courses_cart.html')

@app.route('/cart')
def cart():
    return render_template('cart.html')

@app.route('/thanks', methods=['POST'])
def thanks():
    user_id = session.get('user_id')  # Retrieve the user ID from the session
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        try:
            # Fetch the user's name
            cursor.execute("SELECT name FROM users WHERE id = %s", (user_id,))
            user_data = cursor.fetchone()

            if user_data is None:
                flash('User not found.', 'error')
                return redirect(url_for('courses_cart'))

            user_name = user_data[0]

            # Fetch purchased courses
            cursor.execute("""
                SELECT courses.name 
                FROM cart 
                JOIN courses ON cart.course_id = courses.id 
                WHERE cart.user_id = %s
            """, (user_id,))
            courses = [course[0] for course in cursor.fetchall()]

            if not courses:
                flash('No courses found in cart.', 'error')
                return redirect(url_for('courses_cart'))

            course_list = ', '.join(courses)  # Convert list to a comma-separated string

            # Optionally: Clear the cart after payment confirmation
            cursor.execute("DELETE FROM cart WHERE user_id = %s", (user_id,))
            connection.commit()

            # Render the thanks page with the user's name and courses
            return render_template('thanks.html', username=user_name, courses=course_list)

        except Exception as e:
            flash('Error processing payment. Please try again.', 'error')
            logging.error(f"Error: {e}")
            return redirect(url_for('courses_cart'))
        finally:
            cursor.close()
            connection.close()
    else:
        flash('Could not connect to the database.', 'error')
        return redirect(url_for('courses_cart'))

if __name__ == '__main__':
    app.run(debug=True)




