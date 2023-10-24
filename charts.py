#!/usr/bin/env python
# coding: utf-8

# In[36]:


import pandas as pd
import matplotlib.pyplot as plt

def createCumulativePnl():
    df = pd.read_excel('C:\\Users\\Dell\\Desktop\\wqu capstorne\\3611_code_results\\Results\\wait and trade\\DS_Banknifty_individual\\dte4_15.xlsx')

    # Set the index to use row numbers
    df = df.reset_index()

    # Create a larger figure
    plt.figure(figsize=(12, 6))

    # Plot all columns as lines
    for column in df.columns:
        if column != 'index':
            plt.plot(df['index'], df[column], label=column)

    # Add labels and legend outside the graph
    plt.xlabel('Number of trades')
    plt.ylabel('PNL in Premium Points')
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))

    # Add a title to the chart
    plt.title('4DTE with 15% downward movement')

    # Show the plot
    plt.show()
    
createCumulativePnl()


# In[45]:


import pandas as pd
from matplotlib.ticker import PercentFormatter
import matplotlib.pyplot as plt

def final_graph():
    # Sample data (replace this with your own data)
    df = pd.read_excel('C:\\Users\\Dell\\Desktop\\wqu capstorne\\3611_code_results\\Results\\wait and trade\\DS_Banknifty_individual\\final_results.xlsx')

    df['Date'] = pd.to_datetime(df['Date'])

    # Create subplots with shared x-axis
    fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(10, 6))

    # Plot Cumulative Returns
    ax1.plot(df['Date'], df['Cumulative_Return'], label='Cumulative Returns', color='blue')
    ax1.set_ylabel('Cumulative Returns', color='blue')
    ax1.legend(loc='upper left')
    
    # Format y-axis as percentages
    ax1.yaxis.set_major_formatter(PercentFormatter(1.0))

    # Plot Drawdown
    ax2.plot(df['Date'], df['DD_Return'], label='Drawdown', color='red')
    ax2.set_ylabel('Drawdown', color='red')
    ax2.legend(loc='upper left')
    
    # Format y-axis as percentages
    ax2.yaxis.set_major_formatter(PercentFormatter(1.0))
    
    # Set common x-axis label
    plt.xlabel('Date')

    # Show the plot
    plt.tight_layout()
    plt.show()
    
final_graph()


# In[ ]:




