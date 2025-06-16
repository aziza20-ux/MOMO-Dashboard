# Import Base from the central database definition
from database import Base
from sqlalchemy import Column, Integer, String, BigInteger, Float

class Transaction(Base):
    """
    SQLAlchemy model representing an SMS transaction.
    Maps to the 'transactions' table in the database.
    """
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False) # Link to the user who uploaded this SMS

    protocol = Column(String, nullable=True)
    address = Column(String, nullable=True)
    date = Column(BigInteger, nullable=True)  # Storing as milliseconds timestamp
    type = Column(String, nullable=True)      # '1' for received, '2' for sent
    subject = Column(String, nullable=True)
    body = Column(String, nullable=True)
    toa = Column(String, nullable=True)
    sc_toa = Column(String, nullable=True)
    service_center = Column(String, nullable=True)
    read = Column(String, nullable=True)
    status = Column(String, nullable=True)
    locked = Column(String, nullable=True)
    date_sent = Column(BigInteger, nullable=True)
    sub_id = Column(String, nullable=True)
    readable_date = Column(String, nullable=True)
    contact_name = Column(String, nullable=True)
    amount = Column(Float, nullable=True) # New column to store extracted transaction amount

    def __repr__(self):
        return (
            f"<Transaction(id={self.id}, user_id={self.user_id}, address='{self.address}', "
            f"body='{self.body[:50]}...', amount={self.amount}, date='{self.readable_date}')>"
        )

