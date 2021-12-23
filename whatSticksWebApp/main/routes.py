from flask import Blueprint
from flask import render_template, url_for, redirect, flash, request, abort, session,\
    Response, current_app, send_from_directory
from whatSticksWebApp import db, bcrypt, mail
from whatSticksWebApp.models import Users, Posts, Health_descriptions, Polar_descriptions, Polar_measures,\
    Oura_sleep_descriptions, Oura_sleep_measures
from flask_login import login_user, current_user, logout_user, login_required
import secrets
import os
from datetime import datetime, date, time, timedelta
import datetime
from sqlalchemy import func, desc
import pandas as pd
import json
import zipfile
from whatSticksWebApp.main.utils import json_dict_to_dfs, plot_text_format, chart_scripts,\
    get_user_tz_util,format_duration
from bokeh.plotting import figure, output_file
from bokeh.embed import components
from bokeh.resources import CDN
from bokeh.io import curdoc
from bokeh.themes import built_in_themes
from bokeh.models import ColumnDataSource, Grid, LinearAxis, Plot, Text
import pytz
import zoneinfo
from pytz import timezone
import time
import requests
from whatSticksWebApp.main.utils_oura import link_oura
from whatSticksWebApp.main.utils_dashData import data_dfs, user_activity_list, polar_list,\
    oura_sleep_list, leading_zeros_count

main = Blueprint('main', __name__)
# from functools import wraps

from whatSticksWebApp.util_decorators import my_decorator3, nav_add_data




# @hello_decorator
@main.route("/about", methods=["GET","POST"])
@nav_add_data
def about(**kwargs):#<-- must have **kwargs with @nav_add_data
    default_date=kwargs.get('default_date')
    default_time=kwargs.get('default_time')
    return render_template('about.html',**kwargs)


@main.route("/dashboard", methods=["GET","POST"])
@nav_add_data
@login_required
def dashboard(**kwargs):
    default_date=kwargs['default_date']
    default_time=kwargs['default_time']
    df_health_descriptions,df_polar_descriptions,df_oura_sleep_descriptions = data_dfs()
    current_endpoint=request.url_rule.endpoint
    if len(df_polar_descriptions)>0:
        script1, div1=chart_scripts(df_polar_descriptions)
        cdn_js=CDN.js_files
        cdn_css=CDN.css_files
        #Timleline table columns
        column_names=['ID','Date and Time','Activity','Duration', 'Rating']
        #Timeline table list
        table_lists=user_activity_list(df_health_descriptions) + polar_list(df_polar_descriptions)+ \
            oura_sleep_list(df_oura_sleep_descriptions)
        no_hits_flag=True if len(table_lists)==0 else False
    else:
        #vars for chart that doesn't exist
        div1=None;script1=None;cdn_js=None;cdn_css=None
        #vars for dataframe that doesn't exist:
        table_lists=None;no_hits_flag=True;column_names=None
    if request.method == 'POST':
        formDict = request.form.to_dict()
        print('formDict::::',formDict)
        if formDict.get('submit_upload_health')=='True':
            return redirect(url_for('main.upload_health_data'))
        elif formDict.get('delete_record_id'):
            return redirect(url_for('main.delete_record',current_endpoint=current_endpoint,
                delete_record_id=formDict.get('delete_record_id')))
    return render_template('dashboard.html', div1=div1, script1=script1, cdn_js=cdn_js, cdn_css=cdn_css,
        default_date=default_date, default_time=default_time,table_data=table_lists,
        no_hits_flag=no_hits_flag,len=len,column_names=column_names)


