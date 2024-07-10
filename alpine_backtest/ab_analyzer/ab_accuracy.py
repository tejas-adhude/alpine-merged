import pandas as pd
from alpine import ConsoleColors

def PandL_and_accuracy_summary(input_csv_path:str,output_file_dir:str):
    # Load the CSV file
    print(ConsoleColors.YELLOW+f"{input_csv_path}"+ConsoleColors.RESET)
    
    file_name=input_csv_path.split("\\")[-1].split(".")[0]
    symbol=file_name.split("_")[0]
    
    try:
        df = pd.read_csv(input_csv_path)
    except pd.errors.EmptyDataError:
        return

    # Convert the 'Date' column to datetime format
    df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')

    # Convert 'buyT' and 'sellT' to time format
    df['buyT'] = pd.to_datetime(df['buyT'], format='%H:%M:%S').dt.time
    df['sellT'] = pd.to_datetime(df['sellT'], format='%H:%M:%S').dt.time

    # Convert 'buyP', 'sellP', and 'PandL' to float
    df['buyP'] = df['buyP'].astype(float)
    df['sellP'] = df['sellP'].astype(float)
    df['PandL'] = df['PandL'].astype(float)

    # Calculate overall trading accuracy
    df['Profitable'] = df['buyP'] < df['sellP']
    profitable_trades = df['Profitable'].sum()
    loss_trades = len(df) - profitable_trades

    # Calculate PandL sum overall
    total_pandl = df['PandL'].sum()

    # Group by day, month, and year and calculate the sum of 'PandL' and trade counts
    daily_summary = df.groupby(df['Date'].dt.date).agg({
        'PandL': 'sum',
        'Profitable': 'sum'
    }).reset_index()
    daily_summary['LossTradeCount'] = df.groupby(df['Date'].dt.date)['Profitable'].apply(lambda x: len(x) - x.sum()).values
    daily_summary['AccuracyPercentage'] = (daily_summary['Profitable'] / (daily_summary['Profitable'] + daily_summary['LossTradeCount'])) * 100

    monthly_summary = df.groupby(df['Date'].dt.to_period('M')).agg({
        'PandL': 'sum',
        'Profitable': 'sum'
    }).reset_index()
    monthly_summary['LossTradeCount'] = df.groupby(df['Date'].dt.to_period('M'))['Profitable'].apply(lambda x: len(x) - x.sum()).values
    monthly_summary['AccuracyPercentage'] = (monthly_summary['Profitable'] / (monthly_summary['Profitable'] + monthly_summary['LossTradeCount'])) * 100

    yearly_summary = df.groupby(df['Date'].dt.to_period('Y')).agg({
        'PandL': 'sum',
        'Profitable': 'sum'
    }).reset_index()
    yearly_summary['LossTradeCount'] = df.groupby(df['Date'].dt.to_period('Y'))['Profitable'].apply(lambda x: len(x) - x.sum()).values
    yearly_summary['AccuracyPercentage'] = (yearly_summary['Profitable'] / (yearly_summary['Profitable'] + yearly_summary['LossTradeCount'])) * 100

    # Rename columns
    daily_summary.columns = ['Date', 'PandL', 'ProfitableTradeCount', 'LossTradeCount', 'AccuracyPercentage']
    monthly_summary.columns = ['Month', 'PandL', 'ProfitableTradeCount', 'LossTradeCount', 'AccuracyPercentage']
    yearly_summary.columns = ['Year', 'PandL', 'ProfitableTradeCount', 'LossTradeCount', 'AccuracyPercentage']

    # Save the results to CSV files
    daily_summary.to_csv(rf'{output_file_dir}\{symbol}\{file_name}_daily_summary.csv', index=False)
    monthly_summary.to_csv(rf'{output_file_dir}\{symbol}\{file_name}_monthly_summary.csv', index=False)
    yearly_summary.to_csv(rf'{output_file_dir}\{symbol}\{file_name}_yearly_summary.csv', index=False)

