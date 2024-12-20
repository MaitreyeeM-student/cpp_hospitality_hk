# main/models.py

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import String


# Initialize SQLAlchemy
db = SQLAlchemy()

# Predefined rooms (101-104, 201-204, ..., 505)
rooms = [f"{floor}0{room}" for floor in range(1, 6) for room in range(1, 5)]


predefined_tasks = [
    "Clean room",
    "Restock supplies",
    "Prepare room for new guest",
    "Clean bathrooms",
    "Check for damages",
    "Change bed linens",
    "Pickup trash from lobby"
]

# Priority mapping
custom_priorities = {
    'Urgent': 5,
    'High': 3,
    'Normal': 2,
    'Low': 1
}

# Status mapping for tasks
status_mapping = {
    'done': 'Completed',
    'in_progress': 'Incompleted',
}

# Task status verification
TASK_STATUS = {
    "completed": "completed"
}

# Employee database model
class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    employee_number = db.Column(db.String(100), unique=True, nullable=False)
    role = db.Column(db.String(100))  # Role of employee (e.g., 'Manager' or 'Staff')
    email = db.Column(db.String(100), unique=True, nullable=False)  # New field for email
    password = db.Column(db.String(200), nullable=False)
   
    
    # Relationship assignment between the tables
    tasks_assigned_to = db.relationship(
        'Task', 
        lazy=True,
        foreign_keys='Task.assigned_to'  
    )

    
    tasks_assigned_by = db.relationship(
        'Task', 
        lazy=True,
        foreign_keys='Task.assigned_by' 
    )


    def __repr__(self):
        return f'<Employee {self.name}>'
        

# Task database model
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room = db.Column(db.String(100), nullable=False)  
    description = db.Column(db.String(500), nullable=False)  
    assigned_to = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)  
    assigned_by = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)  
    complete = db.Column(db.Boolean, default=False)  
    verified = db.Column(db.Boolean, default=False)
    notes = db.Column(db.String(500), nullable=True) 
    priority = db.Column(db.String(100), nullable=False, default='Normal')
    assigned_time = db.Column(db.DateTime, default=datetime.now)  
    completed_time = db.Column(db.DateTime, nullable=True)  
    image_url = db.Column(db.String(3000), nullable=True)
    

    def __repr__(self):
        return f'<Task {self.room} - {self.description}>'
        


class TaskHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    assigned_by = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    verified_by = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False) 
    completed_time = db.Column(db.DateTime, nullable=False)
    assigned_time = db.Column(db.DateTime, nullable=False)
    verified_time = db.Column(db.DateTime, nullable=False)
    image_url = db.Column(db.String(3000), nullable=True)

    
    
    assigned_employee = db.relationship(
        'Employee',
        foreign_keys=[assigned_to]
    )
    assignee_employee = db.relationship(
        'Employee',
        foreign_keys=[assigned_by]
    )
    verified_employee = db.relationship(
        'Employee',
        foreign_keys=[verified_by]
    )

    def __repr__(self):
        return f'<TaskHistory room={self.room} task={self.description}>'
        
  