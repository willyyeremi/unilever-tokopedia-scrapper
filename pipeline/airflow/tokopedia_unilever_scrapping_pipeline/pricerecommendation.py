from sqlalchemy import create_engine, MetaData, func, Column, ForeignKey, Integer, String, Float, Date
from sqlalchemy.sql import text
from sqlalchemy.orm import sessionmaker, declarative_base
import pandas
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import PassiveAggressiveRegressor

import module

from pathlib import Path
from datetime import timedelta
from math import ceil


root = Path(__file__).parent.parent

database_credential_dict = module.connection.credential_get(f'{root}\\credential.csv')
database_url = module.connection.url(database_credential_dict['user'], database_credential_dict['password'], database_credential_dict['host'], database_credential_dict['port'], database_credential_dict['database'])
database_engine = create_engine(database_url)
database_session = sessionmaker(autocommit = False, autoflush = False, bind = database_engine)()

metadata = MetaData()
base = declarative_base(metadata = metadata)
class productmaster(base):
    __tablename__ = 'productmaster'
    __table_args__ = {'schema': 'public'}
    id = Column(Integer, primary_key = True)
    name = Column(String)
    type = Column(String)
    detail = Column(String)
    createdate = Column(Date)
class product(base):
    __tablename__ = 'product'
    __table_args__ = {'schema': 'public'}
    id = Column(Integer, primary_key = True)
    productmasterid = Column(Integer, ForeignKey(productmaster.id))
    price = Column(Integer)
    originalprice = Column(Integer)
    discountpercentage = Column(Float)
    platform = Column(String)
    createdate = Column(Date)
class pricerecommendation(base):
    __tablename__ = 'pricerecommendation'
    __table_args__ = {'schema': 'public'}
    productmasterid = Column(Integer, ForeignKey(productmaster.id), primary_key = True)
    price = Column(Integer)
    date = Column(Date)

def data_loader(session, batch_size):
    offset = 0
    data_query = (session 
        .query(
            product.productmasterid.label('productmasterid')
            ,productmaster.type.label('type')
            ,product.price.label('price')
            ,product.originalprice.label('originalprice')
            ,product.discountpercentage.label('discountpercentage')
            ,product.createdate.label('createdate'))
        .join(productmaster)
        .offset(offset)
        .limit(batch_size))
    data = pandas.read_sql(data_query.statement, database_session.bind)
    yield data
    offset += batch_size

def preprocessing_data(chunk_data):
    type_one_hot_encode = pandas.DataFrame(OneHotEncoder(handle_unknown = 'ignore', sparse_output = False).fit_transform(chunk_data[['type']]))
    type_one_hot_encode.index = chunk_data.index
    chunk_data = chunk_data.drop('type', axis = 1)
    chunk_data = pandas.concat([chunk_data, type_one_hot_encode], axis=1)
    chunk_data['createdate'] = pandas.to_datetime(chunk_data['createdate'])
    chunk_data['createdate'] = chunk_data['createdate'].astype(int) / 10**9  
    features = chunk_data[[i for i in chunk_data.columns.values.tolist() if i!= 'price']]
    features.columns = features.columns.astype(str)
    features = StandardScaler().fit_transform(features)
    target = chunk_data[['price']]
    return features, target

for data in data_loader(database_session, 100):
    x_batch, y_batch = preprocessing_data(data)
    model = PassiveAggressiveRegressor().partial_fit(x_batch, y_batch)

next_data_query = (database_session 
    .query(
        productmaster.id.label('productmasterid')
        ,productmaster.type.label('type')))
next_data = pandas.read_sql(next_data_query.statement, database_session.bind)
next_data['originalprice'] = ceil(database_session.query(func.sum(product.originalprice)).scalar() / database_session.query(func.count(product.originalprice)).scalar())
next_data['discountpercentage'] = database_session.query(func.sum(product.discountpercentage)).scalar() / database_session.query(func.count(product.discountpercentage)).scalar()
next_data['createdate'] = pandas.to_datetime('today') + timedelta(days = 1)
next_data['price'] = 0

x_new, y_new = preprocessing_data(next_data)
price_prediction = model.predict(x_new)
next_data['price'] = price_prediction
next_data = next_data.drop(columns = ['type', 'originalprice', 'discountpercentage'], axis = 1)

database_session.execute(text("truncate public.pricerecommendation"))
for data in next_data.to_dict("records"):
    new_data = pricerecommendation(
        productmasterid = data['productmasterid']
        ,price = data['price']
        ,date = data['createdate'])
    database_session.add(new_data)
database_session.commit()

database_session.close()
