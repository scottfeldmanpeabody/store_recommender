import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.interpolate import CubicSpline, UnivariateSpline, interp1d
from scipy import interpolate, stats

class prod_subset(object):
    '''
    Looks at perfomance of indiviudal products
    
    Inputs: 
        df = DataFrame containing sales data
        description = product in question
        (optional) month = subset by transaction month
        (optional) cluster = subset property_code cluster
        
    Produces a subsetted DataFrame of sales per property of that product
        
    Methods:
        return_df() : returns a DataFrame of the subsetted data
        optimiz_price() : naively assumes a uniform distribution and finds the max revenue
        scatplot() :  plots a scatter plot of number sold and revenue as a function of price
        boxplot() :  plots a box plot of number sold and revenue as a function of price
        dists() : plots the distribution of price, number sold, and revenue
        
    Attributes:
        best_price_ : estimated best price to set on an item to maximize profits
        best_revenue_ : the estimated median revenue when using the best price
        best_sales_ : the estimated median number of sales when using the best price
    '''
    
    def __init__(self, df, description, month = None, cluster = None):
        self.df = df
        self.description = description
        self.month = month
        self.cluster = cluster
        self.data = df[df.description == description]
        if cluster:
            self.data = self.data[self.data.cluster == self.cluster]
        if month:
            self.data = self.data[self.data.transaction_month == self.month]
        self.data = self.data.groupby('unit_price').mean()[['number_sold']].reset_index()
        self.data['revenue'] = self.data.unit_price * self.data.number_sold
        self.best_price_, self.best_rev_, self.best_sales_ = self.optimize_price()
        
    def return_df(self):
        '''
        returns a DataFrame of the subsetted data
        '''
        return self.data
    
    def optimize_price(self):
        '''
        naively assumes a uniform distribution and finds the max revenue
        '''
        if self.data.shape[0] < 2:
            return None, None, None
        else:
            x = self.data['unit_price']
            y0 = self.data['number_sold']
            y1 = self.data['revenue']
            
            mn = round(min(x))
            mx = np.ceil(max(x))
            rng = mx - mn
            price_bins = np.linspace(mn,mx,(rng * 4) +1)
            bin_x = np.digitize(x, price_bins, right=True)
            mean,std= stats.norm.fit(bin_x)
            y_fit = stats.norm.pdf(bin_x, mean, std)
            best_price = price_bins[np.unique(bin_x)][bin_x[np.argmax(y_fit)]]
            if np.max(stats.binned_statistic(x, y1, statistic='median')[0]):
                max_rev = np.max(stats.binned_statistic(x, y1, statistic='median')[0])
            else:
                max_rev = np.median(y1[bin_x == bin_x[np.argmax(y_fit)]])
            if np.max(stats.binned_statistic(x, y0, statistic='median')[0]):
                max_sales = np.max(stats.binned_statistic(x, y0, statistic='median')[0])
            else:
                max_sales = np.median(y0[bin_x == bin_x[np.argmax(y_fit)]])
            return best_price, max_rev, max_sales
    
    def scatplot(self):
        '''
        returns number sold and revenue as a function of price
        '''
        if self.data.shape[0] < 2:
            return 'Not enough sales for selected product to plot'

        x = self.data['unit_price']
        y0 = self.data['number_sold']
        #plot splines to look for pattern
        spl0 = UnivariateSpline(x, y0)
        spl0.set_smoothing_factor(1000000)
        y1 = self.data['revenue']
        spl1 = UnivariateSpline(x, y1)
        spl1.set_smoothing_factor(1000000)

        fig, ax = plt.subplots(1,2, figsize = (9,4))

        #Number Sold vs. Unit Price
        sns.scatterplot(x, y0, ax = ax[0])
        ax[0].set_xlabel('Unit Price')
        ax[0].set_ylabel('Average Number Sold')
        ax[0].plot(x, spl0(x), c = 'b', label='Spline Fit')
        ax[0].legend()
        
        #Revenue vs. Unit Price
        sns.scatterplot(x, y1, ax = ax[1])
        ax[1].set_xlabel('Unit Price')
        ax[1].set_ylabel('Average Revenue')
        ax[1].plot(x, spl1(x), c = 'b', label='Spline Fit')
        ax[1].legend()
        
        if self.cluster != None:
            clust_descrip = ' | Cluster: {}'.format(self.cluster)
        else:
            clust_descrip = ''
        plt.suptitle(self.description + clust_descrip)
        fig.savefig('static/sales_scatter.png')
    
    def boxplots(self):
        '''
        plots a box plot of number sold and revenue as a function of price
        '''
        if self.data.shape[0] < 1:
            return "Not enough sales for selected product to plot"
        else:
            x = self.data['unit_price']
            y0 = self.data['number_sold']
            y1 = self.data['revenue']
            
            mn = round(min(x))
            mx = np.ceil(max(x))
            rng = mx - mn
            price_bins = np.linspace(mn,mx,(rng * 4) +1)
            bin_x = np.digitize(x, price_bins, right=True)
            mean,std= stats.norm.fit(bin_x)
            y_fit = stats.norm.pdf(bin_x, mean, std)

            fig, ax = plt.subplots(1,2, figsize = (12,4))
            
            #Number Sold vs. Unit Price
            sns.boxplot(x = bin_x, y = y0, color = 'lightblue', ax = ax[0])
            sns.stripplot(x = bin_x, y = y0, color = 'red', size = 3, ax = ax[0])
            ax[0].plot(bin_x, (y_fit/np.max(y_fit))*self.best_sales_, c = 'green') # scale to box plot
            
            ax[0].set_title('Quantity vs. Price Bins')
            ax[0].set_xticklabels(price_bins[np.unique(bin_x)], rotation = 60)
            ax[0].set_xlabel('Price ($)')
            ax[0].set_ylabel('Number Sold')
            
            #Number Revenue vs. Unit Price
            sns.boxplot(x = bin_x, y = y1, color = 'lightblue', ax = ax[1])
            sns.stripplot(x = bin_x, y = y1, color = 'red', size = 3, ax = ax[1])
            ax[1].plot(bin_x, (y_fit/np.max(y_fit))*self.best_rev_, c = 'green') # scale to box plot
    
            ax[1].set_title('Revenue vs. Price Bins')
            ax[1].set_xticklabels(price_bins[np.unique(bin_x)], rotation = 60)
            ax[1].set_xlabel('Price ($)')
            ax[1].set_ylabel('Revenue ($)')
            
            if self.cluster != None:
                clust_descrip = ' | Cluster: {}'.format(self.cluster)
            else:
                clust_descrip = ''
            plt.suptitle(self.description + clust_descrip)
            fig.savefig('static/sales_boxplot.png')
    
    def dists(self):
        '''
        plots the distribution of price, number sold, and revenue
        '''
        if self.data.shape[0] < 2:
            return 'Not enough sales for selected product to plot'
        else:
            fig, ax = plt.subplots(1,3, figsize = (12,4))

            cols = list(self.data.columns)

            for i, col in enumerate(cols):
                #ax[i].hist(self.data[col])
                ax[i] = sns.distplot(self.data[col], bins = 15, ax = ax[i])
            ax[0].set_ylabel('Probability Density')
            if self.cluster != None:
                clust_descrip = ' | Cluster: {}'.format(self.cluster)
            else:
                clust_descrip = ''
            plt.suptitle('Distributions for ' + self.description + clust_descrip)
            fig.savefig('static/sales_distributions.png')
          