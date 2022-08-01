from whatSticksWebApp import db, login_manager
from datetime import datetime, date
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from flask_login import UserMixin
from flask_script import Manager


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Text)
    email = db.Column(db.Text, unique=True, nullable=False)
    image_file = db.Column(db.Text,nullable=False, default='default.jpg')
    password = db.Column(db.Text, nullable=False)
    user_timezone = db.Column(db.Text, default='US/Eastern')
    permission = db.Column(db.Text)
    theme = db.Column(db.Text)
    gender=db.Column(db.Text)
    height_feet=db.Column(db.Integer)
    height_inches=db.Column(db.Integer)
    ethnicity=db.Column(db.Text)
    birthdate=db.Column(db.Date)
    oura_token=db.Column(db.Text)#Must add this****
    time_stamp = db.Column(db.DateTime, default=datetime.now)
    posts = db.relationship('Posts', backref='author', lazy=True)
    user_input = db.relationship('Health_descriptions', backref='user_input', lazy=True)
    polar = db.relationship('Polar_descriptions', backref='polar_descriptions', lazy=True)
    polar_m = db.relationship('Polar_measures', backref='polar_m', lazy=True)
    oura_sleep = db.relationship('Oura_sleep_descriptions', backref='Oura_sleep', lazy=True)
    oura_sleep_m = db.relationship('Oura_sleep_measures', backref='Oura_sleep_measures', lazy=True)
    weather = db.relationship('Weather_location', backref='Weather_location', lazy=True)
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
        return Users.query.get(user_id)

    def __repr__(self):
        return f"Users('{self.id}', email:'{self.email}', permission:'{self.permission}', user_timezone: '{self.user_timezone}')"

class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title= db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.now)
    content = db.Column(db.Text)
    screenshot = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __repr__(self):
        return f"Posts('{self.title}','{self.date_posted}')"

class Health_descriptions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime_of_activity=db.Column(db.DateTime)
    var_activity = db.Column(db.Text) #walking, running, empty is ok for something like mood
    var_timezone_utc_delta_in_mins = db.Column(db.Float) #difference bewteen utc and timezone of exercise
    user_id=db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    source_name=db.Column(db.Text)
    source_notes=db.Column(db.Text)
    weight=db.Column(db.Float)
    note=db.Column(db.Text)


    def __repr__(self):
        return f"Health_descriptions({self.id},var_activity:{self.var_activity}," \
        f"datetime_of_activity: {self.datetime_of_activity}, note: {self.note}," \
        f" var_timezone_utc_delta_in_mins: {self.var_timezone_utc_delta_in_mins}," \
        f"source_name: {self.source_name})"

class Polar_descriptions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime_of_activity=db.Column(db.DateTime)
    var_activity = db.Column(db.Text) #walking, running, empty is ok for something like mood
    var_type = db.Column(db.Text) #heart rate
    var_periodicity = db.Column(db.Text)#seconds
    var_timezone_utc_delta_in_mins = db.Column(db.Float) #difference bewteen utc and timezone of exercise
    time_stamp_utc = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id=db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    source_filename =db.Column(db.Text)
    metric1_carido=db.Column(db.Float)
    metric2_session_duration=db.Column(db.Float)
    metric3=db.Column(db.Float)
    note=db.Column(db.Text)
    polar_measures = db.relationship('Polar_measures', backref='polar_measures', lazy=True)

    def __repr__(self):
        return f"Polar_descriptions('{self.id}',var_activity:'{self.var_activity}'," \
        f"'var_type: {self.var_type}', datetime_of_activity: '{self.datetime_of_activity}', time_stamp_utc: '{self.time_stamp_utc}')"

