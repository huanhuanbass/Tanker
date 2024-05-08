import streamlit as st
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from datetime import date
from datetime import timedelta
import numpy as np
from ta.volatility import BollingerBands
from ta.trend import SMAIndicator
from pandas.tseries.offsets import BDay
import requests

import plotly.graph_objects as go

draft_template = go.layout.Template()
draft_template.layout.annotations = [
    dict(
        name="draft watermark",
        text="COFCO Internal Use Only",
        textangle=0,
        opacity=0.1,
        font=dict(color="black", size=70),
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
    )
]


cutoff = pd.to_datetime('today')
curryear=cutoff.year

plot_ticks='inside'
plot_tickwidth=2
plot_ticklen=10
plot_title_font_color='dodgerblue'
plot_title_font_size=25
plot_legend_font_size=15
plot_axis=dict(tickfont = dict(size=15))


#Getting Tanker Data
st.text('----Getting Tanker Data...')
@st.cache_data()
def load_tanker_asset_price_data():

    headers = {'x-apikey': 'FMNNXJKJMSV6PE4YA36EOAAJXX1WAH84KSWNU8PEUFGRHUPJZA3QTG1FLE09SXJF'}
    dateto=pd.to_datetime('today')
    datefrom=dateto-BDay(30)
    params={'from':datefrom,'to':dateto}
    url2hvlcc='https://api.balticexchange.com/api/v1.3/feed/FDSWA4V8GN1E6KA1WMQBZL1GX44M62C2/data'
    url2hsuez='https://api.balticexchange.com/api/v1.3/feed/FDSWK35XQX8APGHHZ6CXGJF4F0FJN9F9/data'
    url2hafra='https://api.balticexchange.com/api/v1.3/feed/FDSJBNK8SWRFDFZSBJFT8882Z0T78QUX/data'
    urlnbvlcc='https://api.balticexchange.com/api/v1.3/feed/FDSFV2KEXYIRK5HL3HIHU41P8V6VTU4S/data'
    urlnbsuez='https://api.balticexchange.com/api/v1.3/feed/FDSGNYDXBV44957WV78ZAJXDYMFQXHA5/data'
    urlnbafra='https://api.balticexchange.com/api/v1.3/feed/FDSYVD3ZL6GDX2VOMV932MX85SKHPRBT/data'

    response = requests.get(url2hvlcc, headers=headers,params=params)
    df=pd.DataFrame(response.json())
    vlcc2h=pd.DataFrame(df.loc[0,'data'])
    vlcc2h.set_index('date',inplace=True)
    vlcc2h.rename(columns={'value':'VLCC 5yr'},inplace=True)

    response = requests.get(url2hsuez, headers=headers,params=params)
    df=pd.DataFrame(response.json())
    suez2h=pd.DataFrame(df.loc[0,'data'])
    suez2h.set_index('date',inplace=True)
    suez2h.rename(columns={'value':'Suezmax 5yr'},inplace=True)

    response = requests.get(url2hafra, headers=headers,params=params)
    df=pd.DataFrame(response.json())
    afra2h=pd.DataFrame(df.loc[0,'data'])
    afra2h.set_index('date',inplace=True)
    afra2h.rename(columns={'value':'Aframax 5yr'},inplace=True)

    response = requests.get(urlnbvlcc, headers=headers,params=params)
    df=pd.DataFrame(response.json())
    vlccnb=pd.DataFrame(df.loc[0,'data'])
    vlccnb.set_index('date',inplace=True)
    vlccnb['value']=vlccnb['value']
    vlccnb.rename(columns={'value':'VLCC NB'},inplace=True)

    response = requests.get(urlnbsuez, headers=headers,params=params)
    df=pd.DataFrame(response.json())
    sueznb=pd.DataFrame(df.loc[0,'data'])
    sueznb.set_index('date',inplace=True)
    sueznb['value']=sueznb['value']
    sueznb.rename(columns={'value':'Suezmax NB'},inplace=True)

    response = requests.get(urlnbafra, headers=headers,params=params)
    df=pd.DataFrame(response.json())
    afranb=pd.DataFrame(df.loc[0,'data'])
    afranb.set_index('date',inplace=True)
    afranb['value']=afranb['value']
    afranb.rename(columns={'value':'Aframax NB'},inplace=True)

    assetprice=pd.merge(vlcc2h,suez2h,left_index=True,right_index=True,how='outer')
    assetprice=pd.merge(assetprice,afra2h,left_index=True,right_index=True,how='outer')
    assetprice=pd.merge(assetprice,vlccnb,left_index=True,right_index=True,how='outer')
    assetprice=pd.merge(assetprice,sueznb,left_index=True,right_index=True,how='outer')
    assetprice=pd.merge(assetprice,afranb,left_index=True,right_index=True,how='outer')
    assetprice.index=pd.to_datetime(assetprice.index)
    assetprice.index=assetprice.index.date

    hist=pd.read_csv('tankerhist.csv')
    hist.set_index('Date',inplace=True)
    hist.index=pd.to_datetime(hist.index)
    hist.index=hist.index.date

    all=pd.concat([hist,assetprice])
    all=all[~all.index.duplicated(keep='last')]
    all.fillna(method='ffill',inplace=True)
    all.to_csv('tankerhist.csv',index_label='Date')

    print('done')

    return all


