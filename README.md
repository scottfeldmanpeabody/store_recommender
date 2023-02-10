# Lobby-Based Retail Store Recommender

This project was build to support a company that provides a system for self-serve kiosks type convenience stores. These are mostly located in hotel lobbies. For a hotel operator, the store is not the primary business, but can be a big boost of additional revenue. Since operating the retail store is not neccesarily the core compentancy of the hotel management, whatever support can be given in running the store is highly valuable. 

## Data

The data provided for this project is propriety, and is not included in this repository. For development purposes, a copy of at PostgreSQL was obtained locally and queried directly.

## Product Recommender

The first recommender was build to suggest what additional products the store should be carrying. Since space is often limited,particularly for refrigerated items, suggestion of which products to stop carrying is also provided. Because having a variety of product categories available is key for customer satistfaction in this industry, products are calculated on a per-category basis. Briefly,

1. Each hotel is clustered into groups of similar hotels.
2. The top selling products for that hotel in a particular category over a particular data range are calculated.
3. Top products for that cluster of hotels as well as nationally are also calculated.
4. If the hotel is not carrying a product in the top n products, then the missing product(s) are suggested. (n defaults to 5, but is a user-adjustable parameter should one desire more or fewer products in a particular category)
5. In order to accomodate space for new products, if the hotel is carrying products that are not in the top n, AND these products make of less than x% (defaults to 10%) of sales in that category, suggestions for products to remove are also given.

#### Clustering

Hotels were grouped using a hierarchical clustering model. In this model, each data point is taken individually and then grouped

![hierarchical clustering diagram](https://github.com/scottfeldmanpeabody/convenience_kiosk_recommender/blob/master/img/hierarchical_clustering.png)

*Hierachical clustering. The top chart goes down 100 levels for illustative purposes. In practice, the clustering starts with each individual data point until they're all in one group at the top. You can then back down to however many groups you deem appropriate. In this case, 5 groupings were used*

The 5 groupings for the end model were based on a mixture of parameters. However, the most distinguishing parameter for each group is provided below:

0. Select Service (hotels providing only a selection of services, such as breakfast)
1. Full Service (hotels providing most services you could think of: e.g. dry-cleaning or shoe shines)
2. Flyover States (located in the middle of the US)
3. Campus-Located (hotels based on or near large universities or military bases)
4. Extended Stay (hotels wher eyou might expect to stay weeks rather than days)


#### User Interface.

An web app was built using Flask in order to deploy this recommender.

Parameters are entered into this screen:

![product recommender screen shot](https://github.com/scottfeldmanpeabody/convenience_kiosk_recommender/blob/master/img/product_recommender.png)
*Screen shot of the product recommender*


Should the property code for the hotel be unknown, a lookup table is provided:

![lookup table screenshot](https://github.com/scottfeldmanpeabody/convenience_kiosk_recommender/blob/master/img/property_lookup.png)
*Screen shot of the lookup table*

#### Output

An example output is shown below:

For store #XXXXX BrandX, Anytown, USA on some date:

Your top products in Beverage: Soda:
1. Coca-Cola, Diet Soda, 20 Oz, Bottle: 27.7%
2. Coca-Cola, Classic Soda, 20 Oz, Bottle: 16.5%
3. Coca-Cola, Zero, 20 Oz, Bottle: 15.0%
4. Coca-Cola, Cherry Coca-Cola, 20 Oz, Bottle: 6.5%
5. Sprite, Lemon Lime, 20 Oz, Bottle: 5.8%

Cluster top products:
1. Coca-Cola, Classic Soda, 20 Oz, Bottle: 44.5%
2. Coca-Cola, Diet Soda, 20 Oz, Bottle: 23.5%
3. Sprite, Lemon Lime, 20 Oz, Bottle: 14.4%
4. Coca-Cola, Zero, 20 Oz, Bottle: 9.5%
5. Dr. Pepper, 20 Oz, Bottle: 8.1%

National top product:
1. Coca-Cola, Classic Soda, 20 Oz, Bottle: 39.8%
2. Coca-Cola, Diet Soda, 20 Oz, Bottle: 29.2%
3. Sprite, Lemon Lime, 20 Oz, Bottle: 15.2%
4. Coca-Cola, Zero, 20 Oz, Bottle: 8.3%
5. Dr. Pepper, 20 Oz, Bottle: 7.6%

**The following prouduct is in the cluster top 5 but not stocked by this hotel**

Stocking suggestions:
1. Dr. Pepper, 20 Oz, Bottle

**The following products are not in the cluster top 5. Also, they collectively represent less than 10% of total sales in this category (Ginger Lime Diet Coke just spans the 10% barrier)**

Consider discontinue stocking:
1. Diet Coke, Ginger Lime, 12 Oz, Can: 3.1%
2. Diet Coke, Twisted Mango, 12 Oz, Can: 2.7%
3. Fanta, Orange, 20 Oz, Bottle: 2.3%
4. Fanta, Pineapple, 20 Oz, Bottle: 1.5%
5. Diet Coke, Zesty Blood Orange, 12 Oz, Can: 1.2%






