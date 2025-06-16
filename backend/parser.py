import xml.etree.ElementTree as ET
import re # Import regex module
from sqlalchemy.exc import SQLAlchemyError
from models.transactions import Transaction # Import Transaction model
from database import get_db

def extract_amount_from_body(body_text):
    """
    Extracts a numerical amount from the SMS body string.
    Looks for patterns like "X RWF", "received X", "payment of X", etc.
    Prioritizes RWF currency if present.
    """
    if not body_text:
        return None

    # Regex to find numbers that look like currency amounts,
    # often followed by RWF, or within common transaction phrases.
    # It tries to capture numbers with commas (e.g., 27,000) and decimals (e.g., 123.45)
    # Pattern 1: Number immediately followed by RWF
    match_rwf = re.search(r'(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)\s*RWF', body_text, re.IGNORECASE)
    if match_rwf:
        # Remove commas for conversion to float
        return float(match_rwf.group(1).replace(',', ''))

    # Pattern 2: "received X", "payment of X", "Your balance: X", "Total: X"
    # This is more general and might capture non-RWF numbers, but useful if RWF isn't explicit.
    match_phrases = re.search(
        r'(?:received|payment of|is:|balance:|Total:)\s*(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)',
        body_text, re.IGNORECASE
    )
    if match_phrases:
        return float(match_phrases.group(1).replace(',', ''))
    
    # Pattern 3: Simple large number extraction (less reliable)
    # This might catch TX IDs or other numbers, use as a last resort.
    match_general_number = re.search(r'(\d{2,}(?:,\d{3})*(?:\.\d{1,2})?)', body_text)
    if match_general_number:
        return float(match_general_number.group(1).replace(',', ''))

    return None


def parse_sms_xml_content(xml_content):
    """
    Parses the XML content from the SMS backup and extracts SMS details.
    Now also extracts amount.

    Args:
        xml_content (str): The XML content as a string.

    Returns:
        list: A list of dictionaries, where each dictionary represents an SMS record.
    """
    sms_data = []
    try:
        root = ET.fromstring(xml_content)
        for sms_element in root.findall('sms'):
            sms_record = {
                'protocol': sms_element.get('protocol'),
                'address': sms_element.get('address'),
                'date': sms_element.get('date'),
                'type': sms_element.get('type'),
                'subject': sms_element.get('subject'),
                'body': sms_element.get('body'),
                'toa': sms_element.get('toa'),
                'sc_toa': sms_element.get('sc_toa'),
                'service_center': sms_element.get('service_center'),
                'read': sms_element.get('read'),
                'status': sms_element.get('status'),
                'locked': sms_element.get('locked'),
                'date_sent': sms_element.get('date_sent'),
                'sub_id': sms_element.get('sub_id'),
                'readable_date': sms_element.get('readable_date'),
                'contact_name': sms_element.get('contact_name')
            }
            # Extract amount using the new function
            sms_record['amount'] = extract_amount_from_body(sms_record['body'])

            sms_data.append(sms_record)
    except ET.ParseError as e:
        print(f"Parser Error: Could not parse XML content: {e}")
        return []
    except Exception as e:
        print(f"Parser Error: An unexpected error occurred during XML parsing: {e}")
        return []
    return sms_data

def insert_transactions_from_parsed_data(user_id, parsed_data):
    """
    Inserts a list of parsed SMS data dictionaries into the database
    as Transaction records for a specific user.

    Args:
        user_id (int): The ID of the user uploading the data.
        parsed_data (list): A list of dictionaries, each representing an SMS record.

    Returns:
        int: The number of records successfully inserted.
    """
    inserted_count = 0
    if not parsed_data:
        print("No data to insert.")
        return 0

    with get_db() as db_session:
        for record in parsed_data:
            try:
                # Convert date and date_sent to BigInteger, handle potential errors
                for key in ['date', 'date_sent']:
                    if record.get(key) is not None:
                        try:
                            record[key] = int(record[key])
                        except (ValueError, TypeError):
                            record[key] = None # Set to None if conversion fails
                
                # Add user_id to the record
                record['user_id'] = user_id
                
                new_transaction = Transaction(**record)
                db_session.add(new_transaction)
                inserted_count += 1
            except SQLAlchemyError as e:
                print(f"Database Error: Could not add record for user {user_id}. Error: {e}")
                # Don't rollback immediately, try to insert other records
                # A full rollback on all errors would be too disruptive if one record fails
                pass # Continue processing other records
            except Exception as e:
                print(f"Unexpected Error: Could not process record for user {user_id}. Error: {e}")
                pass

        try:
            db_session.commit()
            print(f"Successfully inserted {inserted_count} transactions for user {user_id}.")
        except SQLAlchemyError as e:
            db_session.rollback()
            print(f"Database Error: Failed to commit all transactions for user {user_id}. Error: {e}")
            inserted_count = 0 # Indicate failure of the batch
        except Exception as e:
            db_session.rollback()
            print(f"Unexpected Error: Failed to commit transactions for user {user_id}. Error: {e}")
            inserted_count = 0

    return inserted_count
