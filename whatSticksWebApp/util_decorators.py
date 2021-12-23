from functools import wraps
from whatSticksWebApp.main.utils import json_dict_to_dfs, plot_text_format, chart_scripts,\
    get_user_tz_util,format_duration
from datetime import datetime, date, time, timedelta
import datetime
import requests
from flask import render_template, url_for, redirect, flash, request, abort, session,\
    Response, current_app, send_from_directory
from flask_login import login_user, current_user, logout_user, login_required

def nav_add_data(function):
    @wraps(function)
    def wrapper(**kwargs):
        #these pass kwargs to current endpoint/page
        kwargs['user_tz'] = get_user_tz_util()
        kwargs['default_date']=datetime.datetime.now().astimezone(kwargs['user_tz']).strftime("%Y-%m-%d")
        kwargs['default_time']=datetime.datetime.now().astimezone(kwargs['user_tz']).strftime("%H:%M")
        kwargs['where_r_we']=request.url_rule.endpoint

        if request.method == 'POST':
            if current_user.username=='Guest':
                flash('Cannot add to data as Guest','info')
                print('if current user is guest')
                return redirect(url_for(kwargs['where_r_we']))
            formDict = request.form.to_dict()
            print('formDict in wrapper::::',formDict)
            #these params get passed to redirect endpoint:
            where_r_we=request.url_rule.endpoint
            activity_date=formDict.get('activity_date')
            activity_time=formDict.get('activity_time')

            if formDict.get('submit_activity'):
                #these params get passed to redirect endpoint:
                var_activity=formDict.get('var_activity')
                notes=formDict.get('activity_notes')
                return redirect(url_for('main.add_activity', activity_date=activity_date,activity_time=activity_time,
                    where_r_we=where_r_we, var_activity=var_activity, notes=notes))
            elif formDict.get('submit_weight'):
                #these params get passed to redirect endpoint:
                weight=formDict.get('weight_input')
                return redirect(url_for('main.add_weight', activity_date=activity_date,activity_time=activity_time,
                    where_r_we=where_r_we, weight=weight))
        print('reached end of wrapper***')
        return function(**kwargs)
    return wrapper



def my_decorator3(function):
    @wraps(function)
    def wrapper(**kwargs):
        print("wrapper running!")
        kwargs['user_tz'] = get_user_tz_util()
        kwargs['default_date']=datetime.datetime.now().astimezone(kwargs['user_tz']).strftime("%Y-%m-%d")
        kwargs['default_time']=datetime.datetime.now().astimezone(kwargs['user_tz']).strftime("%H:%M")
        kwargs['d']=8


        if request.method == 'POST':
            formDict = request.form.to_dict()
            print('formDict in wrapper::::',formDict)
            if formDict.get('submit_activity'):

                activity_date=formDict.get('activity_date')
                activity_time=formDict.get('activity_time')

                # activity_date_weight=formDict.get('activity_date_weight')
                # activity_time_weight=formDict.get('activity_time_weight')

                var_activity=formDict.get('var_activity')
                activity_notes=formDict.get('activity_notes')
                metric3=formDict.get('metric3_weight')

                return redirect(url_for('main.add_activity', activity_date=activity_date,activity_time=activity_time,
                    # activity_date_weight=activity_date_weight,activity_time_weight=activity_time_weight,
                    metric3=metric3,var_activity=var_activity, activity_notes=activity_notes))


        return function(**kwargs)
    
    return wrapper