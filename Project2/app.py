from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database setup (SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Login manager setup
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User model for students
class Student(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    register_number = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(1000))
    name = db.Column(db.String(50))
    date_of_birth = db.Column(db.String(50))
    phone_number = db.Column(db.String(20))
    address = db.Column(db.String(100))
    email = db.Column(db.String(50), unique=True)
    Course = db.Column(db.String(20))
    section = db.Column(db.String(10))
   


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))  # Corrected to 'student.id'
    date = db.Column(db.String(50))
    status = db.Column(db.String(50))

class Arrears(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))  # Corrected to 'student.id'
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'))  # Assuming you have a 'subject' table with 'id' column

class AssignedSubject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_name = db.Column(db.String(50))
    subject_code = db.Column(db.String(20))
   

   

@login_manager.user_loader
def load_user(user_id):
    return Student.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == "POST":
        register_number = request.form.get('register_number')
        password = request.form.get('password')
        student = Student.query.filter_by(register_number=register_number).first()

        if student and check_password_hash(student.password, password):
            login_user(student)
            flash("Login Success", "primary")
            return redirect(url_for('profile'))
        else:
            flash("Invalid credentials", "danger")
           
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logout Successful", "warning")
    return redirect(url_for('login'))


# Admin model for admin-related data
class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(1000))

@app.route('/admin/register', methods=['POST', 'GET'])
def admin_register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        new_admin = Admin(
            username=username,
            password=generate_password_hash(password)
        )

        db.session.add(new_admin)
        db.session.commit()

        flash("Admin Registration Successful. Please login.", "success")
        return redirect(url_for('admin_login'))

    return render_template('admin_register.html')

    
@app.route('/admin/login', methods=['POST','GET'])
def admin_login():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        print("Submitted Username:", username)
        print("Submitted Password:", password)
        
        admin = Admin.query.filter_by(username=username).first()
        if admin:
            print("Admin Found in Database")
            if admin and check_password_hash(admin.password, password):
                login_user(admin)
                flash("Admin Login Success", "primary")
                return redirect(url_for('admin_dashboard'))
        else:
            print("Admin Not Found")

        flash("Invalid admin credentials", "danger")
        return render_template('admin_login.html')

    return render_template('admin_login.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    flash("Admin logout successfull", "warning")
    return redirect(url_for('admin_login'))

def admin_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not (current_user, Admin):
            flash("You do not have permission to access this page.", "danger")
            return redirect(url_for('admin_login'))
        return func(*args, **kwargs)
    return decorated_function


def is_admin(user):
    # Assuming there's a field 'is_admin' in the Admin model
    if isinstance(user, Admin):
        return user.is_admin
    return False




@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    students=Student.query.all()
    return render_template('admin_dashboard.html',students=students)

@app.route('/admin/students/add', methods=['GET', 'POST'])
@admin_required
def admin_add_student():
    if request.method == 'POST':
         # Get form data
        register_number = request.form.get('register_number')
        name = request.form.get('name')
        date_of_birth = request.form.get('date_of_birth')
        phone_number = request.form.get('phone_number')
        address = request.form.get('address')
        password = request.form.get('password')
        email = request.form.get('email')
        course = request.form.get('course')
        section = request.form.get('section')

        # Create a new student object
        new_student = Student(
            register_number=register_number,
            name=name,
            date_of_birth=date_of_birth,
            phone_number=phone_number,
            address=address,
            password=generate_password_hash(password),
            email=email,
            Course=course,
            section=section
        )

        # Add the new student to the database
        db.session.add(new_student)
        db.session.commit()

        flash("Student added successfully.", "success")
        return redirect(url_for('admin_dashboard'))

    return render_template('admin_add_student.html')
    
   

@app.route('/admin/students/<int:student_id>')
@admin_required
def admin_view_student(student_id):
    student = Student.query.get_or_404(student_id)
    return render_template('admin_view_student.html', student=student)

@app.route('/admin/students/edit/<int:student_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_student(student_id):
    student = Student.query.get_or_404(student_id)

    if request.method == 'POST':
            # Update student details
        student.name = request.form.get('name')
        student.date_of_birth = request.form.get('date_of_birth')
        student.phone_number = request.form.get('phone_number')
        student.address = request.form.get('address')
        student.email = request.form.get('email')
        student.course = request.form.get('course')
        student.section = request.form.get('section')

        db.session.commit()
        flash("Student details updated successfully.", "success")
        return redirect(url_for('admin_dashboard'))
        

    return render_template('admin_edit_student.html', student=student)

@app.route('/admin/students/delete/<int:student_id>')
@admin_required
def admin_delete_student(student_id):
    student = Student.query.get_or_404(student_id    )

    # Delete the student
    db.session.delete(student)
    db.session.commit()
    flash("Student deleted successfully.", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/profile')
@login_required
def profile():
    # Retrieve the current logged-in user
    student = current_user

    # Retrieve additional user-related data (e.g., attendance, subjects with arrears)
  
    

    # Render the profile template with user-related data
    return render_template('profile.html', student=student, attendance=attendance,)

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        register_number = request.form.get('register_number')
        name = request.form.get('name')
        date_of_birth = request.form.get('date_of_birth')
        phone_number = request.form.get('phone_number')
        address = request.form.get('address')
        password = request.form.get('password')
        email = request.form.get('email')

        new_student = Student(
            register_number=register_number,
            name=name,
            date_of_birth=date_of_birth,
            phone_number=phone_number,
            address=address,
            password=generate_password_hash(password),
            email=email
        )

        db.session.add(new_student)
        db.session.commit()

        flash("Registration Successful. Please login.", "success")
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # Your signup logic here
    return render_template('signup.html')

@app.route('/attendance')
@login_required
def attendance():
    student = current_user
    attendance = Attendance.query.filter_by(student_id=student.id).all()

    return render_template('attendance.html', student=student, attendance=attendance)

@app.route('/admin/assign_subject', methods=['GET', 'POST'])
@admin_required
def admin_assign_subject():
    if request.method == 'POST':

        subject_name = request.form.get('subject_name')
        subject_code = request.form.get('subject_code')

        assigned_subject = AssignedSubject(
            
            subject_name=subject_name,
            subject_code=subject_code
        )

        db.session.add(assigned_subject)
        db.session.commit()

        flash("Subject assigned to the student successfully.", "success")
        return redirect(url_for('admin_view_student', ))

    students = Student.query.all()
    return render_template('admin_assign_subject.html', students=students)

@app.route('/view_assigned_subjects')
@login_required
def view_assigned_subjects():
    student = current_user
    assigned_subjects = AssignedSubject.query.filter_by().all()
    return render_template('assigned_subjects.html', assigned_subjects=assigned_subjects)




if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables before running the app
    app.run(debug=True,port=5000)