@main.route("/for_scientists", methods=["GET","POST"])
@nav_add_data
@login_required
def for_scientists(**kwargs):
    default_date=kwargs['default_date']
    default_time=kwargs['default_time']
    df_health_descriptions,df_polar_descriptions,df_oura_sleep_descriptions = data_dfs()
    current_endpoint=request.url_rule.endpoint
    if len(df_polar_descriptions)>0:
        script1, div1=chart_scripts(df_polar_descriptions)
        cdn_js=CDN.js_files
        cdn_css=CDN.css_files
        #Timleline table columns
        column_names=['ID','Date and Time','Activity','Duration', 'Rating']
        #Timeline table list
        table_lists=user_activity_list(df_health_descriptions) + polar_list(df_polar_descriptions)+ \
            oura_sleep_list(df_oura_sleep_descriptions)
        no_hits_flag=True if len(table_lists)==0 else False
        print('no_hits_flag::', no_hits_flag)
    else:
        #vars for chart that doesn't exist
        div1=None;script1=None;cdn_js=None;cdn_css=None
        #vars for dataframe that doesn't exist:
        table_lists=None;no_hits_flag=True;column_names=None
        print('no_hits_flag::', no_hits_flag)
    if request.method == 'POST':
        formDict = request.form.to_dict()
        print('formDict::::',formDict)
        if formDict.get('submit_upload_health')=='True':
            return redirect(url_for('main.upload_health_data'))
        elif formDict.get('delete_record_id'):
            return redirect(url_for('main.delete_record',current_endpoint=current_endpoint,
                delete_record_id=formDict.get('delete_record_id')))
    return render_template('for_scientists.html', div1=div1, script1=script1, cdn_js=cdn_js, cdn_css=cdn_css,
        default_date=default_date, default_time=default_time, table_data=table_lists, no_hits_flag=no_hits_flag,
        len=len,column_names=column_names)


@main.route("/delete_record",methods=["GET","POST"])
@login_required
def delete_record(*args,**kwargs):
    delete_record_id=request.args.get('delete_record_id')
    previous_endpoint=request.args.get('current_endpoint')
    del_record_id_int=int(delete_record_id[-1*leading_zeros_count:])
    if current_user.username=="Guest":
        flash('Cannot delete to data as Guest','info')
        print('if current user is guest')
        return redirect(url_for(previous_endpoint))
    elif delete_record_id[:(-1*leading_zeros_count)]=='Polar ':
        db.session.query(Polar_descriptions).filter(Polar_descriptions.id==del_record_id_int).delete()
        db.session.query(Polar_measures).filter(Polar_measures.description_id==del_record_id_int).delete()
        db.session.commit()
    elif delete_record_id[:(-1*leading_zeros_count)]=='Oura Sleep ':
        db.session.query(Oura_sleep_descriptions).filter(Oura_sleep_descriptions.id==del_record_id_int).delete()
        db.session.query(Oura_sleep_measures).filter(Oura_sleep_measures.oura_sleep_description_id==del_record_id_int).delete()
        db.session.commit()
    return redirect(url_for('main.dashboard'))


@main.route("/add_weight",methods=["GET","POST"])
@login_required
def add_weight(**kwargs):
    where_r_we=request.args.get('where_r_we')
    weight=request.args.get('weight')
    user_tz = get_user_tz_util()
    #convert this date time to utc
    date_time_obj_unaware = datetime.datetime.strptime(request.args.get('activity_date')+request.args.get('activity_time'), '%Y-%m-%d%H:%M')
    date_time_obj_aware=user_tz.localize(date_time_obj_unaware)
    timezone_offset = date_time_obj_aware.utcoffset().total_seconds()/60
    
    update_weight=Health_descriptions(datetime_of_activity=date_time_obj_aware,var_activity='Weight',
        var_timezone_utc_delta_in_mins=timezone_offset, user_id=current_user.id,
        weight=weight)
    db.session.add(update_weight)
    db.session.commit()
    return redirect(url_for(where_r_we))