tankerasset=load_tanker_asset_price_data()


if 'tankerasset' not in st.session_state:
    st.session_state['tankerasset']=tankerasset


#Getting Tanker Spot Freight Data
@st.cache_data()
def load_tanker_spot_data():
    headers = {'x-apikey': 'FMNNXJKJMSV6PE4YA36EOAAJXX1WAH84KSWNU8PEUFGRHUPJZA3QTG1FLE09SXJF'}
    dateto=pd.to_datetime('today')
    datefrom=dateto-BDay(15)
    params={'from':datefrom,'to':dateto}
    urlvlcc='https://api.balticexchange.com/api/v1.3/feed/FDSGRNWAV2CX1ICOE2RXSFNC9J2INIWX/data'
    urlsuez='https://api.balticexchange.com/api/v1.3/feed/FDSE8I1ABJ6C8DNXE7D4A8V3OQODKGIV/data'
    urlafra='https://api.balticexchange.com/api/v1.3/feed/FDSNWMGPS29LODSVUTCAP4MYNNKA30S4/data'

    response = requests.get(urlvlcc, headers=headers,params=params)
    df=pd.DataFrame(response.json())
    spotvlcc=pd.DataFrame(df.loc[0,'data'])
    spotvlcc.set_index('date',inplace=True)
    spotvlcc.rename(columns={'value':'VLCC'},inplace=True)

    response = requests.get(urlsuez, headers=headers,params=params)
    df=pd.DataFrame(response.json())
    spotsuez=pd.DataFrame(df.loc[0,'data'])
    spotsuez.set_index('date',inplace=True)
    spotsuez.rename(columns={'value':'Suezmax'},inplace=True)

    response = requests.get(urlafra, headers=headers,params=params)
    df=pd.DataFrame(response.json())
    spotafra=pd.DataFrame(df.loc[0,'data'])
    spotafra.set_index('date',inplace=True)
    spotafra.rename(columns={'value':'Aframax'},inplace=True)

    spotnew=pd.merge(spotvlcc,spotsuez,left_index=True,right_index=True,how='outer')
    spotnew=pd.merge(spotnew,spotafra,left_index=True,right_index=True,how='outer')
    spotnew.index=pd.to_datetime(spotnew.index)

    spot=pd.read_csv('tankerspot.csv')
    spotold=spot.set_index('Date')
    spotold.index=pd.to_datetime(spotold.index)

    st.text('Spot Data Before Update: '+str(spotold.index.date[-1]))

    spot=pd.concat([spotold,spotnew])
    spot.reset_index(inplace=True)
    spot.rename(columns={'index':'Date'},inplace=True)
    spot=spot.drop_duplicates()
    spot.set_index('Date',inplace=True)
    spot=spot.dropna(subset=['VLCC'])

    st.text('Spot Data After Update: '+str(spot.index.date[-1]))

    spot.to_csv('tankerspot.csv',index_label='Date')

    return spot

tankerspot=load_tanker_spot_data()

if 'tankerspot' not in st.session_state:
    st.session_state['tankerspot']=tankerspot

st.text('Tanker Data Done!')




st.title('Tanker')
st.text('Dry Bulk Freight (Tanker) Interactive Dashboard')

st.markdown('## **Dirty Tanker Spot Price**')
spot=st.session_state['tankerspot']

sl=st.multiselect('Select Segment',options=['VLCC','Suezmax','Aframax'],default=['VLCC','Suezmax','Aframax'],key='sl')
sprangelist=st.selectbox('Select Range',options=['Last Year to Date','Year to Date','Month to Date','All'],key='spsl')

