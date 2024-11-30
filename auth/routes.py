# auth/routes.py
import re
from flask import render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
from . import auth_bp
from main.models import db, Employee  # Make sure to import your database models



import re
from flask import render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError
from . import auth_bp
from main.models import db, Employee

# Signup Route
@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            name = request.form['name']
            employee_number = request.form['employee_number']
            email = request.form['email']  # Get email from form
            password = generate_password_hash(request.form['password'])
            role = request.form['role']
        except KeyError as e:
            flash(f"Missing field: {str(e)}")
            return redirect(url_for('auth.signup'))

        # Validate employee number format
        if not re.match(r'^[A-Za-z]\d{3}$', employee_number):
            flash('Employee number must be a letter followed by three digits (e.g., A123).', 'danger')
            return redirect(url_for('auth.signup'))

        # Validate email format
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash('Invalid email address format. Please provide a valid email.', 'danger')
            return redirect(url_for('auth.signup'))

        # Check if employee number already exists
        existing_employee = Employee.query.filter_by(employee_number=employee_number).first()
        if existing_employee:
            flash('Employee number already exists. Please choose a different one.', 'danger')
            return redirect(url_for('auth.signup'))

        # Check if email already exists
        existing_email = Employee.query.filter_by(email=email).first()
        if existing_email:
            flash('Email address is already registered. Please choose a different one.', 'danger')
            return redirect(url_for('auth.signup'))

        try:
            # Create a new employee object with email
            new_employee = Employee(name=name, employee_number=employee_number, email=email, password=password, role=role)
            db.session.add(new_employee)
            db.session.commit()
            flash('Signup successful! Please log in.')
            return redirect(url_for('auth.login'))
        except IntegrityError:
            db.session.rollback()  # Rollback the transaction to prevent further errors
            flash('An error occurred. Please try again.', 'danger')
            return redirect(url_for('auth.signup'))

    return render_template('signup.html')


#
# Login Route
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            employee_number = request.form['employee_number']
            password = request.form['password']
            role = request.form['role']  # User-selected role
        except KeyError as e:
            flash(f"Missing field: {str(e)}")
            return redirect(url_for('auth.login'))

        # Only validate the employee number if it's provided (not empty)
        if employee_number and not re.match(r'^[A-Za-z]\d{3}$', employee_number):
            flash('Employee number must be a letter followed by three digits (e.g., A123).', 'danger')
            return redirect(url_for('auth.login'))

        # Fetch employee with matching employee_number and role
        employee = Employee.query.filter_by(employee_number=employee_number, role=role).first()

        if employee and check_password_hash(employee.password, password):
            session['user_id'] = employee.id
            flash('Login successful!')

            # Redirect based on role
            if employee.role == 'Manager':
                return redirect(url_for('main.manager_dashboard'))  # Redirect to Manager Dashboard
            elif employee.role == 'Staff':
                return redirect(url_for('main.employee_dashboard'))  # Redirect to Employee Dashboard
            else:
                flash('Unknown role. Please contact an administrator.', 'danger')
                return redirect(url_for('auth.login'))
        else:
            flash('Invalid credentials or role. Please try again.', 'danger')
            return redirect(url_for('auth.login'))

    return render_template('login.html')

# Logout Route
@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)  # Remove user_id from the session
    flash('You have been logged out successfully.')
    return redirect(url_for('auth.login'))
