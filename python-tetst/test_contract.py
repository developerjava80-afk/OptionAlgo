
import pandas as pd
from process_call_data import process_call_data
from process_put_data import process_put_data
from db_connector import DBConnector

def main():
    # Prompt user for date and contract
    user_input = input("Enter date (dd-mm-yyyy) and contract (e.g. C48200 or P48200), separated by space: ")
    try:
        date_str, contract = user_input.strip().split()
    except ValueError:
        print("Invalid input format. Example: 01-02-2024 C48200")
        return

    # Convert date to table name pattern (e.g. 01-02-2024 -> 01022024)
    table_name_pattern = date_str.replace('-', '')

    # Connect to DB and get all tables
    config = {
        'user': 'root',
        'password': 'hindus',
        'host': 'localhost',
        'database': 'market_data',
    }
    db = DBConnector(config)
    dfs, table_names = db.get_tables()

    # Find the table for the given date
    selected_df = None
    selected_table = None
    for df, tname in zip(dfs, table_names):
        if table_name_pattern in str(tname):
            selected_df = df
            selected_table = tname
            break
    if selected_df is None:
        print(f"No table found for date {date_str} (pattern: {table_name_pattern})")
        return

    # Check if contract exists in columns
    if contract not in selected_df.columns:
        print(f"Contract {contract} not found in table {selected_table}")
        return

    # Process the contract
    if contract.startswith('C'):
        result_df = process_call_data(selected_df, selected_table, [contract])
        print(f"Processed call contract {contract} in table {selected_table}")
    elif contract.startswith('P'):
        result_df = process_put_data(selected_df, selected_table, [contract])
        print(f"Processed put contract {contract} in table {selected_table}")
    else:
        print("Contract must start with 'C' or 'P'")
        return

    print(result_df)
    print(f"Report generated for {contract} on {date_str}.")

if __name__ == "__main__":
    main()