today = pd.to_datetime('today')
if sprangelist=='Last Year to Date':
    sprangestart=date(today.year-1,1,1)
elif sprangelist=='Month to Date':
    sprangestart=date(today.year,today.month,1)
elif sprangelist=='Year to Date':
    sprangestart=date(today.year,1,1)
else:
    sprangestart=date(2015,1,1)

spotsl=spot[sl]
spotsl=spotsl[spotsl.index>=pd.to_datetime(sprangestart)]

figspot=px.line(spotsl,width=1000,height=500,title='Dirty Tanker Spot Price')
figspot.update_xaxes(ticks=plot_ticks, tickwidth=plot_tickwidth,  ticklen=plot_ticklen)
figspot.update_layout(title_font_color=plot_title_font_color,title_font_size=plot_title_font_size,legend_font_size=plot_legend_font_size,xaxis=plot_axis,yaxis=plot_axis)
figspot.update_layout(template=draft_template)
st.plotly_chart(figspot)


st.markdown('## **Dirty Tanker Spot Price Seasonality**')
contractlist_r=st.selectbox('Select Segment',options=list(spot.columns),key='211')
freq=st.radio('Select Frequency',options=['Daily','Weekly','Monthly','Quarterly'],key='spotfreq')
spotssn=spot[[contractlist_r]]
spotssn.index=pd.to_datetime(spotssn.index)


if freq=='Weekly':
    spotssn['Year']=spotssn.index.year
    spotssn['Week']=spotssn.index.isocalendar().week
    spotssn.loc[spotssn[spotssn.index.date==date(2016,1,2)].index,'Week']=0
    spotssn.loc[spotssn[spotssn.index.date==date(2021,1,2)].index,'Week']=0
    spotssn.loc[spotssn[spotssn.index.date==date(2022,1,1)].index,'Week']=0
    yrlist=list(spotssn['Year'].unique())
    yrlist.sort(reverse=True)
    yrsl=st.multiselect('Select Years',options=yrlist,default=np.arange(curryear-4,curryear+1),key='spotyear1')
    spotssn=spotssn[spotssn['Year'].isin(yrsl)]
    sppt=spotssn.pivot_table(index='Week',columns='Year',values=contractlist_r,aggfunc='mean')
    spotplot=px.line(sppt,width=1000,height=500,title=str(contractlist_r)+' Weekly Seasonality')
    spotplot.update_xaxes(ticks=plot_ticks, tickwidth=plot_tickwidth,  ticklen=plot_ticklen)
    spotplot.update_layout(title_font_color=plot_title_font_color,title_font_size=plot_title_font_size,legend_font_size=plot_legend_font_size,xaxis=plot_axis,yaxis=plot_axis)
    spotplot['data'][-1]['line']['width']=5
    spotplot['data'][-1]['line']['color']='black'

    spotplot.update_layout(template=draft_template)
    st.plotly_chart(spotplot)

elif freq=='Monthly':
    spotssn['Year']=spotssn.index.year
    spotssn['Month']=spotssn.index.month
    yrlist=list(spotssn['Year'].unique())
    yrlist.sort(reverse=True)
    yrsl=st.multiselect('Select Years',options=yrlist,default=np.arange(curryear-6,curryear+1),key='spotyear2')
    spotssn=spotssn[spotssn['Year'].isin(yrsl)]
    sppt=spotssn.pivot_table(index='Month',columns='Year',values=contractlist_r,aggfunc='mean')
    spotplot=px.line(sppt,width=1000,height=500,title=str(contractlist_r)+' Monthly Seasonality')
    spotplot.update_xaxes(ticks=plot_ticks, tickwidth=plot_tickwidth,  ticklen=plot_ticklen)
    spotplot.update_layout(title_font_color=plot_title_font_color,title_font_size=plot_title_font_size,legend_font_size=plot_legend_font_size,xaxis=plot_axis,yaxis=plot_axis)
    spotplot['data'][-1]['line']['width']=5
    spotplot['data'][-1]['line']['color']='black'
    spotplot.update_layout(template=draft_template)
    st.plotly_chart(spotplot)

