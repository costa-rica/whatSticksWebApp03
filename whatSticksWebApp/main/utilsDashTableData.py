import json
import datetime
from datetime import timedelta
import os, zipfile
import pandas as pd
from flask_login import current_user
from whatSticksWebApp import db, bcrypt, mail
from whatSticksWebApp.models import Users, Posts, Health_descriptions, Polar_descriptions, Polar_measures,\
    Oura_sleep_descriptions, Oura_sleep_measures
from sqlalchemy import func
from scipy.optimize import curve_fit
import numpy as np

from bokeh.plotting import figure, output_file
from bokeh.embed import components
from bokeh.resources import CDN
from bokeh.io import curdoc
from bokeh.themes import built_in_themes, Theme
from bokeh.models import ColumnDataSource, Grid, LinearAxis, Plot, Text, Span
import pytz
import zoneinfo
from pytz import timezone
import time
from flask import current_app
from whatSticksWebApp.main.utils import plot_text_format, chart_scripts,\
    get_user_tz_util,format_duration
from whatSticksWebApp.main.utilsPolarUpload import json_dict_to_dfs

leading_zeros_count=5

def data_dfs():
    #filter on user data only
    base_query_health_descriptions=db.session.query(Health_descriptions).filter(Health_descriptions.user_id==1)#KEEP as 1, it gets replaced
    base_query_polar_descriptions=db.session.query(Polar_descriptions).filter(Polar_descriptions.user_id==1)#KEEP as 1, it gets replaced
    base_query_oura_sleep_descriptions=db.session.query(Oura_sleep_descriptions).filter(Oura_sleep_descriptions.user_id==1)#KEEP as 1, it gets replaced
    
    if current_user.id==2:
        df_health_descriptions=pd.read_sql(str(base_query_health_descriptions)[:-1]+str(1),db.session.bind)
        df_polar_descriptions=pd.read_sql(str(base_query_polar_descriptions)[:-1]+str(1),db.session.bind)
        df_oura_sleep_descriptions=pd.read_sql(str(base_query_oura_sleep_descriptions)[:-1]+str(1),db.session.bind)
    else:
        df_health_descriptions=pd.read_sql(str(base_query_health_descriptions)[:-1]+str(current_user.id),db.session.bind)
        df_polar_descriptions=pd.read_sql(str(base_query_polar_descriptions)[:-1]+str(current_user.id),db.session.bind)
        df_oura_sleep_descriptions=pd.read_sql(str(base_query_oura_sleep_descriptions)[:-1]+str(current_user.id),db.session.bind)
    
    df_dict={"df_health_descriptions":df_health_descriptions,"df_polar_descriptions":df_polar_descriptions,
            "df_oura_sleep_descriptions":df_oura_sleep_descriptions}
    
    
    # return (df_health_descriptions,df_polar_descriptions,df_oura_sleep_descriptions)
    return df_dict


def user_activity_list(df_health_descriptions):
    # print('df_health_descriptions columns names::::', df_health_descriptions.columns)
    if 'health_descriptions_id' in df_health_descriptions.columns:
        df_health_descriptions.rename(columns={i:i[len('health_descriptions_'):] for i in list(df_health_descriptions.columns)}, inplace=True)
    df_health_descriptions_sub=df_health_descriptions[['id', 'datetime_of_activity','var_activity','weight']].copy()
    # print('df_health_descriptions_sub:::', df_health_descriptions_sub.columns)
    # df_health_descriptions_sub.to_excel('df_health_descriptions_sub.xlsx')
    df_health_descriptions_sub.var_activity=df_health_descriptions_sub.apply(
        lambda row: 'weight '+ str(row['weight']) if not pd.isnull(row['weight']) else row['var_activity'], axis=1)
    df_health_descriptions_sub.datetime_of_activity=pd.to_datetime(df_health_descriptions_sub['datetime_of_activity'])
    df_health_descriptions_sub.weight=''
    df_health_descriptions_sub['extra_col']=''


    df_health_descriptions_sub.id=df_health_descriptions_sub.id.apply(lambda x: 'User Activity '+str(x).zfill(leading_zeros_count))
    return df_health_descriptions_sub.values.tolist()

def polar_list(df_polar_descriptions):
    
    if 'polar_descriptions_var_activity' in df_polar_descriptions.columns:
        df_polar_descriptions.rename(columns={i:i[len('polar_descriptions_'):] for i in list(df_polar_descriptions.columns)}, inplace=True)
    print('df_polar_descriptions::',df_polar_descriptions.columns)
    df_sub=df_polar_descriptions[['id', 'datetime_of_activity', 'var_activity',
                                    'metric2_session_duration','metric1_carido']].copy()
    df_sub.datetime_of_activity=df_sub['datetime_of_activity'].astype('datetime64[ns]')
    df_sub.datetime_of_activity=pd.to_datetime(df_sub["datetime_of_activity"].dt.strftime('%m/%d/%Y %H:%M'))
    df_sub.metric1_carido=df_sub.metric1_carido.round(2)
    df_sub=df_sub.where(pd.notnull(df_sub), '')
    df_sub.id=df_sub.id.apply(lambda x: 'Polar '+str(x).zfill(leading_zeros_count))
    df_sub.metric2_session_duration=df_sub.metric2_session_duration.apply(lambda x: format_duration(x))
    return df_sub.values.tolist()

def oura_sleep_list(df_oura_sleep_descriptions):
    if 'oura_sleep_descriptions_id' in df_oura_sleep_descriptions.columns:
        df_oura_sleep_descriptions.rename(columns={i:i[len('oura_sleep_descriptions_'):] for i in list(df_oura_sleep_descriptions.columns)}, inplace=True)
    df_sub_oura_sleep=df_oura_sleep_descriptions[['id', 'bedtime_start','duration','score_total']].copy()
    df_sub_oura_sleep.bedtime_start=pd.to_datetime(df_sub_oura_sleep['bedtime_start'])
    df_sub_oura_sleep=df_sub_oura_sleep.where(pd.notnull(df_sub_oura_sleep), '')
    df_sub_oura_sleep=df_sub_oura_sleep.sort_values(by=['bedtime_start'],ascending=False)

    df_sub_oura_sleep['activity']='Sleep'
    df_sub_oura_sleep=df_sub_oura_sleep[['id','bedtime_start', 'activity','duration', 'score_total']]

    df_sub_oura_sleep.id=df_sub_oura_sleep.id.apply(lambda x: 'Oura Sleep '+str(x).zfill(leading_zeros_count))
    df_sub_oura_sleep.duration=df_sub_oura_sleep.duration.apply(lambda x: format_duration(x))
    return df_sub_oura_sleep.values.tolist()