class Polar_measures(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id=db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    description_id=db.Column(db.Integer, db.ForeignKey('polar_descriptions.id'), nullable=False)
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
        return f"Polar_measures('{self.id}',description_id:'{self.description_id}'," \
        f"'var_datetime_utc: {self.var_datetime_utc}', var_value: '{self.var_value}')"

class Oura_sleep_descriptions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id=db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
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
        return f"Oura_sleep_descriptions('{self.id}',summary_date:'{self.summary_date}'," \
        f"'score: {self.score}', score_total: '{self.score_total}')," \
        f"'hr_lowest: {self.hr_lowest}', hr_average: '{self.hr_average}')," \
        f"'bedtime_start: {self.bedtime_start}', bedtime_end: '{self.bedtime_end}')," \
        f"'duration: {self.duration}', onset_latency: '{self.onset_latency}')"

class Oura_sleep_measures(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id=db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    oura_sleep_description_id = db.Column(db.Integer, db.ForeignKey('oura_sleep_descriptions.id'), nullable=False)
    hr_5min = db.Column(db.Integer)
    hypnogram_5min = db.Column(db.Integer)
    rmssd_5min = db.Column(db.Integer)

    def __repr__(self):
        return f"Oura_sleep_measures('{self.id}',oura_sleep_description_id:'{self.oura_sleep_description_id}'"

class Weather_location(db.Model):

    id = db.Column(db.Integer, primary_key = True)
    user_id=db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    time_stamp_utc = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
# data collected from here: https://www.weatherapi.com/docs/
# Current Endpoint
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    city_location_name = db.Column(db.Text)
    region_name = db.Column(db.Text)
    country_name = db.Column(db.Text)
    tz_id = db.Column(db.Text)
    localtime_epoch = db.Column(db.Integer)
    localtime = db.Column(db.Text)

# Weather Alerts Endpoint
    headline = db.Column(db.Text)
    msgType = db.Column(db.Text)
    severity = db.Column(db.Text)
    urgency = db.Column(db.Text)
    areas = db.Column(db.Text)
    category = db.Column(db.Text)
    certainty = db.Column(db.Text)
    event = db.Column(db.Text)
    note = db.Column(db.Text)
    effective = db.Column(db.Text)
    expires = db.Column(db.Text)
    desc = db.Column(db.Text)
    instruction = db.Column(db.Text)

# Air Quality Endpoint
    co = db.Column(db.Float)# Carbon Monoxide (μg/m3)
    o3 = db.Column(db.Float)# Ozone (μg/m3)
    no2 = db.Column(db.Float)# Nitrogen dioxide (μg/m3)
    so2 = db.Column(db.Float)# Sulphur dioxide (μg/m3)
    pm2_5 = db.Column(db.Float)# PM2.5 (μg/m3)
    pm10 = db.Column(db.Float)# PM10 (μg/m3)
    us_epa_index = db.Column(db.Integer)#  	US - EPA standard. 
    gb_defra_index = db.Column(db.Integer)# UK Defra Index

# Realtime API i.e. this is the weather
    last_updated = db.Column(db.Text)
    last_updated_epoch = db.Column(db.Text)
    temp_c = db.Column(db.Float)
    temp_f = db.Column(db.Float)
    feelslike_c = db.Column(db.Float)
    feelslike_f = db.Column(db.Float)
    condition_text = db.Column(db.Text)
    condition_icon = db.Column(db.Text)
    condition_code = db.Column(db.Integer)
    wind_mph = db.Column(db.Float)
    wind_kph = db.Column(db.Float)
    wind_degree = db.Column(db.Integer)
    wind_dir = db.Column(db.String)
    pressure_mb = db.Column(db.Float)
    pressure_in = db.Column(db.Float)
    precip_mm = db.Column(db.Float)
    precip_in = db.Column(db.Float)
    humidity = db.Column(db.Integer)
    cloud = db.Column(db.Integer)
    is_day = db.Column(db.Integer)
    uv = db.Column(db.Float)
    gust_mph = db.Column(db.Float)
    gust_kph = db.Column(db.Float)

# Astronomy API
    sunrise = db.Column(db.Text)
    sunset = db.Column(db.Text)
    moonrise = db.Column(db.Text)
    moonset = db.Column(db.Text)
    moon_phase = db.Column(db.Text)
    moon_illumination = db.Column(db.Integer)

    note = db.Column(db.Text)
        
    def __repr__(self):
        return f"Weather_location(id: {self.id}, user_id: {self.user_id}, " \
            f"city_location_name: {self.city_location_name}, temp_c: {self.temp_c})"