elif freq=='Quarterly':
    spotssn['Year']=spotssn.index.year
    spotssn['Quarter']=spotssn.index.quarter
    yrlist=list(spotssn['Year'].unique())
    yrlist.sort(reverse=True)
    yrsl=st.multiselect('Select Years',options=yrlist,default=np.arange(curryear-6,curryear),key='spotyear3')
    spotssn=spotssn[spotssn['Year'].isin(yrsl)]
    sppt=spotssn.pivot_table(index='Quarter',columns='Year',values=contractlist_r,aggfunc='mean')
    spotplot=px.line(sppt,width=1000,height=500,title=str(contractlist_r)+' Quarterly Seasonality')
    spotplot.update_xaxes(ticks=plot_ticks, tickwidth=plot_tickwidth,  ticklen=plot_ticklen)
    spotplot.update_layout(title_font_color=plot_title_font_color,title_font_size=plot_title_font_size,legend_font_size=plot_legend_font_size,xaxis=plot_axis,yaxis=plot_axis)
    spotplot['data'][-1]['line']['width']=5
    spotplot['data'][-1]['line']['color']='black'
    spotplot.update_layout(template=draft_template)
    st.plotly_chart(spotplot)

elif freq=='Daily':
    spotssn['Year']=spotssn.index.year
    spotssn['Day']=spotssn.index.day_of_year
    yrlist=list(spotssn['Year'].unique())
    yrlist.sort(reverse=True)
    yrsl=st.multiselect('Select Years',options=yrlist,default=np.arange(curryear-3,curryear+1),key='spotyear3')
    spotssn=spotssn[spotssn['Year'].isin(yrsl)]
    sppt=spotssn.pivot_table(index='Day',columns='Year',values=contractlist_r,aggfunc='mean')
    spotplot=px.line(sppt,width=1000,height=500,title=str(contractlist_r)+' Daily Seasonality')
    spotplot.update_xaxes(ticks=plot_ticks, tickwidth=plot_tickwidth,  ticklen=plot_ticklen)
    spotplot.update_layout(title_font_color=plot_title_font_color,title_font_size=plot_title_font_size,legend_font_size=plot_legend_font_size,xaxis=plot_axis,yaxis=plot_axis)
    spotplot['data'][-1]['line']['width']=5
    spotplot['data'][-1]['line']['color']='black'
    spotplot.update_traces(connectgaps=True)
    spotplot.update_layout(template=draft_template)
    st.plotly_chart(spotplot)


st.markdown('## **Technical Analysis**')

rangelist_r=st.selectbox('Select Range',options=['Last Year to Date','Year to Date','Month to Date','Last Week to Date','All'],key='205')
contractlist=st.selectbox('Select Segment',options=spot.columns)
bb=st.number_input('Bollinger Bands Window',value=20)
ma1=st.number_input('Short Term Moving Average Window',value=20)
ma2=st.number_input('Long Term Moving Average Window',value=50)

if rangelist_r=='Last Week to Date':
    rangestart_r=today - timedelta(days=today.weekday()) + timedelta(days=6, weeks=-2)
elif rangelist_r=='Month to Date':
    rangestart_r=date(today.year,today.month,1)
elif rangelist_r=='Year to Date':
    rangestart_r=date(today.year,1,1)
elif rangelist_r=='Last Year to Date':
    rangestart_r=date(today.year-1,1,1)
else:
    rangestart_r=date(2005,1,1)

contract=spot[[contractlist]]
contract.dropna(inplace=True)
contract=contract[pd.to_datetime(contract.index)>=pd.to_datetime(rangestart_r)]

contract.sort_index(inplace=True)
indicator_mast = SMAIndicator(close=contract[contractlist], window=ma1)
indicator_malt = SMAIndicator(close=contract[contractlist], window=ma2)
indicator_bb = BollingerBands(close=contract[contractlist], window=bb, window_dev=2)
contract['ma_st'] = indicator_mast.sma_indicator()
contract['ma_lt'] = indicator_malt.sma_indicator()
contract['bb_m'] = indicator_bb.bollinger_mavg()
contract['bb_h'] = indicator_bb.bollinger_hband()
contract['bb_l'] = indicator_bb.bollinger_lband()


contractplot=px.line(contract,width=1000,height=500,title='Dirty Tanker Bollinger Bands and Moving Average')
contractplot.update_xaxes(ticks=plot_ticks, tickwidth=plot_tickwidth,  ticklen=plot_ticklen)
contractplot.update_layout(title_font_color=plot_title_font_color,title_font_size=plot_title_font_size,legend_font_size=plot_legend_font_size,xaxis=plot_axis,yaxis=plot_axis)
contractplot.update_layout(template=draft_template)
st.plotly_chart(contractplot)


