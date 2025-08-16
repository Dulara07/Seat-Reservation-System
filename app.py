from flask import Flask, render_template, redirect, url_for, flash, request
from config import Config
from models import db, User, Seat, Reservation
from forms import RegisterForm, LoginForm, ReserveForm
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
from functools import wraps

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


def admin_required(fn):
    """Decorator to require admin role."""
    @wraps(fn)
    def wrapper(*a, **k):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required', 'danger')
            return redirect(url_for('index'))
        return fn(*a, **k)
    return wrapper


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.before_first_request
def create_tables():
    db.create_all()

app.jinja_env.globals.update(now=datetime.now)

@app.context_processor
def inject_current_year():
    return {'current_year': datetime.now().year}

# -----------------------
#intern routes
# -----------------------

@app.route('/')
def index():
    return render_template('index.html')


#@app.route('/register', methods=['GET', 'POST'])
#def register():
#    form = RegisterForm()
#    if form.validate_on_submit():
#        # hash + store in password_hash (matches models.User)
#        hashed = generate_password_hash(form.password.data)
 #       user = User(name=form.name.data, email=form.email.data, password_hash=hashed, role='intern')
  #      db.session.add(user)
   #     try:
    #        db.session.commit()
     #   except Exception as e:
      #      db.session.rollback()
       #     flash('Error creating user (maybe email already exists).', 'danger')
        #    return render_template('register.html', form=form)
        #flash('Registration successful. Please log in.', 'success')
        #return redirect(url_for('login'))
   # return render_template('register.html', form=form)




#testing route for the register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        # hash + store in password_hash (matches models.User)
        hashed = generate_password_hash(form.password.data)
        user = User(name=form.name.data, email=form.email.data, password_hash=hashed, role='intern')
        db.session.add(user)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash('Error creating user (maybe email already exists).', 'danger')
            return render_template('register.html', form=form)
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)



