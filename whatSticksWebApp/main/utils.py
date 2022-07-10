import json
import datetime
from datetime import timedelta
import os, zipfile
import pandas as pd
from flask_login import current_user
from whatSticksWebApp import db, bcrypt, mail
from whatSticksWebApp.models import Users, Posts, Health_descriptions, Polar_descriptions, Polar_measures
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

def plot_text_format(x):
    return ('%.1f' % x).rstrip('0').rstrip('.')


def get_user_tz_util():
    print('current_user')
    print(dir(current_user))
    print(current_user.get_id())
    user_record=db.session.query(Users).filter(Users.id==current_user.id).first()
    user_tz=user_record.user_timezone
    user_tz = timezone(user_tz)
    return user_tz

def format_duration(duration):
    if duration>=3600:
        h,m=divmod(duration/60,60)
        return str(round(h))+" hrs "+str(round(m))+" mins"
    else:
        m,s=divmod(duration,60)
        return str(round(m))+" mins "+str(round(s))+" seconds"


def chart_scripts(df_health_descriptions):
    #clean df
    colNames=[i[len('health_description_'):] for i in list(df_health_descriptions.columns)]
    col_names_dict={i:j for i,j in zip(list(df_health_descriptions.columns),colNames)}
    df_health_descriptions.rename(columns=col_names_dict, inplace=True)
    df1=df_health_descriptions.sort_values(by=['datetime_of_activity'])

    
    #assign default chart dates
    # date_end=datetime.datetime.strptime(df1.datetime_of_activity.to_list()[-1],'%Y-%m-%d %H:%M:%S.%f')
    date_end=datetime.datetime.strptime(df_health_descriptions.datetime_of_activity.max(),
        '%Y-%m-%d %H:%M:%S.%f')+ timedelta(days=1)
    date_start=date_end- timedelta(days=7)
    
    
    #get cardio performance metric into lists
    df1=df_health_descriptions.loc[df_health_descriptions.metric1_carido<100]#filter dataset
    obs_x1=[ datetime.datetime.strptime(date_string,'%Y-%m-%d %H:%M:%S.%f') for date_string in df1.datetime_of_activity]
    if len(df1)>0:
        obs_y1=df1.metric1_carido
        obs_y1_formatted=[ plot_text_format(i) for i in obs_y1]


    #get activities into lists
    df2=df_health_descriptions.loc[(df_health_descriptions.var_type=='Activity')]#filter dataset
    obs_x2=[ datetime.datetime.strptime(date_string,'%Y-%m-%d %H:%M:%S.%f') for date_string in df2.datetime_of_activity]
    if len(df2)>0:
        obs_y2=df2.var_activity.to_list()

        
    #get weights into lists
    df3=df_health_descriptions.loc[(df_health_descriptions.var_type=='Weight')]#filter dataset

    obs_x3=[ datetime.datetime.strptime(date_string,'%Y-%m-%d %H:%M:%S.%f') for date_string in df3.datetime_of_activity]
    if len(df3)>0:
        obs_y3=df3.metric3.to_list()
        obs_y3_min=min(obs_y3)
        obs_y3_adjusted=[i-obs_y3_min+10 for i in obs_y3]
    
    #create figure object [start of jupyter notebook]
    fig1=figure(toolbar_location=None,tools='xwheel_zoom,xpan',active_scroll='xwheel_zoom',
                x_range=(date_start,date_end),y_range=(-10,90),width=900, height=400)

    #add cardio_metric1
    if len(obs_x1)>0:
        circle=fig1.circle(obs_x1,obs_y1, legend_label="Cardio Performance", fill_color='#c77711', line_color=None,
                      size=20)
        source1 = ColumnDataSource(dict(x=obs_x1, y=obs_y1, text=obs_y1_formatted))
        glyph1 = Text(text="text",text_font_size={'value': '10px'},x_offset=-10, y_offset=5)
        fig1.add_glyph(source1, glyph1)

    #add activities to fig1
    if len(obs_x2)>0:
        for a,b in zip(obs_x2,obs_y2):
            #add activity data
            source2 = ColumnDataSource(dict(x=[a], y=[80], text=[b]))
            glyph2 = Text(text="text", text_color="#414444", text_font_size={'value': '10px'},
                         x_offset=-10,angle=-1.58)
            
            #add line for activity data
            line_start_time=time.mktime(a.timetuple())*1000
            important_time = Span(location=line_start_time, dimension='height', line_color="#414444", line_dash='dashed', line_width=1)
            fig1.add_glyph(source2, glyph2)
            fig1.add_layout(important_time)

        fig1.add_glyph(source2, glyph2)

    #add weight as triangles
    if len(obs_x3)>0:
        triangle=fig1.triangle(obs_x3,obs_y3_adjusted, legend_label="Weight", fill_color='#c77711', line_color=None,
                      size=20)
        source3 = ColumnDataSource(dict(x=obs_x3, y=obs_y3_adjusted, text=obs_y3))
        glyph3 = Text(text="text",text_font_size={'value': '10px'},x_offset=-10, y_offset=5)
        fig1.add_glyph(source3, glyph3)


    fig1.ygrid.grid_line_color = None
    fig1.yaxis.major_label_text_color = None
    fig1.yaxis.major_tick_line_color = None
    fig1.yaxis.minor_tick_line_color = None

    fig1.legend.background_fill_color = "#578582"
    fig1.legend.background_fill_alpha = 0.2
    fig1.legend.border_line_color = None
    
    theme_1=curdoc().theme = Theme(filename=current_app.config['BOKEH_THEME'])

    script1, div1 = components(fig1, theme=theme_1)

    return (script1, div1)


# current_app.config['BOKEH_THEME'])



