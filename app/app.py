# Demonstrates Bootstrap version 3.3 Starter Template
# available here: https://getbootstrap.com/docs/3.3/getting-started/#examples

from flask import Flask, request, render_template
from flask_basicauth import BasicAuth
import pandas as pd
import numpy as np
import psycopg2 as pg2
import pandas.io.sql as sqlio
import sys
sys.path.append("..")
from src.get_clusters import get_table
from src.category_recommender import sold_by_store, top_sold_by_cluster, top_sold_overall, compare_products
from src.price_optimizer import prod_subset

app = Flask(__name__)

app.config['BASIC_AUTH_USERNAME'] = 'impulsify'
app.config['BASIC_AUTH_PASSWORD'] = 'superhighsecurity'
app.config['BASIC_AUTH_FORCE'] = True
basic_auth = BasicAuth(app)

#sold = get_table('SELECT * FROM product_category_recommender')
sql = 'SELECT DISTINCT property_code FROM product_category_recommender ORDER BY property_code'
prop_list = list(get_table(sql).iloc[:,0])
sql = 'SELECT DISTINCT transaction_month FROM product_category_recommender ORDER BY transaction_month DESC'
month_list = list(get_table(sql).iloc[:,0])
sql = 'SELECT DISTINCT category_name FROM product_category_recommender ORDER BY category_name'
category_list = list(get_table(sql).iloc[:,0])

# home page
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/product_recommender', methods=['GET', 'POST'])
def product_recommender():
    
    categories = category_list
    months = month_list
    nums = [5, 1, 2, 3, 4, 6, 7, 8, 9, 10]
    return render_template('product_recommender.html', categories = categories, months = months, nums = nums)

@app.route('/product_recommender_results', methods=['GET', 'POST'])
def product_recommender_results():
    property = request.form['property'] 
    category = request.form['category']
    month = request.form['month']
    num = request.form['num']
    
    SQL = """SELECT * 
            FROM product_category_recommender 
            WHERE transaction_month = '{0}'
            """.format(month)
    sold = get_table(SQL)

    recommendation = compare_products(property, category, month, int(num), sold)

    return render_template('product_recommender_results.html', property=property, recommendation=recommendation)

@app.route('/property_lookup', methods=['GET', 'POST'])
def property_lookup():
    sql = 'SELECT DISTINCT flag_name FROM product_category_recommender ORDER BY flag_name'
    flags = []
    flags.append(None)
    flags = flags + list(get_table(sql).iloc[:,0])
    sql = 'SELECT DISTINCT city FROM product_category_recommender ORDER BY city'
    cities = list(get_table(sql).iloc[:,0])
    sql = 'SELECT DISTINCT state FROM product_category_recommender ORDER BY state'
    states = [None] + list(get_table(sql).iloc[:,0])

    city = None
    state = None

    if request.method == 'POST':
        city = request.form['city']
        prop_lookup = get_table("SELECT * FROM property_code_lookup WHERE city = '{}' ".format(city))
    #     if request.form['city']:
    #         city = request.form['city']
    #     state = request.form['state']
    #     flag_name = request.form['flag_name']
    # if city != None:
    #     prop_lookup = get_table("SELECT * FROM property_code_lookup WHERE city = '{}' ".format(city))
    # if state != None:
    #     prop_lookup = get_table("SELECT * FROM property_code_lookup WHERE state = '{}' ".format(state))
    # if flag_name != None:
    #     prop_lookup = get_table("SELECT * FROM property_code_lookup WHERE flag_name = '{}' ".format(flag_name))
    else:
        prop_lookup = get_table('SELECT * FROM property_code_lookup')
    return render_template('property_lookup.html', data = prop_lookup.to_html(), \
        flags = flags, cities = cities, states = states)

@app.route('/price_optimizer', methods=['GET', 'POST'])
def price_optimizer():
    #sql = 'SELECT DISTINCT description FROM product_category_recommender ORDER BY description'
    descriptions = []#list(get_table(sql).iloc[:,0])
    
    product_description = None
    sold = None
    best_price = None
    best_sales = None
    best_rev = None
    chart1 = None
    chart2 = None

    if request.method == 'POST':
        product_description = request.form['product_description']
        sql = "SELECT * FROM product_category_recommender WHERE description = '{}' ".format(product_description) 
        sold = get_table(sql)
        sold['unit_price'] = np.round(sold.dollars_sold / sold.number_sold, 2)
        prod = prod_subset(sold, product_description)
        print('description = {}'.format(prod.description))
        prod.dists()    
        prod.boxplots()
        best_price = '{0:.2f}'.format(prod.best_price_)
        best_sales = '{0:.0f}'.format(prod.best_sales_)
        best_rev = '{0:.0f}'.format(prod.best_rev_)
        chart1 = 'static/sales_boxplot.png'
        chart2 = 'static/sales_distributions.png'
        
        
    return render_template('price_optimizer.html', descriptions = descriptions, product_description = product_description, \
         sold = sold, best_price = best_price, best_rev = best_rev, best_sales = best_sales, chart1 = chart1, chart2 = chart2)

@app.route('/product_lookup', methods=['GET', 'POST'])
def product_lookup():
    category = None
    sql = '''SELECT *
                FROM product_category_xref 
                ORDER BY category_name, description
                '''
    if request.method == 'POST':
        category = request.form['category']
        sql = '''SELECT * 
                    FROM product_category_xref
                    WHERE category_name = '{}'
                    ORDER BY category_name, description
                    '''.format(category)
        
    products = get_table(sql)
    categories = list(get_table('SELECT name FROM categories ORDER BY name').iloc[:,0])

    return render_template('product_lookup.html', data = products.to_html(), categories = categories)

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, threaded=True, debug=True)
