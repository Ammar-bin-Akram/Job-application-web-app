from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Jobs(db.Model):
    __tablename__ = 'jobs'  # Specify the table name

    id = db.Column(db.Integer, primary_key=True)
    job_link = db.Column(db.String(255), nullable=False)
    job_status = db.Column(db.String(50), nullable=False)
