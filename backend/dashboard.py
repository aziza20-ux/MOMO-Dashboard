from database import get_db
from models.transactions import Transaction
from sqlalchemy import func, extract, and_
import datetime

def get_user_transactions(user_id, transaction_type=None, start_date=None, end_date=None,
                          min_amount=None, max_amount=None, limit=None):
    """
    Retrieves SMS transactions for a given user with optional filters.

    Args:
        user_id (int): The ID of the user.
        transaction_type (str, optional): '1' for received, '2' for sent.
        start_date (str, optional): Start date in YYYY-MM-DD format.
        end_date (str, optional): End date in YYYY-MM-DD format.
        min_amount (float, optional): Minimum transaction amount.
        max_amount (float, optional): Maximum transaction amount.
        limit (int, optional): Maximum number of transactions to retrieve.

    Returns:
        list: A list of Transaction objects.
    """
    with get_db() as db_session:
        query = db_session.query(Transaction).filter(Transaction.user_id == user_id)

        if transaction_type:
            query = query.filter(Transaction.type == transaction_type)
        
        if start_date:
            try:
                start_dt = datetime.datetime.strptime(start_date, '%Y-%m-%d')
                start_ms = int(start_dt.timestamp() * 1000)
                query = query.filter(Transaction.date >= start_ms)
            except ValueError:
                raise ValueError(f"Invalid start_date format: {start_date}")

        if end_date:
            try:
                end_dt = datetime.datetime.strptime(end_date, '%Y-%m-%d')
                end_ms = int((end_dt + datetime.timedelta(days=1)).timestamp() * 1000 - 1)
                query = query.filter(Transaction.date <= end_ms)
            except ValueError:
                raise ValueError(f"Invalid end_date format: {end_date}")

        if min_amount is not None:
            query = query.filter(Transaction.amount >= min_amount)

        if max_amount is not None:
            query = query.filter(Transaction.amount <= max_amount)

        # Apply ordering before limiting
        query = query.order_by(Transaction.date.desc())

        if limit is not None:
            query = query.limit(limit)

        return query.all()


def get_transaction_by_id(user_id, transaction_id):
    """
    Retrieves a single SMS transaction by its ID for a specific user.

    Args:
        user_id (int): The ID of the user.
        transaction_id (int): The ID of the transaction.

    Returns:
        Transaction: The Transaction object if found, otherwise None.
    """
    with get_db() as db_session:
        return db_session.query(Transaction).filter(
            and_(
                Transaction.user_id == user_id,
                Transaction.id == transaction_id
            )
        ).first()


def get_transaction_summary(user_id):
    """
    Provides a count summary of transaction types (received vs. sent).

    Returns:
        dict: Summary with count of total, received, sent, and unknown type SMS.
    """
    summary = {
        'total_sms': 0,
        'received_sms': 0,
        'sent_sms': 0,
        'unknown_type_sms': 0
    }

    with get_db() as db_session:
        summary['total_sms'] = db_session.query(Transaction).filter_by(user_id=user_id).count()

        type_counts = db_session.query(
            Transaction.type, func.count(Transaction.id)
        ).filter_by(user_id=user_id).group_by(Transaction.type).all()

        for sms_type, count in type_counts:
            if sms_type == '1':
                summary['received_sms'] = count
            elif sms_type == '2':
                summary['sent_sms'] = count
            else:
                summary['unknown_type_sms'] += count

    return summary


def get_transaction_volume_by_type(user_id):
    """
    Aggregates total transaction amount by type (received vs. sent).
    Returns data suitable for a pie chart.

    Returns:
        dict: Labels and data for charting.
    """
    with get_db() as db_session:
        type_volumes = db_session.query(
            Transaction.type, func.sum(Transaction.amount)
        ).filter(
            and_(
                Transaction.user_id == user_id,
                Transaction.amount.isnot(None)
            )
        ).group_by(Transaction.type).all()

        data = {
            'labels': [],
            'data': []
        }

        for sms_type, total_amount in type_volumes:
            label = "Received" if sms_type == '1' else ("Sent" if sms_type == '2' else "Other")
            data['labels'].append(label)
            data['data'].append(float(total_amount or 0))

        return data


def get_monthly_transaction_volume(user_id):
    """
    Aggregates total transaction amount by month for charting.
    Returns data suitable for a bar or line chart.

    Returns:
        dict: Month-wise labels and corresponding transaction volume.
    """
    transactions_by_month_volume = {}

    with get_db() as db_session:
        all_transactions = db_session.query(
            Transaction.date, Transaction.amount
        ).filter(
            and_(
                Transaction.user_id == user_id,
                Transaction.amount.isnot(None)
            )
        ).all()

        for tx_date_ms, amount in all_transactions:
            if tx_date_ms is None or amount is None:
                continue
            try:
                dt_object = datetime.datetime.fromtimestamp(tx_date_ms / 1000)
                month_year = dt_object.strftime('%Y-%m')
                transactions_by_month_volume[month_year] = (
                    transactions_by_month_volume.get(month_year, 0.0) + float(amount)
                )
            except (ValueError, TypeError):
                continue

    sorted_months = sorted(transactions_by_month_volume.keys())
    labels = sorted_months
    data = [transactions_by_month_volume[month] for month in sorted_months]

    return {'labels': labels, 'data': data}


def get_amount_distribution_summary(user_id):
    """
    Calculates the total received amount and total sent amount.
    Suitable for a simple bar chart or numerical display.

    Returns:
        dict: Labels and totals for received and sent amounts.
    """
    total_received = 0.0
    total_sent = 0.0

    with get_db() as db_session:
        received_query = db_session.query(func.sum(Transaction.amount)).filter(
            and_(
                Transaction.user_id == user_id,
                Transaction.type == '1',
                Transaction.amount.isnot(None)
            )
        ).scalar()

        if received_query:
            total_received = float(received_query)

        sent_query = db_session.query(func.sum(Transaction.amount)).filter(
            and_(
                Transaction.user_id == user_id,
                Transaction.type == '2',
                Transaction.amount.isnot(None)
            )
        ).scalar()

        if sent_query:
            total_sent = float(sent_query)

    return {
        'labels': ['Received', 'Sent'],
        'data': [total_received, total_sent]
    }

