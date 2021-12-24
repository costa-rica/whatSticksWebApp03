from whatSticksWebApp import db
from whatSticksWebApp.models import Users, Posts, Health_descriptions,Polar_descriptions,\
    Polar_measures, Oura_sleep_descriptions, Oura_sleep_measures
# proxyApp=create_app()
# ctx=proxyApp.app_context()
# ctx.push()
import requests
import pandas as pd
import json
from sqlalchemy import func
from datetime import datetime, date, time, timedelta
import datetime

def link_oura(personal_token, user_id):
    url_sleep='https://api.ouraring.com/v1/sleep?start=2020-03-11&end=2020-03-21?'
    response_sleep = requests.get(url_sleep, headers={"Authorization": "Bearer " + personal_token})
    sleep_dict=response_sleep.json()

    #remove link between original api data
    Oura_sleep_descriptions_json=json.dumps(sleep_dict['sleep'])
    Oura_sleep_descriptions_dict_deep=json.loads(Oura_sleep_descriptions_json)
    #make two datasets for dataframes add corresponding ids
    Oura_sleep_measures_lists=[]

    #Get last Oura_sleep_description id
    max_id=db.session.query(func.max(Oura_sleep_descriptions.id)).first()[0]
    count=1 if max_id==None else max_id +1

    for i in Oura_sleep_descriptions_dict_deep:
        temp_dict={}
        temp_dict['hr_5min']=i['hr_5min']
        temp_dict['hypnogram_5min']=i['hypnogram_5min']
        temp_dict['rmssd_5min']=i['rmssd_5min']
        temp_dict['oura_sleep_description_id']=[str(count) for i in range(len(i['hr_5min']))]
        Oura_sleep_measures_lists.append(temp_dict)
        del i['hr_5min']
        del i['hypnogram_5min']
        del i['rmssd_5min']
        i['id']=str(count)
        i['user_id']=user_id
        count+=1

    #Combine sleep description data to one dataframe
    Oura_sleep_descriptions_df=pd.DataFrame()
    for i in Oura_sleep_descriptions_dict_deep:
        Oura_sleep_descriptions_df=Oura_sleep_descriptions_df.append(i,ignore_index=True)


    # Convert date columns to datetime
    Oura_sleep_descriptions_df['summary_date']=pd.to_datetime(Oura_sleep_descriptions_df['summary_date']).dt.date
    Oura_sleep_descriptions_df['bedtime_end']=pd.to_datetime(Oura_sleep_descriptions_df['bedtime_end'].str[:-6])
    Oura_sleep_descriptions_df['bedtime_start']=pd.to_datetime(Oura_sleep_descriptions_df['bedtime_start'].str[:-6])

    #get df of existing oura sleep
    existing_descriptions=pd.read_sql(db.session.query(Oura_sleep_descriptions).filter(Oura_sleep_descriptions.user_id == user_id).statement,db.session.bind) 
    #make list of bedtime_start string
    descript_exclude_list=list(existing_descriptions['bedtime_start'].astype(str))
    #remove existing sleep records (based on bedtime_start) from Oura_sleep_description_df
    Oura_sleep_descriptions_df['bedtime_start']=Oura_sleep_descriptions_df['bedtime_start'].dt.strftime('%Y-%m-%d %H:%M:%S')
    Oura_sleep_descriptions_df_upload=Oura_sleep_descriptions_df[~Oura_sleep_descriptions_df.bedtime_start.isin(descript_exclude_list)]
    #convert bedtime_start back to datetime64
    #Gets warnign but seems to be fine....
    Oura_sleep_descriptions_df_upload['bedtime_start']=pd.to_datetime(Oura_sleep_descriptions_df_upload['bedtime_start'])
    print(len(Oura_sleep_descriptions_df_upload))

    #combene sleep measures data to one dataframe
    Oura_sleep_measures_df=pd.DataFrame()
    for i in Oura_sleep_measures_lists:
        oura_sleep_descriptions_id=pd.DataFrame(i['oura_sleep_description_id'],columns=['oura_sleep_description_id'])
        hr_5min_df=pd.DataFrame(i['hr_5min'],columns=['hr_5min'])
        hypnogram_5min_df=pd.DataFrame(list(i['hypnogram_5min']),columns=['hypnogram_5min'])
        rmssd_5min_df=pd.DataFrame(i['rmssd_5min'],columns=['rmssd_5min'])
        Oura_sleep_measures_df_temp = pd.concat([oura_sleep_descriptions_id,hr_5min_df, hypnogram_5min_df, rmssd_5min_df], axis=1, join="outer")
        Oura_sleep_measures_df=Oura_sleep_measures_df.append(Oura_sleep_measures_df_temp,ignore_index=True)
    #Filter only the description_id's that have been kept by Oura_sleep_description_df_upload
    Oura_sleep_measures_df_upload=Oura_sleep_measures_df[Oura_sleep_measures_df.oura_sleep_description_id.isin(list(Oura_sleep_descriptions_df_upload.id))]
    print(len(Oura_sleep_measures_df_upload))

    Oura_sleep_descriptions_df_upload.to_sql('oura_sleep_descriptions',db.engine, if_exists='append',index=False)
    Oura_sleep_measures_df_upload.to_sql('oura_sleep_measures',db.engine, if_exists='append',index=False)

    return len(Oura_sleep_descriptions_df_upload)