@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            flash('Logged in.', 'success')
            # optional `next` param support
            nxt = request.args.get('next')
            return redirect(nxt or url_for('index'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out.', 'info')
    return redirect(url_for('index'))


@app.route('/seats')
@login_required
def seats():
    # template expects `qdate`
    qdate = request.args.get('date')
    if qdate:
        try:
            qdate = datetime.strptime(qdate, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format, using today.', 'warning')
            qdate = date.today()
    else:
        qdate = date.today()

    reserved_seat_ids = [r.seat_id for r in Reservation.query.filter_by(date=qdate, status='active').all()]
    available_seats = Seat.query.filter(Seat.status == 'available')
    if reserved_seat_ids:
        available_seats = available_seats.filter(~Seat.id.in_(reserved_seat_ids))
    available_seats = available_seats.all()

    return render_template('seats.html', seats=available_seats, qdate=qdate)


@app.route('/reserve/<int:seat_id>', methods=['GET', 'POST'])
@login_required
def reserve(seat_id):
    seat = Seat.query.get_or_404(seat_id)
    form = ReserveForm()
    # limit seat choices to selected seat for normal user flow
    form.seat_id.choices = [(seat.id, f'{seat.seat_number} - {seat.location}')]
    if form.validate_on_submit():
        rdate = form.date.data
        if rdate < date.today():
            flash('Cannot book past dates.', 'danger')
            return render_template('reserve.html', form=form, seat=seat)

        # check if user already has reservation that date
        existing = Reservation.query.filter_by(user_id=current_user.id, date=rdate, status='active').first()
        if existing:
            flash('You already have a reservation for that date.', 'warning')
            return redirect(url_for('my_reservations'))

        # check seat availability
        booked = Reservation.query.filter_by(seat_id=seat.id, date=rdate, status='active').first()
        if booked:
            flash('Sorry, seat was just booked by someone else.', 'danger')
            return redirect(url_for('seats', date=rdate.strftime('%Y-%m-%d')))

        new_res = Reservation(user_id=current_user.id, seat_id=seat.id, date=rdate, time_slot=form.time_slot.data)
        db.session.add(new_res)
        db.session.commit()
        flash('Reservation created.', 'success')
        return redirect(url_for('my_reservations'))

    # pre-fill date with today
    if not form.date.data:
        form.date.data = date.today()
    return render_template('reserve.html', form=form, seat=seat)


@app.route('/my_reservations', methods=['GET', 'POST'])
@login_required
def my_reservations():
    # template posts to this page to cancel (no action attr)
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'cancel':
            try:
                rid = int(request.form.get('res_id'))
            except (TypeError, ValueError):
                flash('Invalid reservation id.', 'danger')
                return redirect(url_for('my_reservations'))
            res = Reservation.query.get_or_404(rid)
            if res.user_id != current_user.id and current_user.role != 'admin':
                flash('Not authorized', 'danger')
                return redirect(url_for('my_reservations'))
            if res.date < date.today():
                flash('Cannot cancel past reservations', 'warning')
                return redirect(url_for('my_reservations'))
            res.status = 'cancelled'
            db.session.commit()
            flash('Reservation cancelled', 'info')
            return redirect(url_for('my_reservations'))

    reservations = Reservation.query.filter_by(user_id=current_user.id).order_by(Reservation.date.desc()).all()
    return render_template('my_reservations.html', reservations=reservations)


@app.route('/cancel/<int:res_id>')
@login_required
def cancel(res_id):
    res = Reservation.query.get_or_404(res_id)
    if res.user_id != current_user.id and current_user.role != 'admin':
        flash('Not authorized', 'danger')
        return redirect(url_for('index'))
    if res.date < date.today():
        flash('Cannot cancel past reservations', 'warning')
        return redirect(url_for('my_reservations'))
    res.status = 'cancelled'
    db.session.commit()
    flash('Reservation cancelled', 'info')
    return redirect(url_for('my_reservations'))


@app.route('/modify/<int:res_id>', methods=['GET', 'POST'])
@login_required
def modify_reservation(res_id):
    res = Reservation.query.get_or_404(res_id)
    if res.user_id != current_user.id and current_user.role != 'admin':
        flash('Not authorized', 'danger')
        return redirect(url_for('index'))
    if res.date < date.today():
        flash('Cannot modify past reservations.', 'warning')
        return redirect(url_for('my_reservations'))

    form = ReserveForm()
    form.seat_id.choices = [(s.id, f'{s.seat_number} - {s.location}') for s in Seat.query.filter_by(status='available').all()]

    if form.validate_on_submit():
        # check new seat availability for given date
        if Reservation.query.filter_by(seat_id=form.seat_id.data, date=form.date.data, status='active').filter(Reservation.id != res.id).first():
            flash('Selected seat is not available for this date.', 'danger')
            return redirect(url_for('modify_reservation', res_id=res.id))

        res.seat_id = form.seat_id.data
        res.date = form.date.data
        res.time_slot = form.time_slot.data
        db.session.commit()
        flash('Reservation updated successfully.', 'success')
        return redirect(url_for('my_reservations'))

    # pre-fill
    form.seat_id.data = res.seat_id
    form.date.data = res.date
    form.time_slot.data = res.time_slot
    return render_template('modify_reservation.html', form=form, res=res)


# -----------------------
# Admin routes
# -----------------------




@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    # compute some basic stats for the admin dashboard template
    total_reservations = Reservation.query.count()
    today_reservations = Reservation.query.filter_by(date=date.today()).count()
    # seat usage: (seat_number, count)
    seat_usage = db.session.query(Seat.seat_number, db.func.count(Reservation.id).label('count')) \
        .outerjoin(Reservation) \
        .group_by(Seat.seat_number) \
        .order_by(db.desc('count')).all()

    return render_template('admin_dashboard.html',
                           total_reservations=total_reservations,
                           today_reservations=today_reservations,
                           seat_usage=seat_usage)


@app.route('/admin/seats', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_seats():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            seat_number = request.form.get('seat_number')
            location = request.form.get('location')
            if seat_number:
                s = Seat(seat_number=seat_number, location=location)
                db.session.add(s)
                db.session.commit()
                flash('Seat added.', 'success')
            else:
                flash('Seat number required.', 'danger')

        elif action == 'delete':
            try:
                sid = int(request.form.get('seat_id'))
                Seat.query.filter_by(id=sid).delete()
                db.session.commit()
                flash('Seat removed.', 'info')
            except Exception:
                flash('Could not delete seat.', 'danger')

        elif action == 'edit':
            try:
                sid = int(request.form.get('seat_id'))
                seat = Seat.query.get_or_404(sid)
                seat.seat_number = request.form.get('seat_number')
                seat.location = request.form.get('location')
                # optional status field in template
                status = request.form.get('status')
                if status:
                    seat.status = status
                db.session.commit()
                flash('Seat updated.', 'info')
            except Exception:
                flash('Could not update seat.', 'danger')

        return redirect(url_for('admin_seats'))

    seats = Seat.query.all()
    return render_template('admin_seats.html', seats=seats)


@app.route('/admin/reservations', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_reservations():
    # Allow admin to cancel from this page via POST
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'cancel':
            try:
                rid = int(request.form.get('res_id'))
                res = Reservation.query.get_or_404(rid)
                res.status = 'cancelled'
                db.session.commit()
                flash('Reservation cancelled.', 'info')
            except Exception:
                flash('Could not cancel reservation.', 'danger')
        return redirect(url_for('admin_reservations'))

    date_filter = request.args.get('date')
    user_filter = request.args.get('user')

    query = Reservation.query
    if date_filter:
        try:
            date_obj = datetime.strptime(date_filter, '%Y-%m-%d').date()
            query = query.filter_by(date=date_obj)
        except ValueError:
            flash('Invalid date filter ignored.', 'warning')

    if user_filter:
        query = query.join(User).filter(User.name.ilike(f"%{user_filter}%"))

    reservations = query.order_by(Reservation.date.desc()).all()
    return render_template('admin_reservations.html', reservations=reservations)


@app.route('/admin/assign', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_assign():
    form = ReserveForm()
    form.seat_id.choices = [(s.id, f'{s.seat_number} - {s.location}') for s in Seat.query.all()]
    users = User.query.all()
    if request.method == 'POST' and form.validate_on_submit():
        user_id = int(request.form.get('user_id'))
        rdate = form.date.data
        seat_id = form.seat_id.data

        # check seat availability
        if Reservation.query.filter_by(seat_id=seat_id, date=rdate, status='active').first():
            flash('Seat already booked for that date.', 'danger')
            return redirect(url_for('admin_assign'))

        new_r = Reservation(user_id=user_id, seat_id=seat_id, date=rdate, time_slot=form.time_slot.data)
        db.session.add(new_r)
        db.session.commit()
        flash('Seat assigned successfully.', 'success')
        return redirect(url_for('admin_reservations'))

    # default date
    if not form.date.data:
        form.date.data = date.today()
    return render_template('admin_assign.html', form=form, users=users)


@app.route('/admin/reports')
@login_required
@admin_required
def admin_reports():
    total_seats = Seat.query.count()
    total_reservations = Reservation.query.count()
    upcoming_reservations = Reservation.query.filter(Reservation.date >= date.today()).count()
    most_booked = db.session.query(Seat.seat_number, db.func.count(Reservation.id).label('count')) \
        .join(Reservation) \
        .group_by(Seat.seat_number) \
        .order_by(db.desc('count')).first()

    return render_template('admin_reports.html',
                           total_seats=total_seats,
                           total_reservations=total_reservations,
                           upcoming_reservations=upcoming_reservations,
                           most_booked=most_booked)


if __name__ == '__main__':
    # create DB tables if they don't exist (useful on dev)
    with app.app_context():
        db.create_all()
    app.run(debug=True)