st.markdown('## **Size Spread**')

sprange=st.selectbox('Select Range',options=['Last Year to Date','Year to Date','Month to Date','All'],key='sprg')

today = pd.to_datetime('today')
if sprange=='Last Year to Date':
    spstart=date(today.year-1,1,1)
elif sprange=='Month to Date':
    spstart=date(today.year,today.month,1)
elif sprange=='Year to Date':
    spstart=date(today.year,1,1)
else:
    spstart=date(2015,1,1)

contract1=st.selectbox('Select Segment 1',options=spot.columns)
seglist=list(spot.columns)
seglist.remove(contract1)
contract2=st.selectbox('Select Segment 2',options=seglist)

spotsp=spot.copy()
spotsp['Spread']=spotsp[contract1]-spotsp[contract2]
spotsp=spotsp[['Spread']]
spotsp_=spotsp[pd.to_datetime(spotsp.index)>=pd.to_datetime(spstart)]

figsp=px.line(spotsp_['Spread'],width=1000,height=500,title=contract1+' minus '+contract2+' Spot Price Spread')
figsp.update_xaxes(ticks=plot_ticks, tickwidth=plot_tickwidth,  ticklen=plot_ticklen)
figsp.update_layout(title_font_color=plot_title_font_color,title_font_size=plot_title_font_size,legend_font_size=plot_legend_font_size,xaxis=plot_axis,yaxis=plot_axis)
figsp.update_layout(template=draft_template)
st.plotly_chart(figsp)

spfreq=st.radio('Select Frequency',options=['Daily','Weekly','Monthly','Quarterly'],key='spotspfreq')

if spfreq=='Weekly':
    spotsp['Year']=spotsp.index.year
    spotsp['Week']=spotsp.index.isocalendar().week
    spotsp.loc[spotsp[spotsp.index.date==date(2016,1,2)].index,'Week']=0
    spotsp.loc[spotsp[spotsp.index.date==date(2021,1,2)].index,'Week']=0
    spotsp.loc[spotsp[spotsp.index.date==date(2022,1,1)].index,'Week']=0
    yrlist=list(spotsp['Year'].unique())
    yrlist.sort(reverse=True)
    yrsl=st.multiselect('Select Years',options=yrlist,default=np.arange(curryear-4,curryear+1),key='spotspyear1')
    spotsp=spotsp[spotsp['Year'].isin(yrsl)]
    sppt=spotsp.pivot_table(index='Week',columns='Year',values='Spread',aggfunc='mean')
    spotplot=px.line(sppt,width=1000,height=500,title=contract1+' minus '+contract2+' Spot Price Spread'+' Weekly Seasonality')
    spotplot.update_xaxes(ticks=plot_ticks, tickwidth=plot_tickwidth,  ticklen=plot_ticklen)
    spotplot.update_layout(title_font_color=plot_title_font_color,title_font_size=plot_title_font_size,legend_font_size=plot_legend_font_size,xaxis=plot_axis,yaxis=plot_axis)
    spotplot['data'][-1]['line']['width']=5
    spotplot['data'][-1]['line']['color']='black'

    spotplot.update_layout(template=draft_template)
    st.plotly_chart(spotplot)

elif spfreq=='Monthly':
    spotsp['Year']=spotsp.index.year
    spotsp['Month']=spotsp.index.month
    yrlist=list(spotsp['Year'].unique())
    yrlist.sort(reverse=True)
    yrsl=st.multiselect('Select Years',options=yrlist,default=np.arange(curryear-6,curryear+1),key='spotspyear2')
    spotsp=spotsp[spotsp['Year'].isin(yrsl)]
    sppt=spotsp.pivot_table(index='Month',columns='Year',values='Spread',aggfunc='mean')
    spotplot=px.line(sppt,width=1000,height=500,title=contract1+' minus '+contract2+' Spot Price Spread'+' Monthly Seasonality')
    spotplot.update_xaxes(ticks=plot_ticks, tickwidth=plot_tickwidth,  ticklen=plot_ticklen)
    spotplot.update_layout(title_font_color=plot_title_font_color,title_font_size=plot_title_font_size,legend_font_size=plot_legend_font_size,xaxis=plot_axis,yaxis=plot_axis)
    spotplot['data'][-1]['line']['width']=5
    spotplot['data'][-1]['line']['color']='black'
    spotplot.update_layout(template=draft_template)
    st.plotly_chart(spotplot)

