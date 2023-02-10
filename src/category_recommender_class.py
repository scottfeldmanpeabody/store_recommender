import pandas as pd
import numpy as np
import psycopg2 as pg2
import pandas.io.sql as sqlio
import sys
sys.path.append("..")
from src.get_clusters import get_table, push_table

class CategoryRecommender(object):
    '''
    Recommends products based on clusters of hotels
    '''

    def __init__(self, property_code, category, month, num = 5):
        self.sold = get_table('select * from product_category_recommender')
        self.property_code = property_code
        self.category = category
        self.month = month
        self.num = num
        self.sold_by_store = sold_by_store(property_code, category, month)

    def sold_by_store(self.property_code, self.category, self.month):
        top_store = self.sold[['agg_ward','property_code','category_name','description', 'transaction_month', 'number_sold']][sold.number_sold > 0]. \
            groupby(['agg_ward','property_code','category_name', 'description', 'transaction_month'], as_index=False).sum(). \
            sort_values(by=['agg_ward','property_code','category_name', 'transaction_month', 'number_sold'], ascending=False)    
        
        out = top_store[(top_store.property_code == property_code) & 
                        (top_store.category_name == category) & 
                        (top_store.transaction_month == month)]
        total_sold = np.sum(out.number_sold)
        out.loc[:, 'pct_of_sold'] = out['number_sold']/total_sold
        out.loc[:,'cum_pct'] = out['pct_of_sold'].cumsum()
        
        return out

    def top_sold_by_cluster(cluster, category = self.category, month = self.month, num = self.num):
        top_cluster = self.sold[['agg_ward','category_name','description', 'transaction_month','number_sold']][sold.number_sold > 0]. \
            groupby(['agg_ward','category_name', 'description', 'transaction_month'], as_index=False).sum(). \
            sort_values(by=['agg_ward','category_name', 'transaction_month', 'number_sold'], ascending=False)

        return top_cluster[(top_cluster.agg_ward == cluster) & 
                        (top_cluster.category_name == category) & 
                        (top_cluster.transaction_month == month)].head(num)

    def top_sold_overall(category = self.category, month = self.month, num = self.num):
        top_overall = self.sold[['category_name', 'description', 'transaction_month','number_sold']][sold.number_sold > 0]. \
            groupby(['category_name', 'description', 'transaction_month'], as_index=False).sum(). \
            sort_values(by=['category_name', 'transaction_month', 'number_sold'], ascending=False)
        
        return top_overall[(top_overall.category_name == category) & 
                        (top_overall.transaction_month == month)].head(num)

    def compare_products(property_code = self.property_code, category = self.category, month = self.month, num = self.num):
        '''
        inputs: property_code
                category = product_category
                month = transaction_month
                num = number of products to compare
        outputs: print outs of top selling products in that category by this store vs. 
                store clusters and nationaly. As well as suggestions for different products
                in that category to stock and products to discontinue
        '''
        
        
        top_store_prods = sold_by_store(property_code, category, month).head(num)
        store_prods = sold_by_store(property_code, category, month)
        clust = np.max(sold[(self.sold.property_code == property_code) &
                            (self.sold.category_name == category)].agg_ward) # the max doesn't do anything all the clusters are the same
        clust_prods = top_sold_by_cluster(clust, category, month, num)
        tot_clust = np.sum(clust_prods.number_sold)
        natl_prods = top_sold_overall(category, month)
        tot_natl = np.sum(natl_prods.number_sold)
        
        desc = self.sold[['flag_name','city','state']][self.sold.property_code == property_code].iloc[0]
        print('For store #{0}, {1}, {2}, {3} {4}'.format(property_code,
                                                        desc.flag_name,
                                                        desc.city,
                                                        desc.state,
                                                        month))
        
        if store_prods.shape[0] == 0:
            print('No products sold in {}'.format(category))
            
            if natl_prods.shape[0] < num:
                n = natl_prods.shape[0]
            else:
                n = num
            print('\nNational top products in {}:'.format(category))
            for i in range(n):
                print('{0}. {1}: {2}%'.format(i+1, natl_prods.description.iloc[i],
                                        round(100 * natl_prods.number_sold.iloc[i]/tot_natl,1)))
            return print('')
        
        if sold_by_store(property_code, category, month).shape[0] < num:
            n = sold_by_store(property_code, category, month).shape[0]
        else:
            n = num
        print('\nYour top products in {}:'.format(category))
        for i in range(n):
            print('{0}. {1}: {2} units, {3}%'.format(i+1, top_store_prods.description.iloc[i],
                                            top_store_prods.number_sold.iloc[i], 
                                                    round(100 * top_store_prods.pct_of_sold.iloc[i],1)))
        
        if clust_prods.shape[0] < num:
            n = clust_prods.shape[0]
        else:
            n = num
        print('\nCluster({}) top products:'.format(clust))
        for i in range(n):
            print('{0}. {1}: {2}%'.format(i+1, clust_prods.description.iloc[i],
                                    round(100 * clust_prods.number_sold.iloc[i]/tot_clust,1)))
        
        if natl_prods.shape[0] < num:
            n = natl_prods.shape[0]
        else:
            n = num
        print('\nNational top product:')
        for i in range(n):
            print('{0}. {1}: {2}%'.format(i+1, natl_prods.description.iloc[i],
                                    round(100 * natl_prods.number_sold.iloc[i]/tot_natl,1)))
        
        '''
        products suggested for removal are not in top 5 of cluster and are in the
        bottom 10% cumulative of sales
        '''
        
        #change this to products that aren't in the top 10, not top 5
        to_remove = store_prods[(~store_prods.description.isin(clust_prods.description.unique())) &
                            (store_prods.cum_pct > .9)]
        
        if set(clust_prods.description) - set(store_prods.description) == set():
            print('\nYou are selling the top products already!')
            if to_remove.shape[0] > 0:
                print('\nConsider discontinue stocking:')
                for i in range(to_remove.shape[0]):
                    print('{0}. {1}: {2} units, {3}%'.format(i+1, to_remove.description.iloc[i],
                                                            to_remove.number_sold.iloc[i],
                                                            round(100 * to_remove.pct_of_sold.iloc[i],1))) 
        else:
            print('\nStocking suggestions:')
            add = list(set(clust_prods.description) - set(store_prods.description))
            for idx, item in enumerate(add):
                print('{0}. {1}'.format(idx+1, item))
            if to_remove.shape[0] > 0:
                print('\nConsider discontinue stocking:')
                for i in range(to_remove.shape[0]):
                    print('{0}. {1}: {2} units, {3}%'.format(i+1, to_remove.description.iloc[i],
                                                            to_remove.number_sold.iloc[i],
                                                            round(100 * to_remove.pct_of_sold.iloc[i],1)))





if __name__ == "__main__":
    
    print('getting data (this may take awhile)... ')

    recommender = CategoryRecommender('SPICC', 'Beverage: Soda', '2019-09', 5)

    print('analyzing...')

    recommender.compare_products()