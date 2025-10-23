from process_option_data import process_option_data


def process_call_data(df, table_name, call_columns):
    """Backward-compatible wrapper that delegates to process_option_data."""
    return process_option_data(df, table_name, call_columns)

