# main/routes.py

from flask import render_template, redirect, url_for, request, session, flash
from datetime import datetime
from .models import db, Employee, Task, TaskHistory, rooms, predefined_tasks,custom_priorities, status_mapping, TASK_STATUS
from task_priority_summary_verify_utils.priority import Priority  
from task_priority_summary_verify_utils.verify import TaskVerification, TaskManager 
from task_priority_summary_verify_utils.summary import Reporting
from main.SNS_SQS import ASSIGN_TASK_SNS_TOPIC
from werkzeug.utils import secure_filename
import os
import uuid
from main.s3_lamdba import create_bucket, upload_file_to_s3, generate_presigned_url, trigger_lambda_image_processing
from main.SNS_SQS import publish_message_to_sns
from . import main_bp

# Manager

# Manager dashboard route
@main_bp.route('/manager_dashboard')
def manager_dashboard():
    employees = Employee.query.all()
    tasks = db.session.query(Task, Employee).join(Employee, Task.assigned_to == Employee.id).all()
    
    # Retrieve the assigner information and include the image URL
    tasks_with_assigner = [
        {
            "task": task,
            "assigned_to": assigned_to,
            "assigned_by": Employee.query.get(task.assigned_by),  # Retrieve the assigner
            "image_url": task.image_url  # Add the image URL to the task data
        } for task, assigned_to in tasks
    ]
    
    reporting_instance = Reporting(status_mapping)
    task_summary = reporting_instance.task_summary(tasks)

    return render_template(
        'manager_dashboard.html', 
        rooms=rooms,
        predefined_tasks=predefined_tasks, 
        employees=employees, 
        tasks=tasks_with_assigner,
        task_summary=task_summary,
        custom_priorities=custom_priorities
    )

  
    

@main_bp.route('/assign_task', methods=['POST'])
def assign_task():
    if 'user_id' not in session or not Employee.query.get(session['user_id']).role == 'Manager':
        flash('You need to be logged in as a manager to assign tasks.')
        return redirect(url_for('auth.login'))

    user = Employee.query.get(session['user_id'])
    
    room = request.form['room']
    descriptions = request.form.getlist('description') 
    employee_id = request.form['employee_id']
    priority_level = request.form['priority']

    #  priority
    try:
        priority = Priority(custom_priorities)
        priority.set_priority(priority_level)
    except (ValueError, KeyError) as e:
        flash(str(e) if isinstance(e, ValueError) else f'Invalid priority level. Please select from: {", ".join(custom_priorities.keys())}.')
        return redirect(url_for('main.manager_dashboard'))

    # Validate the assigned employee exists
    assigned_to = Employee.query.get(employee_id)
    if not assigned_to:
        flash('Employee not found.')
        return redirect(url_for('main.manager_dashboard'))

    # the room limit of 5 incomplete rooms
    incomplete_rooms = db.session.query(Task.room).filter_by(
        assigned_to=assigned_to.id, complete=False
    ).distinct().all()
    unique_incomplete_rooms = {room[0] for room in incomplete_rooms}

    if len(unique_incomplete_rooms) >= 5:
        flash('This employee already has the maximum of 5 rooms assigned with incomplete tasks.')
        return redirect(url_for('main.manager_dashboard'))

    for description in descriptions:
        task = Task(room=room, description=description, assigned_to=assigned_to.id, assigned_by=user.id, assigned_time=datetime.now())
        db.session.add(task)

    message = {
    "type": "Task Assigned",
    "details": {
        "room": room,
        "descriptions": descriptions,  
        "priority": priority_level
    },
    "employee_name": assigned_to.name,
    "assigned_to": assigned_to.email 
   
    }

    
    publish_message_to_sns(ASSIGN_TASK_SNS_TOPIC, message)

    # Commit all changes 
    db.session.commit()

    flash('Task assigned successfully!')
    return redirect(url_for('main.manager_dashboard'))

