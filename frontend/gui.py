import streamlit as st
import requests
import pandas as pd
import datetime
import plotly.express as px
from utils import *


# Kommentaraenderung: Function to highlight text within a DataFrame
def highlight_text(text, keyword, font_size=20):
    highlighted_keyword = f'<b style="font-size: {font_size}px;">{keyword}</b>'
    return text.replace(keyword, highlighted_keyword)

def call_backend(data):
    """
    Run simulation by sending data via FastAPI to backend.

    Parameters
    -------------
    data(dict):
      Dictionary with raw input data.

    Returns
    -------------
    res (dict):
      Prediction dictionary containing 'class' (int) and 'prob' (float).
      
    """
    pred = requests.post(
           'http://localhost:8000/predict',
           params=data).json()
    return pred


# app setup
st.set_page_config(page_title='BWI Application', 
                   page_icon='./images/BW_icon.png')
st.title('BWI Application')
st.sidebar.image('./images/BWI_GmbH_logo.png', 
                 use_column_width='auto')

# instruction prompt
prompt = st.empty()
instruction = 'Bitte Daten für die Vorhersage eingeben!'
prompt.text(instruction)

# personal infos
st.sidebar.markdown("""---""")
st.sidebar.markdown('**Personenangaben**')
geschlecht = st.sidebar.radio('Geschlecht', ['Männlich', 
                                             'Weiblich', 
                                             'Divers'])
min_date = datetime.date(1900, 1, 1)
end_date = datetime.date.today()
start_date = st.sidebar.date_input('Geburtsdatum', 
                                   min_value=min_date, 
                                   max_value=end_date, 
                                   value=datetime.date(1970, 1, 1))
education = st.sidebar.radio('Höchster Bildungsabschluss', 
                             ['Ohne Bildungabschluss', 
                              'Sekundarbildungsabschluss', 
                              'Akademischer Bildungabschluss'])
employment_status = st.sidebar.radio('Aktuelles Erwerbsverhältnis',
                                     ['Keines',
                                      'Angestellt/Selbständig',
                                      'Rentenbezogen'])
if employment_status != 'Keines':
    employment_date = st.sidebar.date_input('Einstellungsdatum/Renteneintritt', 
                                            min_value=min_date, 
                                            max_value=end_date, 
                                            value=datetime.date(2000, 1, 1))
else:
    employment_date = end_date

# Credit infos
st.sidebar.markdown("""---""")
st.sidebar.markdown('**Kreditanforderungen**')
credit = st.sidebar.number_input(label='Kredithöhe [€]', min_value=0.0, step=100.,format="%.2f")
annuity = st.sidebar.number_input(label='Annuität [€]', min_value=0.0, step=100.,format="%.2f")
goods_price = st.sidebar.number_input(label='Finanzierungs-/Gegenstandskosten [€]', min_value=0.0, step=100.,format="%.2f")

# payment infos
st.sidebar.markdown("""---""")
st.sidebar.markdown('**Zahlungsprofil bei Home Credit Group**')

if st.sidebar.checkbox('Kunde der Home Credit Group?'):
    num_month_credits = st.sidebar.number_input("Kummulierte Anzahl der Monate an Kreditlaufzeit bei der Home Credit Group", min_value=0, value=0, step=1, format="%d")
    if num_month_credits != 0:
        num_month_credits_dpd = st.sidebar.number_input("Davon überfällige Monate",  min_value=0, max_value=num_month_credits, step=1, format="%d")
    else:
        num_month_credits_dpd = 0

    num_installments = st.sidebar.number_input("Gesamtanzahl der Ratenzahlung im letzten Kredit der Home Credit Group",  min_value=0, step=1, format="%d")
    if num_installments != 0:
        num_installments_dpd = st.sidebar.number_input("Davon überfallige Ratenzahlungen", max_value=num_installments, min_value=0, step=1, format="%d")
    else:
        num_installments_dpd = 0

    sum_prev_credits = st.sidebar.number_input(label='Summe aller voriger Kredite bei der Home Credit Group [€]', min_value=0.0, step=100.,format="%.2f")
    if sum_prev_credits != 0.0:
        sum_prev_goods_price = st.sidebar.number_input(label='Summierte Finanzierungs-/Gegenstandskosten aller voriger Kredite bei der Home Credit Group [€]', min_value=0.0, step=100.,format="%.2f")
    else:
        sum_prev_goods_price = 0.0

else:
    num_month_credits = -1
    num_month_credits_dpd = -1
    num_installments = -1
    num_installments_dpd = 1
    sum_prev_credits = -1.0
    sum_prev_goods_price = -10000001.0