@main.route("/add_activity",methods=["GET","POST"])
@login_required
def add_activity(**kwargs):
    print('add_activity--requests:::',request.args)
    where_r_we=request.args.get('where_r_we')
    var_activity=request.args.get('var_activity')
    notes=request.args.get('notes')
    user_tz = get_user_tz_util()

    #convert this date time to utc
    date_time_obj_unaware = datetime.datetime.strptime(request.args.get('activity_date')+request.args.get('activity_time'), '%Y-%m-%d%H:%M')
    date_time_obj_aware=user_tz.localize(date_time_obj_unaware)
    timezone_offset = date_time_obj_aware.utcoffset().total_seconds()/60

    if not notes:
        # print('not activity_notes')
        update_activity=Health_descriptions(datetime_of_activity=date_time_obj_aware,
            var_timezone_utc_delta_in_mins=timezone_offset, user_id=current_user.id,
            var_activity=var_activity)
    else:
        update_activity=Health_descriptions(datetime_of_activity=date_time_obj_aware,
            var_timezone_utc_delta_in_mins=timezone_offset, user_id=current_user.id,
            var_activity=var_activity, note=notes)
    db.session.add(update_activity)
    db.session.commit()
    return redirect(url_for(where_r_we))
    #might need this:
    # return render_template('dashboard.html', div1=div1, script1=script1, cdn_js=cdn_js, cdn_css=cdn_css,
        # default_date=default_date, default_time=default_time)



@main.route("/upload health data", methods=["GET","POST"])
@nav_add_data
@login_required
def upload_health_data(**kwargs):

    if request.method == 'POST':
        print('POST method')
        formDict = request.form.to_dict()
        filesDict = request.files.to_dict()
        print('formDict:::', formDict)
        print('filesDict:::', filesDict)
        if current_user.username=='Guest':
            flash('Cannot add data as guest', 'warning')
            return redirect(url_for('main.upload_health_data'))

        elif formDict.get('upload_file_button'):
            print('upload_file_button accessed')
            # print(dir(filesDict.get('uploaded_file')))
            # print('filename:::',filesDict.get('uploaded_file').filename)
            if filesDict.get('uploaded_file').filename=='':
                flash(f'File not selected', 'warning')
                return redirect(url_for('main.upload_health_data'))

            print('upload button pressed')


            #save file
            uploaded_file = request.files['uploaded_file']
            current_files_dir=os.path.join(current_app.config['UPLOADED_FILES_FOLDER'])

            if not os.path.isdir(current_files_dir):
                os.makedirs(current_files_dir)
                print("created folder : ", current_files_dir)
            else:
                print(current_files_dir, "folder already exists.")

            uploaded_file.save(os.path.join(current_files_dir,uploaded_file.filename))

            #TODO: polar upload should be a utility of its own. Code should
            #look in json files and pull heart rate by second, distance and speed.
            #right now ***too much hard coded stuff in json_dict_to_df_dict***

            #get files to json dict
            polar_zip=zipfile.ZipFile(os.path.join(current_app.config[
                'UPLOADED_FILES_FOLDER'], uploaded_file.filename))

            polar_data_dict={}
            for i in polar_zip.filelist:
                polar_data_dict[i.filename]=json.loads(polar_zip.read(i.filename))

            #get files to df dict
            df_description,df_measure=json_dict_to_dfs(polar_data_dict)
            session_count=len(df_description)

            #put data into tables
            df_description.to_sql('polar_descriptions',db.engine, if_exists='append',index=False)
            df_measure.to_sql('polar_measures',db.engine, if_exists='append',index=False)

            flash(f'Successfully uploaded ' + str(session_count) +' Polar sessions', 'success')
            return redirect(url_for('main.upload_health_data'))

        elif formDict.get('connect_oura'):
            print('connect_oura accessed')
            personal_token=formDict.get('oura_token')
            user_id=current_user.id
            sleep_entries_count=link_oura(personal_token, user_id)
            flash(f'Successfully uploaded ' + str(sleep_entries_count) +' Oura sleep entries', 'success')
            return redirect(url_for('main.upload_health_data'))

    return render_template('upload_health_data.html', **kwargs)