elif spfreq=='Quarterly':
    spotsp['Year']=spotsp.index.year
    spotsp['Quarter']=spotsp.index.quarter
    yrlist=list(spotsp['Year'].unique())
    yrlist.sort(reverse=True)
    yrsl=st.multiselect('Select Years',options=yrlist,default=np.arange(curryear-6,curryear),key='spotspyear3')
    spotsp=spotsp[spotsp['Year'].isin(yrsl)]
    sppt=spotsp.pivot_table(index='Quarter',columns='Year',values='Spread',aggfunc='mean')
    spotplot=px.line(sppt,width=1000,height=500,title=contract1+' minus '+contract2+' Spot Price Spread'+' Quarterly Seasonality')
    spotplot.update_xaxes(ticks=plot_ticks, tickwidth=plot_tickwidth,  ticklen=plot_ticklen)
    spotplot.update_layout(title_font_color=plot_title_font_color,title_font_size=plot_title_font_size,legend_font_size=plot_legend_font_size,xaxis=plot_axis,yaxis=plot_axis)
    spotplot['data'][-1]['line']['width']=5
    spotplot['data'][-1]['line']['color']='black'
    spotplot.update_layout(template=draft_template)
    st.plotly_chart(spotplot)

elif spfreq=='Daily':
    spotsp['Year']=spotsp.index.year
    spotsp['Day']=spotsp.index.day_of_year
    yrlist=list(spotsp['Year'].unique())
    yrlist.sort(reverse=True)
    yrsl=st.multiselect('Select Years',options=yrlist,default=np.arange(curryear-3,curryear+1),key='spotspyear3')
    spotsp=spotsp[spotsp['Year'].isin(yrsl)]
    sppt=spotsp.pivot_table(index='Day',columns='Year',values='Spread',aggfunc='mean')
    spotplot=px.line(sppt,width=1000,height=500,title=contract1+' minus '+contract2+' Spot Price Spread'+' Daily Seasonality')
    spotplot.update_xaxes(ticks=plot_ticks, tickwidth=plot_tickwidth,  ticklen=plot_ticklen)
    spotplot.update_layout(title_font_color=plot_title_font_color,title_font_size=plot_title_font_size,legend_font_size=plot_legend_font_size,xaxis=plot_axis,yaxis=plot_axis)
    spotplot['data'][-1]['line']['width']=5
    spotplot['data'][-1]['line']['color']='black'
    spotplot.update_traces(connectgaps=True)
    spotplot.update_layout(template=draft_template)
    st.plotly_chart(spotplot)




st.markdown('## **Dirty Tanker Asset Price**')

asst=st.session_state['tankerasset']
asset=asst.copy()

asset.index=pd.to_datetime(asset.index)

nbsl=st.multiselect('Select Segment for New Building Price',options=['VLCC NB','Suezmax NB','Aframax NB'],default=['VLCC NB'],key='slnb')
shsl=st.multiselect('Select Segment for Second Hand Price',options=['VLCC 5yr','Suezmax 5yr','Aframax 5yr'],default=['VLCC 5yr'],key='slsh')
rangelist=st.selectbox('Select Range',options=['Last Year to Date','Year to Date','Month to Date','All'],key='asssl')

today = pd.to_datetime('today')
if rangelist=='Last Year to Date':
    rangestart=date(today.year-1,1,1)
elif rangelist=='Month to Date':
    rangestart=date(today.year,today.month,1)
elif rangelist=='Year to Date':
    rangestart=date(today.year,1,1)
else:
    rangestart=date(2015,1,1)


assetsl=asset[nbsl+shsl]
assetsl=assetsl[assetsl.index>=pd.to_datetime(rangestart)]


figass=px.line(assetsl,width=1000,height=500,title='Vessel Asset Price')
figass.update_xaxes(ticks=plot_ticks, tickwidth=plot_tickwidth,  ticklen=plot_ticklen)
figass.update_layout(title_font_color=plot_title_font_color,title_font_size=plot_title_font_size,legend_font_size=plot_legend_font_size,xaxis=plot_axis,yaxis=plot_axis)
figass.update_layout(template=draft_template)
st.plotly_chart(figass)