# external payment infos
st.sidebar.markdown("""---""")
st.sidebar.markdown('**Zahlungsprofil bei externen Instituten**')
if st.sidebar.checkbox('Kreditscore Bank 1 vorhanden?'):
    ext_bank_score_1 = st.sidebar.number_input(label='Kreditscore externer Bank 1 [0.0 bis 1.0]', min_value=0.0, max_value=1.0, step=0.01, format="%.6f")
else:
    ext_bank_score_1 = -1.0
if st.sidebar.checkbox('Kreditscore Bank 2 vorhanden?'):
    ext_bank_score_2 = st.sidebar.number_input(label='Kreditscore externer Bank 2 [0.0 bis 1.0]', min_value=0.0, max_value=1.0, step=0.01, format="%.6f")
else:
    ext_bank_score_2 = -1.0
if st.sidebar.checkbox('Kreditscore Bank 3 vorhanden?'):
    ext_bank_score_3 = st.sidebar.number_input(label='Kreditscore externer Bank 3 [0.0 bis 1.0]', min_value=0.0, max_value=1.0, step=0.01, format="%.6f")
else:
    ext_bank_score_3 = -1.0

if st.sidebar.checkbox('Historie mit anderen Kreditinstituten?'):
    num_other_active_credits = st.sidebar.number_input("Anzahl aktiver Kredite bei anderen Instituten", min_value=0, value=0, step=1, format="%d")
    sum_other_credits = st.sidebar.number_input("Summe aller Kredite bei anderen Instituten [€]", min_value=0.0, step=100.,format="%.2f")
    sum_debt_other_credits = st.sidebar.number_input("Summe ausstehender Schulden für Kredite anderer Institute [€]", min_value=0.0, step=100.,format="%.2f")
else:
    num_other_active_credits = -1
    sum_other_credits = -1.0
    sum_debt_other_credits = -1.0

# additional infos
st.sidebar.markdown("""---""")
st.sidebar.markdown('**Zusätzliche Informationen**')
date_registration = st.sidebar.date_input('Datum der letzten Änderung der Registrierung', 
                                          min_value=min_date, 
                                          max_value=end_date, 
                                          value=datetime.date(2000, 1, 1))

date_id = st.sidebar.date_input('Datum der letzten Änderung des ID-Dokuments', 
                                min_value=min_date, 
                                max_value=end_date, 
                                value=datetime.date(2000, 1, 1))

date_phone = st.sidebar.date_input('Datum der letzten Änderung der Telefonnummer', 
                                   min_value=min_date, 
                                   max_value=end_date, 
                                   value=datetime.date(2000, 1, 1))

# button action
st.sidebar.markdown("""---""")
st.sidebar.markdown(""" <style>
                    div.stButton > button:first-child {
                    background-color: rgb(256,76,76);color:white;font-size:26px;
                    }
                    </style>""", unsafe_allow_html=True)

