create table online_shop.public.productmaster(
	id serial
	-- ,product_id varchar(255)
	,"name" varchar(255)
	,"type" varchar(255)
	,detail text
	,createdate date
	,primary key (id));
comment on column public.productmaster.id is 'Unique identifier for the product master.';
-- comment on column public.productmaster.product_id is 'Natural key based on product page URL.';
comment on column public.productmaster."name" is 'Name of the product.';
comment on column public.productmaster."type" is 'Type or category of the product.';
comment on column public.productmaster.detail is 'Additional details or description of the product.';
comment on column public.productmaster.createdate is 'Timestamp indicating the date and time when the data was crawled.';

create table online_shop.public.product(
	id serial
	,productmasterid int
	,price int8
	,originalprice int8
	,discountpercentage float
	,platform varchar(255)
	,createdate date
	,primary key (id)
	,foreign key (productmasterid) references public.productmaster(id));
comment on column public.product.id is 'Unique identifier for the product entry.';
comment on column public.product.productmasterid is 'Foreign key referencing the product master associated with this entry.';
comment on column public.product.price is 'Current price of the product.';
comment on column public.product.originalprice is 'Original price of the product.';
comment on column public.product.discountpercentage is 'Discount percentage applied to the product.';
comment on column public.product.platform is 'Platform from which the product data was crawled.';
comment on column public.product.createdate is 'Timestamp indicating the date and time when the data was crawled.';

create table online_shop.public.pricerecommendation(
	productmasterid int
	,price int8
	,"date" date
	,foreign key (productmasterid) references public.productmaster(id));
comment on column public.pricerecommendation.productmasterid is 'Foreign key referencing the product master associated with this recommendation.';
comment on column public.pricerecommendation.price is 'Predicted price recommendation for the corresponding product master.';
comment on column public.pricerecommendation."date" is 'Date for which the price recommendation is generated.';

create database airflow_database;

create database api_user_access;

\c api_user_access;

CREATE TABLE api_user_access.public.users (
	id serial4 NOT NULL
	,username varchar NOT NULL
	,"password" varchar NOT NULL
	,CONSTRAINT users_pk PRIMARY KEY (id)
	,CONSTRAINT users_unique UNIQUE (username)
);
