import pandas as pd
import os
import datetime

def save_results_to_excel(results, output_folder=None):
    if output_folder is None:
        output_folder = r'C:\Users\shiva\OneDrive\Documents\algo results'
    os.makedirs(output_folder, exist_ok=True)
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = os.path.join(output_folder, f'results_{timestamp}.xlsx')
    results_df = pd.DataFrame(results)
    # Only keep Contract and PnL columns
    results_df = results_df[['Contract', 'PnL']]
    results_df.to_excel(output_path, index=False)
    print(results_df)
    return output_path

def save_row_details_report(row_details, table_name, output_folder=None):
    if output_folder is None:
        output_folder = r'C:\Users\shiva\OneDrive\Documents\algo results'
    os.makedirs(output_folder, exist_ok=True)
    if not row_details or not isinstance(row_details, list) or not any(row_details):
        print(f"No row details to save for {table_name}.")
        return None
    report_path = os.path.join(output_folder, f'{table_name}_details.xlsx')
    df = pd.DataFrame(row_details)
    if df.empty:
        print(f"Row details DataFrame is empty for {table_name}, not saving file.")
        return None
    df.to_excel(report_path, index=False)
    #print(f"Detailed row-by-row report saved to {report_path}")
    return report_path
