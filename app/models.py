from sqlalchemy import Column, Integer, String, ForeignKey, Date, TEXT, Interval, TIMESTAMP
from sqlalchemy.orm import relationship
from app.db.database import Base

# class User_s(BaseSecret):
#     __tablename__ = "users_s"

#     id = Column(Integer, primary_key=True, index=True)
#     login = Column(TEXT, unique=True, nullable=False)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, nullable=False)
    sex = Column(String(3), nullable=True)
    age = Column(Integer, nullable=True)
    permission = Column(Integer, nullable=False) #2 - это = 1, 2 - это тр и итрф = 2,  
                                               # 1 - это тр = 3, 1 - это интр = 4. 
    
    transaction = relationship("Ttransaction", back_populates="user")
    session = relationship("Session", back_populates="user")


# Критерии по транзаккциям
class Mcc(Base):
    __tablename__ = "mcc"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    category_name = Column(String, nullable=False)

    transaction = relationship("Ttransaction",back_populates="mcc")

class Place(Base):
    __tablename__ = "place"

    id = Column(Integer, primary_key=True, index=True)
    country = Column(String)
    region = Column(String)
    city = Column(String)
    street = Column(String)

    transaction = relationship("Ttransaction",back_populates="place")

class Stack(Base):
    __tablename__ = "stack"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    conditions = Column(TEXT)

    


class Ttransaction(Base):
    __tablename__ = "transaction"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer,ForeignKey("users.user_id"))
    mcc_id = Column(Integer,ForeignKey("mcc.id"))
    sum = Column(Integer, nullable=False)
    place_id = Column(Integer,ForeignKey("place.id"), nullable=True)
    amount = Column(Integer)
    date = Column(Date,nullable=False)
    payment_method = Column(Integer, nullable=False)
    stack = Column(Integer, ForeignKey("stack.id"))
    
    user = relationship("User", back_populates="transaction")
    mcc = relationship("Mcc", back_populates="transaction")
    place = relationship("Place", back_populates="transaction")
   

# Критерии больше про удачные решения дизайна/функционала
class Support(Base):
    __tablename__ = "support"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer,ForeignKey("users.user_id"))
    date = Column(TIMESTAMP,nullable=False)
    type = Column(String,nullable=False)
    ui_version_app = Column(String, nullable=False)


class Session(Base):
    __tablename__ = "session"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer,ForeignKey("users.user_id"))
    type = Column(String,nullable=False)
    clicks_on_new_ui = Column(Integer)
    clicks_on_old_ui = Column(Integer)
    ui_version_app = Column(String, nullable=False)
    session_duration = Column(Interval, nullable=False)  
    date_start =  Column(Date, nullable=False)  
    user = relationship("User", back_populates="session")





    
