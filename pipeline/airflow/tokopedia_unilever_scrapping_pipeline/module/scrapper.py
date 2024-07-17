def driver_maker():
    from selenium.webdriver import Chrome, ChromeOptions
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    
    service = Service(ChromeDriverManager().install())
    options =  ChromeOptions()
    driver = Chrome(service = service, options = options)
    return driver

def next_button_check(soup):
    next_button = soup.find('a', class_='css-14ulvr4')
    if next_button:
        next_page_url = next_button.get('href')
        next_page_url = "https://www.tokopedia.com" + next_page_url
        value = 1
    else:
        next_page_url = ''
        value = 0
    return next_page_url, value

def item_link_get(soup):
    link_list = []
    product_containers = soup.find_all('div', class_='css-1sn1xa2')
    for product_container in product_containers:
        link_containers = product_container.find_all('a', class_='pcv3__info-content css-gwkf0u')
        for link_container in link_containers:
            product_url = link_container.get('href')
            link_list.append(product_url)
    return link_list

def product_list_loader(driver: object, url):
    from bs4 import BeautifulSoup
    import time
    driver.get(url)
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    next_page_url, state_value = next_button_check(soup)
    link_list = item_link_get(soup)
    return link_list, next_page_url, state_value

def web_data_get(driver, link_list):
    import bs4
    import pandas
    import time
    from datetime import datetime

    data_list = []
    for link in link_list:
        current_timestamp = pandas.to_datetime(datetime.strftime(datetime.now(), '%Y-%m-%d'))
        driver.get(link)
        time.sleep(7)
        soup = bs4.BeautifulSoup(driver.page_source, 'html.parser')
        product_data = {}
        product_data['name'] = soup.find('h1', class_='css-1xfedof').text.strip()
        product_data['type'] = soup.select('ol.css-60knpe > li.css-d5bnys')[3].text
        product_data['detail'] = soup.select_one('div[data-testid="lblPDPDescriptionProduk"]').text
        product_data['createdate'] = current_timestamp
        product_data['price'] = int(soup.select_one('div.price[data-testid="lblPDPDetailProductPrice"]').text.replace("Rp", "").replace(".", ""))
        discountpercentage_element = soup.select_one('span[data-testid="lblPDPDetailDiscountPercentage"]')
        if discountpercentage_element:
            product_data['discountpercentage'] = float(discountpercentage_element.text.replace("%", "")) / 100
        else:
            product_data['discountpercentage'] = float(0)
        originalprice_element = soup.select_one('span[data-testid="lblPDPDetailOriginalPrice"]')
        if originalprice_element:
            product_data['originalprice'] = int(originalprice_element.text.replace("Rp", "").replace(".", ""))
        else:
            product_data['originalprice'] = int(product_data['price'])
        product_data['platform'] = 'tokopedia'
        data_list.append(product_data)
    return data_list

def product_master_input(credential_path, data_list):
    from sqlalchemy import create_engine, MetaData, Column, Integer, String, Date
    from sqlalchemy.orm import sessionmaker, declarative_base
    import module
    
    # defining database connection
    database_credential_dict = module.connection.credential_get(credential_path)
    database_url = module.connection.url(database_credential_dict['user'], database_credential_dict['password'], database_credential_dict['host'], database_credential_dict['port'], database_credential_dict['database'])
    database_engine = create_engine(database_url)
    database_connection = database_engine.connect()
    database_session = sessionmaker(bind = database_engine)()
    # defining the table in database as object
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
    # processing data
    for data in data_list:
        exist_check = database_session.query(productmaster).filter_by(name = data['name']).first()
        if exist_check:
            exist_check.type = data['type']
            exist_check.detail = data['detail']
        else:
            new_data = productmaster(
                name = data['name']
                ,type = data['type']
                ,detail = data['detail']
                ,createdate = data['createdate'])
            database_session.add(new_data)
        database_session.commit()
    # closing the databasee connection
    database_connection.close()

def product_input(credential_path, data_list):
    from sqlalchemy import create_engine, MetaData, Column, ForeignKey, Integer, Float, String, Date
    from sqlalchemy.orm import sessionmaker, declarative_base
    import module
    
    # defining database connection
    database_credential_dict = module.connection.credential_get(credential_path)
    database_url = module.connection.url(database_credential_dict['user'], database_credential_dict['password'], database_credential_dict['host'], database_credential_dict['port'], database_credential_dict['database'])
    database_engine = create_engine(database_url)
    database_connection = database_engine.connect()
    database_session = sessionmaker(bind = database_engine)()
    # defining the table in database as object
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
        # childern: Mapped["product"] = relationship(back_populates = "parent")
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
        # parent: Mapped["productmaster"] = relationship
    # processing data
    for data in data_list:
        data['productmasterid'] = database_session.query(productmaster).filter_by(name = data['name']).first().id
        new_data = product(
            productmasterid = data['productmasterid']
            ,price = data['price']
            ,originalprice = data['originalprice']
            ,discountpercentage = data['discountpercentage']
            ,platform = data['platform']
            ,createdate = data['createdate'])
        database_session.add(new_data)
        database_session.commit()
    # closing the databasee connection
    database_connection.close()