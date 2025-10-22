import random

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS


app = Flask(__name__)
app.config['SECRET_KEY'] = 'oremus'
app.config['JSON_AS_ASCII'] = False
CORS(app)

# ============================================
# HOME & MAIN ROUTES
# ============================================
@app.route('/')
def index():
    """Home page - renders the master dashboard"""
    return render_template('index.html')


# ============================================
# DASHBOARD ROUTES
# ============================================
@app.route('/dashboard')
def dashboard():
    """Main dashboard view"""
    return render_template('master.html')

@app.route('/dashboard/1')
def dashboard_1():
    """Dashboard variant 1"""
    return render_template('master.html')

@app.route('/dashboard/2')
def dashboard_2():
    """Dashboard variant 2"""
    return render_template('master.html')

@app.route('/dashboard/3')
def dashboard_3():
    """Dashboard variant 3"""
    return render_template('master.html')


# ============================================
# COMPONENTS ROUTES
# ============================================
@app.route('/components/avatars')
def avatars():
    """Avatars component page"""
    return render_template('master.html')

@app.route('/components/buttons')
def buttons():
    """Buttons component page"""
    return render_template('master.html')


# ============================================
# USER PROFILE ROUTES
# ============================================
@app.route('/profile')
def profile():
    """User profile page"""
    return render_template('master.html')

@app.route('/profile/edit')
def profile_edit():
    """Edit profile page"""
    return render_template('master.html')

@app.route('/profile/settings')
def profile_settings():
    """Profile settings page"""
    return render_template('master.html')


# ============================================
# USER MANAGEMENT ROUTES
# ============================================
@app.route('/users')
def users():
    """List of all users"""
    return render_template('master.html')

@app.route('/users/add', methods=['GET', 'POST'])
def add_user():
    """Add new customer/user"""
    if request.method == 'POST':
        # Handle form submission
        data = request.get_json() or request.form
        return jsonify({
            'status': 'success',
            'message': 'User added successfully'
        })
    return render_template('master.html')

@app.route('/users/<int:user_id>')
def view_user(user_id):
    """View specific user details"""
    return render_template('master.html')

@app.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
def edit_user(user_id):
    """Edit specific user"""
    if request.method == 'POST':
        return jsonify({
            'status': 'success',
            'message': 'User updated successfully'
        })
    return render_template('master.html')

@app.route('/users/<int:user_id>/delete', methods=['POST'])
def delete_user(user_id):
    """Delete specific user"""
    return jsonify({
        'status': 'success',
        'message': 'User deleted successfully'
    })


# ============================================
# NAVIGATION & UTILITY ROUTES
# ============================================
@app.route('/help')
def help():
    """Help page"""
    return render_template('master.html')

@app.route('/licenses')
def licenses():
    """Licenses information page"""
    return render_template('master.html')

@app.route('/logout')
def logout():
    """Logout user and redirect to home"""
    # In a real application, you would clear the session here
    return redirect(url_for('index'))


# ============================================
# API ENDPOINTS (Optional)
# ============================================
@app.route('/api/dashboard/stats')
def get_dashboard_stats():
    """API endpoint to get dashboard statistics"""
    stats = {
        'new_users': random.randint(1, 50),
        'sales': random.randint(10, 100),
        'subscribers': random.randint(5, 200),
        'total_income': random.randint(1000, 50000),
        'total_spend': random.randint(100, 10000)
    }
    return jsonify(stats)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=59000)