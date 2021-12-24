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


#The model set to max heartrate = 170
def michaelis_m_eq_fix170(time_var, shape_var):
    return (170 *time_var)/(shape_var + time_var)

def json_dict_to_dfs(polar_data_dict):

    df_descriptions=pd.DataFrame()
    df_measures=pd.DataFrame()
    max_id=db.session.query(func.max(Polar_descriptions.id)).first()[0]
    
    #TODO if lenghth is less than 140 then drop
    #Making two dataframes: df1 descripton of workout, df2 metrics, end of loop appends each to respective larger dfs
    for i,j in polar_data_dict.items():
        if 'training-session-' in i:
            #get last id from database
            max_id=1 if max_id==None else max_id +1
            df1=pd.DataFrame()
            
            df1['var_activity']=[j['exercises'][0]['sport']]#if one row, first should be in brackets or soemthing liek that
            df1['var_type']='heart rate'#must come from input data polar h1 only does heart rate
            df1['var_periodicity']='seconds' #must come from input data polar h1 only does seconds
            df1['var_timezone_utc_delta_in_mins']=j['exercises'][0]['timezoneOffset']
            df1['time_stamp_utc']=datetime.datetime.utcnow()
            df1['user_id']=current_user.id#comes from app current_user.id
            df1['source_filename']=i
            df1['description_id']=max_id
            df1['datetime_of_activity']=datetime.datetime.strptime(j['startTime'],'%Y-%m-%dT%H:%M:%S.%f')

            #if samples are empty insert row of na's
            if len(j['exercises'][0]['samples'])==0:
                df2=pd.DataFrame([j['startTime']],columns=['var_datetime_utc'])
                df2['description_id']=max_id
                df2['heart_rate']=np.nan
                df2['speed']=np.nan
                df2['distance']=np.nan
                df2['longitude']=np.nan
                df2['latitude']=np.nan
                df2['altitude']=np.nan
                
            else:
                var_datetime_utc_list=[]
                for data_item_series in j['exercises'][0]['samples']:
                    if data_item_series!='recordedRoute' and len(var_datetime_utc_list)==0:
                        var_datetime_utc_list=[datetime.datetime.strptime(
                            x['dateTime'],'%Y-%m-%dT%H:%M:%S.%f')+ timedelta(
                            minutes=j['exercises'][0]['timezoneOffset']) for x in j[
                            'exercises'][0]['samples'][data_item_series]]

                        df2=pd.DataFrame(var_datetime_utc_list,columns=['var_datetime_utc'])
                        df2['description_id']=max_id
                        reading_count=len(var_datetime_utc_list)
                    if data_item_series== 'heartRate':
                        df2['heart_rate']=[x['value'] for x in j['exercises'][0]['samples'][data_item_series]]
                    if data_item_series== 'speed':
                        df2['speed']= [x['value'] for x in j['exercises'][0]['samples'][data_item_series]]
                    if data_item_series== 'distance':
                        df2['distance']= [x['value'] for x in j['exercises'][0]['samples'][data_item_series]]
                    if data_item_series== 'recordedRoute':
                        longitude_list= [x['longitude'] for x in j['exercises'][0]['samples'][data_item_series]]
                        while reading_count>len(longitude_list):
                            longitude_list.append(longitude_list[-1])
                        df2['longitude']=longitude_list
                        latitude_list= [x['latitude'] for x in j['exercises'][0]['samples'][data_item_series]]
                        while reading_count>len(latitude_list):
                            latitude_list.append(latitude_list[-1])
                        df2['latitude']=latitude_list
                        altitude_list= [x['altitude'] for x in j['exercises'][0]['samples'][data_item_series]]
                        while reading_count>len(altitude_list):
                            altitude_list.append(altitude_list[-1])
                        df2['altitude']=altitude_list
                
                df1['metric2_session_duration']=reading_count
                
                df_descriptions=df_descriptions.append(df1, ignore_index = True)
                df_measures=df_measures.append(df2, ignore_index = True)
    df_descriptions.set_index('description_id', inplace=True)
    
    #calculate metric1_cardio
    metric1_list=[]
    for description_id in df_measures['description_id'].unique():
        df_byId=df_measures[df_measures.description_id==description_id]
        x_obs=df_byId.var_datetime_utc.to_list()
        if len(x_obs)>139:
            x_obs=[(i-x_obs[0]).total_seconds() for i in x_obs][:140]
            y_obs=df_byId.heart_rate.to_list()[:140]
            popt_fix170 = curve_fit(michaelis_m_eq_fix170, x_obs, y_obs,bounds=(0,np.inf))[0][0]
        else:
            popt_fix170=np.nan
        metric1_list.append(popt_fix170)

    #add metric1_cardio to df_description
    df_descriptions['metric1_carido']=metric1_list
    
    ####Check that same polar time stamps are not uploaded.
    #get existing database health_measure.description id and var_datetime_utc ***TODO Make this filter on user*****
    base_query_health_measures=db.session.query(Polar_measures.description_id,Polar_measures.var_datetime_utc)
    health_measures_var_datetime=pd.read_sql(str(base_query_health_measures),db.session.bind) 
    # health_measure_var_datetime.rename(columns={'health_measure_description_id':'description_id',
    #                                            'health_measure_var_datetime_utc':'var_datetime_utc'}, inplace=True)
    health_measures_var_datetime.rename(columns={i:i[len('polar_measures_'):] for i in health_measures_var_datetime.columns},
        inplace=True)

    if len(health_measures_var_datetime)>0:
        ##convert both var_datetime_utc columns to string
        df_measures_2=df_measures
        df_measures_2.var_datetime_utc=df_measures_2.var_datetime_utc.astype(str)    
        print('health_measure_var_datetime.columsn:::', health_measures_var_datetime.columns)
        # print('df_measure_2.coumns::',df_measure_2.columns)
        #check that var_datetime_utc variable/column is same length as in df_measure
        if len(health_measures_var_datetime.var_datetime_utc[0])>len(df_measures_2.var_datetime_utc[0]):
            cut_length=(len(health_measures_var_datetime.var_datetime_utc[0])-len(df_measures_2.var_datetime_utc[0]))*-1
            health_measures_var_datetime.var_datetime_utc=health_measures_var_datetime.var_datetime_utc.str[:cut_length]
        
        if len(df_measures_2.var_datetime_utc[0])>len(health_measures_var_datetime.var_datetime_utc[0]):
            cut_length=(len(df_measures_2.var_datetime_utc[0])-len(health_measures_var_datetime.var_datetime_utc[0]))*-1
            df_measures_2.var_datetime_utc=df_measures_2.var_datetime_utc.str[:cut_length]

        df_matching_times=pd.merge(df_measures_2, health_measures_var_datetime,on="var_datetime_utc")
        dup_descript_id_list=list(df_matching_times.description_id_x.unique())
        
        #overwrite upload dataframes with duplicate training sessions removed.
        df_measures=df_measures[~df_measures.description_id.isin(dup_descript_id_list)]
        df_descriptions=df_descriptions[~df_descriptions.index.isin(dup_descript_id_list)]
    
    return (df_descriptions,df_measures)