# Verify task 
@main_bp.route('/verify_task/<int:task_id>', methods=['POST'])
def verify_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        flash('Task not found.')
        return redirect(url_for('main.manager_dashboard'))

    if not task.complete:
        flash('Task verification failed: Task is not completed.')
        return redirect(url_for('main.manager_dashboard'))

    status = "completed"
    verification_key = "completed"

    task_instance = TaskVerification(
        name=str(task.id),
        status=status,
        statuses=TASK_STATUS,
        verification_key=verification_key
    )
    
    tasks = {task.id: task_instance}
    task_manager = TaskManager(tasks=tasks, verification_key=verification_key)
    
    if task_manager.verify_task(task.id):
        verified_by = session['user_id']
        
    if task_manager.verify_task(task.id):
        task_history = TaskHistory(
            room=task.room,
            description=task.description,
            assigned_to=task.assigned_to,
            assigned_by=task.assigned_by,
            verified_by=verified_by,
            completed_time=task.completed_time or datetime.now(),
            assigned_time=task.assigned_time,
            verified_time=datetime.now()
        )
        db.session.add(task_history)
        db.session.delete(task)
        db.session.commit()
        flash('Task verified and moved to history.')
    else:
        flash('Task verification failed: Task did not meet verification requirements.')

    return redirect(url_for('main.manager_dashboard'))


# Update task description
@main_bp.route('/update_task/<int:task_id>', methods=['POST'])
def update_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        flash('Task not found.')
        return redirect(url_for('main.manager_dashboard'))

    task.description = request.form['description']
    db.session.commit()
    flash('Task updated successfully.')
    return redirect(url_for('main.manager_dashboard'))


# Delete task 
@main_bp.route('/delete_task/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    task = Task.query.get(task_id)
    if task:
        db.session.delete(task)
        db.session.commit()
        flash('Task deleted successfully.')
    else:
        flash('Task not found.')

    return redirect(url_for('main.manager_dashboard'))


# Employee

# View tasks based on role
@main_bp.route('/tasks', methods=['GET'])
def view_tasks():
    if 'user_id' not in session:
        flash('You need to be logged in to view your tasks.')
        return redirect(url_for('auth.login'))

    employee = Employee.query.get(session['user_id'])
    tasks = Task.query.all() if employee.role == 'Manager' else Task.query.filter_by(assigned_to=employee.id).all()

    return render_template('employee_dashboard.html', tasks=tasks)

@main_bp.route('/employee_dashboard')
def employee_dashboard():
    if 'user_id' not in session:
        flash('You need to be logged in to view your dashboard.')
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    employee = Employee.query.get(user_id)
    tasks = Task.query.filter_by(assigned_to=employee.id).all()

    # Reporting and task summary for the employee
    ind_reporting_instance = Reporting(status_mapping)
    individual_task_summary = {}

    for task in tasks:
        if task.assigned_to not in individual_task_summary:
            individual_task_summary[task.assigned_to] = {status: 0 for status in status_mapping.values()}
        
        status = ind_reporting_instance.get_task_status(task)
        individual_task_summary[task.assigned_to][status] += 1

    return render_template('employee_dashboard.html', tasks=tasks, task_summary=individual_task_summary)

@main_bp.route('/complete_task/<int:task_id>', methods=['POST'])
def complete_task(task_id):
    task = Task.query.get(task_id)
    user_id = session.get('user_id')

    # Check if task exists and is assigned to the current user
    if task and task.assigned_to == user_id:
        # Optional image upload
        file = request.files.get("image")
        if file and file.filename:  # If a file is uploaded
            # Validate file type
            allowed_extensions = {'png', 'jpg', 'jpeg'}
            if file and '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                filename = secure_filename(file.filename)
                # UUID to avoid conflicts with the original file names
                key = f"task_images/{task_id}/{uuid.uuid4()}_{filename}"
                
                create_bucket() 
                try:
                    s3_url = upload_file_to_s3(file, key)  
                    task.image_url = s3_url  
                    db.session.commit()
                    
                    processed_key = trigger_lambda_image_processing(key)
                    processed_s3_url = generate_presigned_url(processed_key)
                    if processed_s3_url:
                        task.image_url = processed_s3_url  
                    else:
                        flash("Error generating presigned URL for processed image.")
                        return redirect(url_for("main.employee_dashboard"))
                except Exception as e:
                    flash("Error uploading image, but task will still be marked complete.")
                    print(f"Error uploading image: {e}")
            else:
                flash("Invalid file type. Allowed types are: png, jpg, jpeg.")
                return redirect(url_for("main.employee_dashboard"))

        if task.image_url:
            # Check if the pre-signed URL is valid or has expired
            
            s3_url = task.image_url
            #  regenerate url (if expired)
            # task.image_url = generate_presigned_url(bucket_name, key)

        
        task.complete = True
        task.completed_time = datetime.now()
        db.session.commit()  

        employee = Employee.query.get(user_id)
        assigned_by_employee = Employee.query.get(task.assigned_by)
        

        flash('Task marked as complete.')
    else:
        flash('You do not have permission to mark this task as complete or the task does not exist.')

    return redirect(url_for('main.employee_dashboard'))