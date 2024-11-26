import pandas as pd

translation_dict = {'requested_credit': 'Kredithöhe', 
                    'annuity': 'Annuität', 
                    'goods_price': 'Finanzierungs-/Gegenstandskosten', 
                    'age': 'Alter',
                    'years_employed': 'Anstellungs-/Rentendauer', 
                    'years_registered': 'Zeit seit Registrierungsänderung', 
                    'years_id_publish': 'Zeit seit ID-Dokumentänderung', 
                    'ext_bank_score_1': 'Kreditscore Bank 1', 
                    'ext_bank_score_2': 'Kreditscore Bank 2', 
                    'ext_bank_score_3': 'Kreditscore Bank 3', 
                    'years_phone': 'Zeit seit Telefonnummeränderung',
                    'sum_other_credits': 'Kreditsumme bei anderen Instituten', 
                    'sum_debt_other_credits': 'Schulden bei anderen Instituten',
                    'num_other_active_credits':  'Aktive Kredite bei anderen Instituten', 
                    'sum_prev_credits': 'Summe voriger Kredite',
                    'num_install_payments_dpd': 'Überfällige Ratenzahlungen des letzten Kredits', 
                    'num_month_credits_dpd': 'Überfällige Monate der vorigen Kredite', 
                    'sum_prev_goods_price': 'Summierte Finanzierungs-/Gegenstandskosten voriger Kredite', 
                    'gender': 'Geschlecht',
                    'income_type': 'Erwerbsverhältnis',
                    'education': 'Bildungsabschluss'}


def translate_feature_importances(engl_dict):
    """
    Translate english feature importances to german.

    Parameters
    -------------
    engl_dict(dict):
      Dictionary holding all english feature importances.

    Returns
    -------------
    ger_dict(dict):
      Dictionary holding all german feature importances.

    """
    engl_dict = pd.DataFrame.from_dict(engl_dict)
    ger_dict = pd.DataFrame({'0':[]})
    for feature in translation_dict:
        ger_dict.loc[translation_dict[feature]] = engl_dict.loc[feature]
    return ger_dict.to_dict()

def gradient_color(value):
    # Clamp the value between 0.0 and 1.0
    value = max(0.0, min(1.0, value))
    
    # Calculate the red and green components based on the value
    green = int((1.0 - value) * 255)
    red = int(value * 255)
    
    # Convert the red and green components to hexadecimal
    red_hex = format(red, '02x')
    green_hex = format(green, '02x')
    
    # Combine the components to create the color hex code
    color_hex = f'#{red_hex}{green_hex}00'
    
    return color_hex

def valid_input(numbers):
    """
    Check if all numbers are in valid range [-1;[.

    Parameters
    -------------
    numbers(list):
      Array of variables to be checked.

    Returns
    -------------
    (boolean):
      True if all numbers are valid, otherwise False.

    """
    for number in numbers:
        if number < -1.0:
            return False
    return True


def within_boundaries(numbers, low, high):
    """
    Check if all numbers are within given boundaries.

    Parameters
    -------------
    numbers(list):
      Array of variables to be checked.

    low(float):
      Inclusive lower boundary.
    
    high(float):
      Inclusive higher boundary.

    Returns
    -------------
    (boolean):
      True if all numbers are within boundaries, otherwise False.

    """
    for number in numbers:
        if number < low:
            return False
        elif number > high:
            return False
    return True

def date_to_years(start_date, end_date):
    """
    Convert timeintervall between dates to years.

    Parameters
    -------------
    start_date(datetime):
      First day of intervall.

    end_date(datetime):
      Last day of intervall.

    Returns
    -------------
    (float):
      Number of years between two given dates.
      
    """
    diff = abs(end_date - start_date)
    return diff.days/365.0