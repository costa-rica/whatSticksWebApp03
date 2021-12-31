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

def polar_chart_params(df_polar_descriptions):
    df_polar_descriptions.rename(columns={i:i[len('polar_descriptions_'):] for i in df_polar_descriptions.columns}, inplace=True)
    df1=df_polar_descriptions.loc[df_polar_descriptions.metric1_carido<100]
    df1=df1.sort_values(by=['datetime_of_activity'])
    obs_x1=[datetime.datetime.strptime(date_string,'%Y-%m-%d %H:%M:%S.%f') for date_string in df1.datetime_of_activity]
    obs_y1=df1.metric1_carido
    obs_y1_formatted=[ plot_text_format(i) for i in obs_y1]
    return [obs_x1,obs_y1,obs_y1_formatted]

def user_act_chart_params(df_health_descriptions):
    df_health_descriptions.rename(columns={i:i[len('health_descriptions_'):] for i in df_health_descriptions.columns}, inplace=True)
    df2=df_health_descriptions.loc[pd.isnull(df_health_descriptions.weight)]
    #1 time (obs_x)
    obs_x2=[ datetime.datetime.strptime(date_string,'%Y-%m-%d %H:%M:%S.%f') for date_string in df2.datetime_of_activity]
    #3 activity (obs_y2)
    obs_y2=df2.var_activity.to_list()
    return [obs_x2,obs_y2]

def user_wgt_chart_params(df_health_descriptions):
    df3=df_health_descriptions.loc[~pd.isnull(df_health_descriptions.weight)]
    obs_x3=[ datetime.datetime.strptime(date_string,'%Y-%m-%d %H:%M:%S.%f') for date_string in df3.datetime_of_activity]
    obs_y3=df3.weight
    obs_y3_formatted=[ plot_text_format(i) for i in obs_y3]
    return [obs_x3,obs_y3,obs_y3_formatted]

def oura_sleep_chart_params(df_oura_sleep_descriptions):
    df_oura_sleep_descriptions.rename(columns={i:i[len('oura_sleep_descriptions_'):] for i in df_oura_sleep_descriptions.columns}, inplace=True)
    bedtimes_start_list=[datetime.datetime.strptime(date_string,'%Y-%m-%d %H:%M:%S.%f') for date_string in df_oura_sleep_descriptions.bedtime_start]
    bedtimes_end_list=[datetime.datetime.strptime(date_string,'%Y-%m-%d %H:%M:%S.%f') for date_string in df_oura_sleep_descriptions.bedtime_end]
    obs_width4=[(b-a) for a,b in zip(bedtimes_start_list,bedtimes_end_list)]
    obs_x4=[a+b/2 for a,b in zip(bedtimes_start_list,obs_width4)]
    obs_y4=df_oura_sleep_descriptions.score_total
    obs_y4_formatted=[plot_text_format(i) for i in obs_y4]
    return [obs_x4, obs_y4,obs_y4_formatted, obs_width4]

def chart_bokeh_obj(chart_params_dict):
    fig1=figure(toolbar_location=None,tools='xwheel_zoom,xpan',active_scroll='xwheel_zoom',
            x_range=(chart_params_dict['chart'][0],chart_params_dict['chart'][1]),
            y_range=(-10,200),width=900, height=400)

    #add cardio_metric1
    circle=fig1.circle(chart_params_dict['polar'][0],chart_params_dict['polar'][1], legend_label="Cardio Performance", fill_color='#c77711', line_color=None,size=20)
    source1 = ColumnDataSource(dict(x=chart_params_dict['polar'][0], y=chart_params_dict['polar'][1], text=chart_params_dict['polar'][2]))
    glyph1 = Text(text="text",text_font_size={'value': '10px'},x_offset=-10, y_offset=5)
    fig1.add_glyph(source1, glyph1)
    print('chart_params_dict[user_act]')
    print(chart_params_dict['user_act'][0])
    if len(chart_params_dict['user_act'][0])>0:
        #add user activity vertical lines
        for a,b in zip(chart_params_dict['user_act'][0],chart_params_dict['user_act'][1]):
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
        #--End formatting lines---


    #Add weight circles
    circle3=fig1.circle(chart_params_dict['user_wgt'][0],chart_params_dict['user_wgt'][1], legend_label="Weight",
        fill_color='#ebebeb', line_color=None,size=20)
    source3 = ColumnDataSource(dict(x=chart_params_dict['user_wgt'][0], y=chart_params_dict['user_wgt'][1], 
        text=chart_params_dict['user_wgt'][2]))
    glyph3 = Text(text="text",text_font_size={'value': '10px'},x_offset=-10, y_offset=5)
    fig1.add_glyph(source3, glyph3)

    #sleep rectangle
    oura_sleep_rect=fig1.rect(chart_params_dict['oura_sleep'][0], chart_params_dict['oura_sleep'][1],
        chart_params_dict['oura_sleep'][3], 5, fill_color="#888000", line_color="#444")
    #sleep rectangle label
    source4 = ColumnDataSource(dict(x=chart_params_dict['oura_sleep'][0], y=chart_params_dict['oura_sleep'][1],
        text=chart_params_dict['oura_sleep'][2]))
    glyph4 = Text(text="text",text_font_size={'value': '10px'},x_offset=-10, y_offset=5)
    fig1.add_glyph(source4, glyph4)

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