import pandas as pd
from process_call_data import process_call_data
from process_put_data import process_put_data
from db_connector import DBConnector

def main():
    # Prompt user for date parts and contract
    day = input("Enter day (dd): ").zfill(2)
    month = input("Enter month (mm): ").zfill(2)
    year = input("Enter year (yyyy): ")
    contract = input("Enter contract (e.g. C48200 or P48200): ").strip()
    date_str = f"{month}-{day}-{year}"

    # Convert to MMDDYYYY for table search
    table_name_pattern = date_str

    # Connect to DB and get all tables
    config = {
        'user': 'root',
        'password': 'hindus',
        'host': 'localhost',
        'database': 'market_data',
    }
    db = DBConnector(config)
    dfs, table_names = db.get_tables()

    # Print all available table names
    print("Available tables:")
    for tname in table_names:
        print(f"  {tname}")

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
    # Trim the table name to 20 characters before passing to processing functions
    table_arg = str(selected_table)[:20]
    if contract.startswith('C'):
        result_df = process_call_data(selected_df, table_arg, [contract])
        print(f"Processed call contract {contract} in table {selected_table} (arg: {table_arg})")
    elif contract.startswith('P'):
        result_df = process_put_data(selected_df, table_arg, [contract])
        print(f"Processed put contract {contract} in table {selected_table} (arg: {table_arg})")
    else:
        print("Contract must start with 'C' or 'P'")
        return

    print(result_df)
    print(f"Report generated for {contract} on {date_str}.")

if __name__ == "__main__":
    main()
