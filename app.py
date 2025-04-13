from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///crm.db'
app.config['SECRET_KEY'] = 'your_secret_key'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(50))
    tags = db.Column(db.String(250))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    interactions = db.relationship('InteractionLog', backref='contact', lazy=True, cascade="all, delete-orphan")
    tasks = db.relationship('FollowUpTask', backref='contact', lazy=True, cascade="all, delete-orphan")

class InteractionLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id'), nullable=False)
    note = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class FollowUpTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id'), nullable=False)
    task = db.Column(db.String(250), nullable=False)
    due_date = db.Column(db.Date)
    completed = db.Column(db.Boolean, default=False)

@app.route('/')
def index():
    search_query = request.args.get('search', '')
    tag_filter = request.args.get('tag', '')

    contacts = Contact.query

    if search_query:
        contacts = contacts.filter(
            Contact.name.ilike(f"%{search_query}%") |
            Contact.email.ilike(f"%{search_query}%") |
            Contact.tags.ilike(f"%{search_query}%")
        )

    if tag_filter:
        contacts = contacts.filter(Contact.tags.ilike(f"%{tag_filter}%"))

    contacts = contacts.order_by(Contact.created_at.desc()).all()
    all_tags = list({tag.strip() for c in Contact.query.all() for tag in c.tags.split(',') if tag.strip()})

    return render_template('index.html', contacts=contacts, search_query=search_query, tag_filter=tag_filter, all_tags=all_tags)

@app.route('/add', methods=['POST'])
def add_contact():
    new_contact = Contact(
        name=request.form['name'],
        email=request.form['email'],
        phone=request.form['phone'],
        tags=request.form['tags'],
        notes=request.form['notes']
    )
    db.session.add(new_contact)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete_contact(id):
    contact = Contact.query.get_or_404(id)
    db.session.delete(contact)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/add_note/<int:contact_id>', methods=['POST'])
def add_note(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    note = request.form['note']
    if note.strip():
        new_entry = InteractionLog(contact_id=contact.id, note=note)
        db.session.add(new_entry)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/add_task/<int:contact_id>', methods=['POST'])
def add_task(contact_id):
    task_text = request.form['task']
    due_date = request.form['due_date']
    new_task = FollowUpTask(contact_id=contact_id, task=task_text, due_date=due_date or None)
    db.session.add(new_task)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/complete_task/<int:task_id>')
def complete_task(task_id):
    task = FollowUpTask.query.get_or_404(task_id)
    task.completed = True
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete_task/<int:task_id>')
def delete_task(task_id):
    task = FollowUpTask.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
