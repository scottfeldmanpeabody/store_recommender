import pandas as pd
import numpy as np
import psycopg2 as pg2
import pandas.io.sql as sqlio
from sklearn.cluster import AgglomerativeClustering
from sqlalchemy import create_engine
import io

def get_table(sql, db = 'xxx', user = 'postgres',host= 'localhost', port = '0000'):
    conn = pg2.connect(dbname=db, user=user, host=host, port=port)
    table = sqlio.read_sql_query(sql, conn)
    conn = None
    return table

def push_table(df, table, db = 'xxx', user = 'postgres',
               host= 'localhost', port = '0000'):
    '''
    inputs:
        df = dataframe to push
        table = table name to write in database
        db = database
        user, host, port = database connection info
    
    outputs:
        writes table to DB. Overwrites if table already exists
    '''
    engine = create_engine('postgresql+psycopg2://'+user+':@'+host+':'+port+'/'+db)
    df.head(0).to_sql('property_clusters', engine, if_exists='replace',index=False) #truncates the table
    
    conn = engine.raw_connection()
    cur = conn.cursor()
    output = io.StringIO()
    df.to_csv(output, sep='|', header=False, index=False)
    output.seek(0)
    contents = output.getvalue()
    cur.copy_from(output, table, sep = '|', null="") # null values become ''
    conn.commit()

if __name__ == "__main__":

    # Connect to DB and Get Data

    print('getting data...')
    sql = '''select p.id property_id
        , p.property_code
        , p.name property_name
        , p.address
        , p.city
        , p.state
        , p.zip
        , p.sales_tax_rate
        , p.alcohol_tax_rate
        , p.tobacco_tax_rate
        , p.management_company_id
        , p.flag_id
        , f.name flag_name
        , f.brand_id
        , b.name brand_name
        , p.kind
        , p.guest_profile
        , p.currency_id
        , p.location_type
        , p.rooms

    from table1 p

    LEFT JOIN table2 AS b
        ON p.brand_id = b.id
                
    LEFT JOIN table3 AS f
        ON p.flag_id = f.id
        
    ;'''
    props = get_table(sql)
    print('data received.')


    # Feature Engineering
    print('creating features...')

    ## Currency code => Currency
    props['currency'] = np.where(props.currency_id == 1, 'USD', 'CAD')

    ## Group locations into zones of first digit from zip
    props.zip = np.where(props.zip.str.isnumeric(),props.zip.astype(str).str[0],'can')

    ## Number of Properties Under Managment
    mgmt = pd.DataFrame(props['management_company_id'].value_counts()).reset_index()
    mgmt.rename(columns={'index':'management_company_id',
                        'management_company_id':'props_under_mgmt'}, inplace=True)
    props = props.merge(mgmt, on=('management_company_id'))

    ## Selecting Columns
    props_mod = props.copy()
    index_col = ['property_id'] # column to use as index
    numeric_cols = ['props_under_mgmt','rooms',
                    #'alcohol_tax_rate', 'sales_tax_rate', 'tobacco_tax_rate'
                ]
    dummy_cols = ['kind','guest_profile','location_type',
                'currency','flag_name','zip']
    drop_cols = list(set(props.columns) - set(index_col) - set(numeric_cols))

    props_mod = props_mod.merge(pd.get_dummies(data = props_mod,columns = dummy_cols,drop_first=True))

    ## One-Hot Encoding
    props_mod = props.copy() #initialize modeling df
    index_col = ['property_id'] #saved as index of modeling df
    numeric_cols = ['props_under_mgmt','rooms',
                    #'alcohol_tax_rate', 'sales_tax_rate', 'tobacco_tax_rate' #these columns not well populated
                ] #included numerical columns in model
    dummy_cols = ['kind','guest_profile','location_type',
                'currency','flag_name','zip'] #columns to one-hot encode
    drop_cols = list(set(props.columns) - set(index_col) - set(numeric_cols)) #columns not used for model
    props_mod = props_mod.merge(pd.get_dummies(data = props_mod,columns = dummy_cols,drop_first=True)) #create dummies
    props_mod = props_mod.drop(drop_cols , axis = 1) #drop unused features
    props_mod.index = props_mod.property_id #sets index by id
    props_mod.drop(index_col, axis = 1 , inplace = True) #drop id columns since we don't want to model on it

    ## Clustering
    print('creating clusters...')
    agg_ward = AgglomerativeClustering(n_clusters=6).fit_predict(props_mod) #define clusters
    props['cluster'] = agg_ward # add cluster definition to original dataset

    ## Write Table to DB
    print('writing table to db...')
    push_table(props, 'property_clusters')
    print('complete.')
