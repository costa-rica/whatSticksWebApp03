import json
import datetime
from datetime import timedelta
import os, zipfile
import pandas as pd
from flask_login import current_user
from whatSticksWebApp import db, bcrypt, mail
from whatSticksWebApp.models import Users, Posts, Health_descriptions, Polar_descriptions,\
     Polar_measures, Oura_sleep_descriptions
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


def heart_org_excel(age):
    wsh_home_dir=current_app.config['WSH_HOME_DIR']
    heart_excel_path=os.path.join(current_app.config['WSH_HOME_DIR'],'heart_org_data.xlsx')
    heart_df=pd.read_excel(heart_excel_path)
    bpm_50=heart_df.loc[heart_df.Age>=age,'50_bpm'].min()
    bpm_85=heart_df.loc[heart_df.Age>=age,'85_bpm'].min()
    return (bpm_50, bpm_85)

def user_current_age():
    bday=Users.query.filter_by(id=1).with_entities(Users.birthdate).first()[0]
    today=datetime.date.today()
    age=today-bday
    age=int(age.days/365)
    return age

#user_hr_list, include dashed lines bool, units for chart
def polar_bar_chart_dash():
    current_user_id= current_user.id if current_user.username!="Guest" else 1
    user_hr_list=[i[0] for i in Polar_measures.query.filter_by(user_id=current_user_id).with_entities(Polar_measures.heart_rate).all()]
    user_polar_hr_avg=int(sum(user_hr_list)/len(user_hr_list))
    wsh_community_avg=user_polar_hr_avg-5

    user_x_label=current_user.username
    peer_x_label='Peer Group'

    x_axis_list=[user_x_label, peer_x_label]
    hr_list=[user_polar_hr_avg,wsh_community_avg]

    label_note=' bpm'
    text_font_size_wsh='14px'

    #get user age from database
    user_age=user_current_age()

    #labels for each bar
    source_user_avg_hr = ColumnDataSource(dict(x=[user_x_label], y=[user_polar_hr_avg+2], text=[str(user_polar_hr_avg)+label_note]))
    glyph_user_avg_hr = Text(text="text", text_color="#414444", text_font_size={'value': text_font_size_wsh},
                x_offset=-40,angle=0)

    source_wsh_community_avg = ColumnDataSource(dict(x=[peer_x_label], y=[wsh_community_avg+2], text=[str(wsh_community_avg)+label_note]))
    glyph_wsh_community_avg = Text(text="text", text_color="#414444", text_font_size={'value': text_font_size_wsh},
                x_offset=-40,angle=0)

    #get corresponding heart.org 50 and 85% thresholds
    bpm_50, bpm_85=heart_org_excel(user_age)

    text_detail_dashed_lines=f"""
    Bottom dashed line is {bpm_50} beats per minute (bpm), which is 50% of your peer group. Top dashed line is
    {bpm_85} bpm, which is 85% exertion of your peer group.
    """

    #horizaontal line 50% based on user age
    hline_50pct_bpm = Span(location=bpm_50, dimension='width', line_color='gray', line_width=1, line_dash='dashed')
    # source_50pct_bpm = ColumnDataSource(dict(x=[''], y=[bpm_50+2], text=[str(bpm_50)+f" bpm - 50%"]))
    # glyph_50pct_bpm = Text(text="text", text_color="#414444", text_font_size={'value': text_font_size_wsh},
    #             x_offset=-100,angle=0)
    
    #horizaontal line 85% based on user age
    hline_85pct_bpm = Span(location=bpm_85, dimension='width', line_color='gray', line_width=1, line_dash='dashed')
    # source_85pct_bpm = ColumnDataSource(dict(x=[''], y=[bpm_85+2], text=[str(bpm_85)+f" bpm - 85%"]))
    # glyph_85pct_bpm = Text(text="text", text_color="#414444", text_font_size={'value': text_font_size_wsh},
    #             x_offset=-100,angle=0)

    #make list of dashed lines and bar chart values
    values_list=[user_polar_hr_avg, wsh_community_avg, bpm_50, bpm_85]
    chart_max_height=max(values_list)+10



    fig1 = figure(x_range=x_axis_list,
         height=400,
        #  width=800,
         sizing_mode='stretch_width',
         toolbar_location=None, tools="",
        y_range=(0,chart_max_height), 
        # sizing_mode = 'stretch_both', tools = 'pan', id = "blue_fig"
        )

    fig1.vbar(x=x_axis_list, top=hr_list, width=.7)

    fig1.xgrid.grid_line_color = None
    fig1.y_range.start = 0

    fig1.add_glyph(source_user_avg_hr, glyph_user_avg_hr)
    fig1.add_glyph(source_wsh_community_avg, glyph_wsh_community_avg)

    fig1.renderers.extend([hline_50pct_bpm])
    # fig1.add_glyph(source_50pct_bpm, glyph_50pct_bpm)
    fig1.renderers.extend([hline_85pct_bpm])
    # fig1.add_glyph(source_85pct_bpm, glyph_85pct_bpm)

    #standard wsh chart formatting
    fig1.ygrid.grid_line_color = None
    fig1.yaxis.major_label_text_color = None
    fig1.yaxis.major_tick_line_color = None
    fig1.yaxis.minor_tick_line_color = None

    #specific to this chart formatting
    fig1.xaxis.major_tick_line_color = None
    fig1.xaxis.major_label_text_font_size  = text_font_size_wsh

    # fig1.responsive = True

    theme_1=curdoc().theme = Theme(filename=current_app.config['BOKEH_THEME'])
    script1, div1 = components(fig1, theme=theme_1)
    return (script1, div1, text_detail_dashed_lines)



