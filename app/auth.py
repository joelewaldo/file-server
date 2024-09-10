from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_user, login_required, logout_user
from datetime import datetime
from pytz import utc
from .models.user_model import User, UserSettings
from .extensions import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
  if request.method == 'POST':
    data = request.form
    if User.query.filter_by(username=data['username']).first():
      flash('Username already exists')
      return jsonify({"message": "User already exists"}), 400

    new_user = User(username=data['username'], name=data['name'])
    new_user.set_password(data['password'])
    db.session.add(new_user)
    db.session.commit()

    new_user_settings = UserSettings(user_id=new_user.id)
    db.session.add(new_user_settings)
    db.session.commit()
    return redirect(url_for('auth.login'))

  return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
  if request.method == 'POST':
    data = request.form
    user = User.query.filter_by(username=data['username']).first()

    if user and user.check_password(data['password']):

      if not user.api_key or utc.localize(datetime.now()) > utc.localize(user.api_key_expiration):
        api_key = user.generate_api_key()
        db.session.commit()
      else:
        api_key = user.api_key
      
      remember = True if data.get('remember') else False

      login_user(user, remember=remember)
      return redirect(url_for('main.list_files'))

        # return jsonify({"api_key": api_key}), 200
      
    flash('Invalid Credentials')
    return jsonify({"message": "Invalid credentials"}), 401

  return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
  logout_user()
  return redirect(url_for('main.index'))

def authenticate(api_key):
  user = User.query.filter_by(api_key=api_key).first()
  return user if user else None