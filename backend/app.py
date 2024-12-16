from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user, login_user, logout_user
from models import User, Subject, Homework
from forms import LoginForm, SignupForm, SubjectForm, HomeworkForm
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

main = Blueprint('main', __name__)

@main.route('/')
def index():
    if current_user.is_authenticated:
        # Fetch homeworks ordered by due_date ascending
        user_homeworks = Homework.query.join(Subject).filter(Subject.user_id == current_user.id).order_by(Homework.due_date.asc()).all()
        current_time = datetime.now()
        return render_template('index.html', homeworks=user_homeworks, current_time=current_time)
    return render_template('index.html')

@main.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        flash('You are already logged in.', 'info')
        return redirect(url_for('main.index'))
    
    form = SignupForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        password = form.password.data
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('main.signup'))
        
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('main.login'))
    
    return render_template('signup.html', form=form)

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash('You are already logged in.', 'info')
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        password = form.password.data
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('main.login'))
    
    return render_template('login.html', form=form)

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@main.route('/subjects', methods=['GET', 'POST'])
@login_required
def subjects():
    form = SubjectForm()
    if form.validate_on_submit():
        subject_name = form.name.data.strip()
        if subject_name:
            new_subject = Subject(name=subject_name, user_id=current_user.id)
            db.session.add(new_subject)
            db.session.commit()
            flash('Subject added successfully!', 'success')
        else:
            flash('Subject name cannot be empty.', 'danger')
        return redirect(url_for('main.subjects'))
    
    user_subjects = Subject.query.filter_by(user_id=current_user.id).all()
    return render_template('subjects.html', subjects=user_subjects, form=form)

@main.route('/subjects/edit/<int:subject_id>', methods=['GET', 'POST'])
@login_required
def edit_subject(subject_id):
    subject = Subject.query.filter_by(id=subject_id, user_id=current_user.id).first_or_404()
    form = SubjectForm(obj=subject)
    
    if form.validate_on_submit():
        new_name = form.name.data.strip()
        if new_name:
            subject.name = new_name
            db.session.commit()
            flash('Subject updated successfully!', 'success')
            return redirect(url_for('main.subjects'))
        else:
            flash('Subject name cannot be empty.', 'danger')
    
    return render_template('edit_subject.html', subject=subject, form=form)

@main.route('/subjects/delete/<int:subject_id>', methods=['POST'])
@login_required
def delete_subject(subject_id):
    subject = Subject.query.filter_by(id=subject_id, user_id=current_user.id).first_or_404()
    db.session.delete(subject)
    db.session.commit()
    flash('Subject deleted successfully!', 'success')
    return redirect(url_for('main.subjects'))

@main.route('/homeworks', methods=['GET', 'POST'])
@login_required
def homeworks():
    form = HomeworkForm()
    user_subjects = Subject.query.filter_by(user_id=current_user.id).all()
    form.subject_id.choices = [(subject.id, subject.name) for subject in user_subjects]
    
    if form.validate_on_submit():
        description = form.description.data.strip()
        due_date = form.due_date.data
        subject_id = form.subject_id.data
        
        if not description:
            flash('Homework description cannot be empty.', 'danger')
            return redirect(url_for('main.homeworks'))
        
        subject = Subject.query.filter_by(id=subject_id, user_id=current_user.id).first()
        if not subject:
            flash('Selected subject does not exist.', 'danger')
            return redirect(url_for('main.homeworks'))
        
        new_homework = Homework(description=description, due_date=due_date, subject_id=subject.id)
        db.session.add(new_homework)
        db.session.commit()
        flash('Homework added successfully!', 'success')
        return redirect(url_for('main.homeworks'))
    
    user_homeworks = Homework.query.join(Subject).filter(Subject.user_id == current_user.id).order_by(Homework.due_date.asc()).all()
    current_time = datetime.now()
    return render_template('homeworks.html', homeworks=user_homeworks, subjects=user_subjects, form=form, current_time=current_time)

@main.route('/homeworks/edit/<int:homework_id>', methods=['GET', 'POST'])
@login_required
def edit_homework(homework_id):
    homework = Homework.query.join(Subject).filter(Homework.id == homework_id, Subject.user_id == current_user.id).first_or_404()
    form = HomeworkForm(obj=homework)
    user_subjects = Subject.query.filter_by(user_id=current_user.id).all()
    form.subject_id.choices = [(subject.id, subject.name) for subject in user_subjects]
    
    if form.validate_on_submit():
        description = form.description.data.strip()
        due_date = form.due_date.data
        subject_id = form.subject_id.data
        
        if not description:
            flash('Homework description cannot be empty.', 'danger')
            return redirect(url_for('main.edit_homework', homework_id=homework_id))
        
        subject = Subject.query.filter_by(id=subject_id, user_id=current_user.id).first()
        if not subject:
            flash('Selected subject does not exist.', 'danger')
            return redirect(url_for('main.edit_homework', homework_id=homework_id))
        
        homework.description = description
        homework.due_date = due_date
        homework.subject_id = subject.id
        db.session.commit()
        flash('Homework updated successfully!', 'success')
        return redirect(url_for('main.homeworks'))
    
    return render_template('edit_homework.html', homework=homework, subjects=user_subjects, form=form)

@main.route('/homeworks/delete/<int:homework_id>', methods=['POST'])
@login_required
def delete_homework(homework_id):
    homework = Homework.query.join(Subject).filter(Homework.id == homework_id, Subject.user_id == current_user.id).first_or_404()
    db.session.delete(homework)
    db.session.commit()
    flash('Homework deleted successfully!', 'success')
    return redirect(url_for('main.homeworks'))
