import pandas as pd

def save_to_xlsx(result_dict, activity_dict, base_date, filepath='schedule_result.xlsx'):
    rows = []

    for task_name, result in result_dict.items():
        activity = activity_dict[task_name]

        start_offset = result['start']
        end_offset = result['end']
        start_date = base_date + start_offset
        end_date = base_date + end_offset

        rows.append({
            'block_name': task_name,
            'start_date': start_date,
            'end_date': end_date,
            'duration': activity.duration,
            'load_size': activity.load_size,
        })

    result_df = pd.DataFrame(rows)
    result_df.sort_values(by='start_date', inplace=True)

    result_df.to_excel(filepath, index=False)