def oura_sleep_bar_chart_dash():
    current_user_id= current_user.id if current_user.username!="Guest" else 1
    user_sleep_durations_list=[i[0] for i in Oura_sleep_descriptions.query.filter_by(user_id=current_user_id).with_entities(Oura_sleep_descriptions.duration).all()]
    user_sleep_duration_avg_seconds=int(sum(user_sleep_durations_list)/len(user_sleep_durations_list))
    user_sleep_duration_avg_hours=round(user_sleep_duration_avg_seconds/60/60,2)
    wsh_community_avg=round(user_sleep_duration_avg_hours-1,2)

    user_x_label=current_user.username
    peer_x_label='Peer Group'

    x_axis_list=[user_x_label, peer_x_label]
    sleep_durations_xaxis_list=[user_sleep_duration_avg_hours,wsh_community_avg]

    label_note=' hours'
    text_font_size_wsh='14px'

    #get user age from database
    user_age=user_current_age()

    chart_label_buffer=1

    #labels for each bar
    source_user_avg_hr = ColumnDataSource(dict(x=[user_x_label], y=[user_sleep_duration_avg_hours+chart_label_buffer],
        text=[str(user_sleep_duration_avg_hours)+label_note]))
    glyph_user_avg_hr = Text(text="text", text_color="#414444", text_font_size={'value': text_font_size_wsh},
                x_offset=-40,angle=0)

    source_wsh_community_avg = ColumnDataSource(dict(x=[peer_x_label], y=[wsh_community_avg+chart_label_buffer], text=[str(wsh_community_avg)+label_note]))
    glyph_wsh_community_avg = Text(text="text", text_color="#414444", text_font_size={'value': text_font_size_wsh},
                x_offset=-40,angle=0)

    #get corresponding heart.org 50 and 85% thresholds
    # bpm_50, bpm_85=heart_org_excel(user_age)
    bpm_50, bpm_85=(4.5, 9)

    text_detail_dashed_lines=f"""
    Bottom dashed line is {bpm_50} beats per minute (bpm), which is 50% of your peer group. Top dashed line is
    {bpm_85} bpm, which is 85% exertion of your peer group.
    """

    #horizaontal line 50% based on user age
    hline_50pct_bpm = Span(location=bpm_50, dimension='width', line_color='gray', line_width=1, line_dash='dashed')
    # source_50pct_bpm = ColumnDataSource(dict(x=[''], y=[bpm_50+2], text=[str(bpm_50)+f" bpm - 50%"]))
    # glyph_50pct_bpm = Text(text="text", text_color="#414444", text_font_size={'value': text_font_size_wsh},
    #             x_offset=-100,angle=0)
    
    #horizaontal line 85% based on user age
    hline_85pct_bpm = Span(location=bpm_85, dimension='width', line_color='gray', line_width=1, line_dash='dashed')
    # source_85pct_bpm = ColumnDataSource(dict(x=[''], y=[bpm_85+2], text=[str(bpm_85)+f" bpm - 85%"]))
    # glyph_85pct_bpm = Text(text="text", text_color="#414444", text_font_size={'value': text_font_size_wsh},
    #             x_offset=-100,angle=0)

    #make list of dashed lines and bar chart values
    values_list=[user_sleep_duration_avg_hours, wsh_community_avg, bpm_50, bpm_85]
    chart_max_height=max(values_list)+3



    fig1 = figure(x_range=x_axis_list, height=400, sizing_mode='stretch_width',toolbar_location=None, tools="",
        y_range=(0,chart_max_height))

    fig1.vbar(x=x_axis_list, top=sleep_durations_xaxis_list, width=.7)

    fig1.xgrid.grid_line_color = None
    fig1.y_range.start = 0

    fig1.add_glyph(source_user_avg_hr, glyph_user_avg_hr)
    fig1.add_glyph(source_wsh_community_avg, glyph_wsh_community_avg)

    fig1.renderers.extend([hline_50pct_bpm])
    # fig1.add_glyph(source_50pct_bpm, glyph_50pct_bpm)
    fig1.renderers.extend([hline_85pct_bpm])
    # fig1.add_glyph(source_85pct_bpm, glyph_85pct_bpm)

    #standard wsh chart formatting
    fig1.ygrid.grid_line_color = None
    fig1.yaxis.major_label_text_color = None
    fig1.yaxis.major_tick_line_color = None
    fig1.yaxis.minor_tick_line_color = None

    #specific to this chart formatting
    fig1.xaxis.major_tick_line_color = None
    fig1.xaxis.major_label_text_font_size  = text_font_size_wsh

    theme_1=curdoc().theme = Theme(filename=current_app.config['BOKEH_THEME'])
    script1, div1 = components(fig1, theme=theme_1)
    return (script1, div1, text_detail_dashed_lines)