if st.sidebar.button('**Kreditrisiko berechnen**', use_container_width=True):
    with st.spinner('Überprüfung der Eingaben ...'):
        # convert data format
        if geschlecht == 'Männlich':
            gender = 'M'
        elif geschlecht == 'Weiblich':
            gender = 'F'
        else:
            gender = 'XNA'

        age = date_to_years(start_date, end_date)
        employment_dur = date_to_years(employment_date, end_date)
        id_dur = date_to_years(date_id, end_date)
        phone_dur = date_to_years(date_phone, date_registration)
        registration_dur = date_to_years(date_registration, end_date)

        secundary_education = True if education == "Sekundarbildungsabschluss" else False
        higher_education = True if education == "Akademischer Bildungabschluss" else False

        income_type_working = True if employment_status == "Angestellt/Selbständig" else False
        income_type_pensioner = True if employment_status == "Rentenbezogen" else False

        # check data for format (already prevented by streamlit)
        correct_data = True
        if not within_boundaries([ext_bank_score_1, ext_bank_score_2, ext_bank_score_3], -1.0, 1.0):
            correct_data = False
        if not valid_input([credit, annuity, goods_price, 
                            num_installments, num_installments_dpd,
                            num_month_credits, num_month_credits_dpd,
                            sum_prev_credits,
                            num_other_active_credits, sum_other_credits, sum_debt_other_credits]):
            correct_data = False

    # in case input data in correct format, run prediction
    if correct_data:
        prompt.empty()
        # dictionary with default prediction values to send to backend
        data = {'requested_credit': credit,
                'annuity': annuity,
                'goods_price': goods_price,
                'age': age,
                'gender': gender,
                'ext_bank_score_1': ext_bank_score_1,
                'ext_bank_score_2': ext_bank_score_2,
                'ext_bank_score_3': ext_bank_score_3,
                'num_install_payments': num_installments,
                'num_install_payments_dpd': num_installments_dpd,
                'num_month_credits': num_month_credits,
                'num_month_credits_dpd': num_month_credits_dpd,
                'sum_prev_credits': sum_prev_credits,
                'sum_prev_goods_price': sum_prev_goods_price,
                'num_other_active_credits': num_other_active_credits,
                'sum_other_credits': sum_other_credits,
                'sum_debt_other_credits': sum_debt_other_credits,
                'higher_education_type': higher_education,
                'secondary_education_type': secundary_education,
                'income_type_working': income_type_working,
                'income_type_pensioner': income_type_pensioner,
                'years_employed': employment_dur,
                'years_registered': registration_dur,
                'years_id_publish': id_dur,
                'years_phone': phone_dur
                }
        prediction_done = False
        # show spinner while prediction is running
        with st.spinner('Vorhersage läuft ...'):
            try:
                # make post request
                pred = call_backend(data)
                prediction_done = True
            except Exception:
                st.error('Fehler: Bitte Verbindung zum Backend überprüfen!')
                prediction_done = False
        # show results

        if pred['class'] == 0:
            pred['probability'] = 1-pred['probability']

        color_map = {"Risiko": gradient_color(pred['probability']), 'Potential': '#eeeeee'}
        fig1 = px.bar({"x": ["Kunde", 'Kunde'], "Farbe": ['Risiko', 'Potential'], 'y': [pred['probability'], 1-pred['probability']]}, x='y', color='Farbe', y='x', orientation='h', color_discrete_map=color_map)
        fig1.update_layout(title="Risiko Level: " + str(round(pred['probability']*100, 2)) + "%", width=740, height=175, xaxis_title='', xaxis_visible=True,
                            yaxis_visible=False,
                            showlegend=False)
        st.write(fig1)

        risk1, risk2, risk3, risk4 = st.columns([1, 1, 1, 1])

        #risk1.caption("Sehr gut")
        df1 = pd.DataFrame.from_dict({'0': ['Sehr gut', 'Kundenantrag akzeptieren']})
        style1 = df1.style.hide_index()
        style1.hide_columns()
        #risk2.subheader("Okay")
        df2 = pd.DataFrame.from_dict({'1': ['Okay', 'Sicherheiten einfordern und Zinssatz erhöhen']})
        style2 = df2.style.hide_index()
        style2.hide_columns()
        #risk3.subheader("Riskant")
        df3 = pd.DataFrame.from_dict({'2': ['Riskant', 'Annahme ausschließlich durch Rücksprache mit Vorgesetzten']})
        style3 = df3.style.hide_index()
        style3.hide_columns()
        #risk4.subheader("Schlecht")
        df4 = pd.DataFrame.from_dict({'3': ['Schlecht', 'Kundenantrag ablehnen']})
        style4 = df4.style.hide_index()
        style4.hide_columns()

        # Apply text highlighting to the specific column
        if pred['probability'] >= 0.75:
            keyword = 'Schlecht'
        elif pred['probability'] >= 0.5:
            keyword = 'Riskant'
        elif pred['probability'] >= 0.25:
            keyword = 'Okay'
        else:
            keyword = 'Sehr gut'
        df1['0'] = df1['0'].apply(lambda x: highlight_text(x, keyword))
        df2['1'] = df2['1'].apply(lambda x: highlight_text(x, keyword))
        df3['2'] = df3['2'].apply(lambda x: highlight_text(x, keyword))
        df4['3'] = df4['3'].apply(lambda x: highlight_text(x, keyword))
        style1 = df1.style.hide_index()
        style1.hide_columns()

        # Write the formatted DataFrames to the columns
        risk1.write(style1.to_html(escape=False), unsafe_allow_html=True)
        risk2.write(style2.to_html(escape=False), unsafe_allow_html=True)
        risk3.write(style3.to_html(escape=False), unsafe_allow_html=True)
        risk4.write(style4.to_html(escape=False), unsafe_allow_html=True)

        fig=px.bar(translate_feature_importances(pred['feature_importance']), x='0', orientation='h')
        fig.update_traces(marker=dict(color='rgb(256,76,76)'))
        fig.update_layout(title='Wichtigste Merkmale',
                          xaxis_title='Gewichtung',
                          yaxis_title='Merkmal',
                          yaxis={'categoryorder': 'total ascending'},
                          height=700)
        st.write(fig)
