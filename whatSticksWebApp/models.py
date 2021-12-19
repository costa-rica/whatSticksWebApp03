from whatSticksWebApp import db, login_manager
from datetime import datetime, date
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from flask_login import UserMixin

from flask_script import Manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Text, unique=True)
    email = db.Column(db.Text, unique=True, nullable=False)
    image_file = db.Column(db.Text,nullable=False, default='default.jpg')
    password = db.Column(db.Text, nullable=False)
    user_timezone = db.Column(db.Text, default='US/Eastern')
    permission = db.Column(db.Text)
    theme = db.Column(db.Text)
    time_stamp = db.Column(db.DateTime, default=datetime.now)
    posts = db.relationship('Post', backref='author', lazy=True)
    health_data_polar = db.relationship('Health_description', backref='health_data_polar', lazy=True)
    health_data_oura_sleep = db.relationship('Oura_sleep_description', backref='health_data_oura_sleep', lazy=True)
    # track_inv = db.relationship('Tracking_inv', backref='updator_inv', lazy=True)


    def get_reset_token(self, expires_sec=1800):
        s=Serializer(current_app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s=Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return f"User('{self.id}', email:'{self.email}', permission:'{self.permission}', user_timezone: '{self.user_timezone}')"

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title= db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.now)
    content = db.Column(db.Text)
    screenshot = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Post('{self.title}','{self.date_posted}')"




class Health_description(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime_of_activity=db.Column(db.DateTime)
    var_activity = db.Column(db.Text) #walking, running, empty is ok for something like mood
    # var_type = db.Column(db.Text) #heart rate, mood, weight, etc.
    # var_periodicity = db.Column(db.Text)
    var_timezone_utc_delta_in_mins = db.Column(db.Float) #difference bewteen utc and timezone of exercise
    # time_stamp_utc = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id=db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # source_filename =db.Column(db.Text)
    source_name=db.Column(db.Text)
    source_notes=db.Column(db.Text)
    weight=db.Column(db.Float)
    # metric2_session_duration=db.Column(db.Float)
    # metric3=db.Column(db.Float)
    # metric4=db.Column(db.Float)
    # metric5=db.Column(db.Float)
    note=db.Column(db.Text)
    # posts = db.relationship('Post', backref='author', lazy=True)

    def __repr__(self):
        return f"Health_description('{self.id}',var_activity:'{self.var_activity}'," \
        f"'datetime_of_activity: '{self.datetime_of_activity}', note: {self.note}'," \
        f"' time_stamp_utc: '{self.time_stamp_utc}', source_name: '{self.source_name}')"




class Polar_description(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime_of_activity=db.Column(db.DateTime)
    var_activity = db.Column(db.Text) #walking, running, empty is ok for something like mood
    var_type = db.Column(db.Text) #heart rate
    var_periodicity = db.Column(db.Text)#seconds
    var_timezone_utc_delta_in_mins = db.Column(db.Float) #difference bewteen utc and timezone of exercise
    time_stamp_utc = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id=db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    source_filename =db.Column(db.Text)
    # source_name=db.Column(db.Text)
    # source_notes=db.Column(db.Text)
    metric1_carido=db.Column(db.Float)
    metric2_session_duration=db.Column(db.Float)
    metric3=db.Column(db.Float)
    # metric4=db.Column(db.Float)
    # metric5=db.Column(db.Float)
    note=db.Column(db.Text)
    # posts = db.relationship('Post', backref='author', lazy=True)

    def __repr__(self):
        return f"Polar_description('{self.id}',var_activity:'{self.var_activity}'," \
        f"'var_type: {self.var_type}', datetime_of_activity: '{self.datetime_of_activity}', time_stamp_utc: '{self.time_stamp_utc}')"



class Polar_measure(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description_id=db.Column(db.Integer, db.ForeignKey('health_description.id'), nullable=False)
    var_datetime_utc = db.Column(db.DateTime, nullable=True)
    var_value = db.Column(db.Text)
    var_unit = db.Column(db.Text)
    var_type = db.Column(db.Text)
    heart_rate = db.Column(db.Integer)
    speed=db.Column(db.Float)
    distance=db.Column(db.Float)
    longitude=db.Column(db.Float)
    latitude=db.Column(db.Float)
    altitude=db.Column(db.Float)

    def __repr__(self):
        return f"Polar_measure('{self.id}',description_id:'{self.description_id}'," \
        f"'var_datetime_utc: {self.var_datetime_utc}', var_value: '{self.var_value}')"

class Oura_sleep_description(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id=db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    summary_date = db.Column(db.Date)
    period_id = db.Column(db.Integer)
    is_longest = db.Column(db.Integer)
    timezone = db.Column(db.Integer)
    bedtime_end = db.Column(db.DateTime)
    bedtime_start = db.Column(db.DateTime)
    breath_average = db.Column(db.Float)
    duration = db.Column(db.Integer)
    total = db.Column(db.Integer)
    awake = db.Column(db.Integer)
    rem = db.Column(db.Integer)
    deep = db.Column(db.Integer)
    light = db.Column(db.Integer)
    midpoint_time = db.Column(db.Integer)
    efficiency = db.Column(db.Integer)
    restless = db.Column(db.Integer)
    onset_latency = db.Column(db.Integer)
    rmssd = db.Column(db.Integer)
    score = db.Column(db.Integer)
    score_alignment = db.Column(db.Integer)
    score_deep = db.Column(db.Integer)
    score_disturbances = db.Column(db.Integer)
    score_efficiency = db.Column(db.Integer)
    score_latency = db.Column(db.Integer)
    score_rem = db.Column(db.Integer)
    score_total = db.Column(db.Integer)
    temperature_deviation = db.Column(db.Float)
    bedtime_start_delta = db.Column(db.Integer)
    bedtime_end_delta = db.Column(db.Integer)
    midpoint_at_delta = db.Column(db.Integer)
    temperature_delta = db.Column(db.Float)
    hr_lowest = db.Column(db.Integer)
    hr_average = db.Column(db.Float)
    temperature_trend_deviation=db.Column(db.Float)
    measures = db.relationship('Oura_sleep_measures', backref='detailed_measures', lazy=True)

    def __repr__(self):
        return f"Oura_sleep_description('{self.id}',summary_date:'{self.summary_date}'," \
        f"'score: {self.score}', score_total: '{self.score_total}')," \
        f"'hr_lowest: {self.hr_lowest}', hr_average: '{self.hr_average}')," \
        f"'bedtime_start: {self.bedtime_start}', bedtime_end: '{self.bedtime_end}')," \
        f"'duration: {self.duration}', onset_latency: '{self.onset_latency}')"

class Oura_sleep_measures(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    oura_sleep_description_id = db.Column(db.Integer, db.ForeignKey('oura_sleep_description.id'), nullable=False)
    hr_5min = db.Column(db.Integer)
    hypnogram_5min = db.Column(db.Integer)
    rmssd_5min = db.Column(db.Integer)

    def __repr__(self):
        return f"Oura_sleep_measures('{self.id}',oura_sleep_description_id:'{self.oura_sleep_description_id}'"
