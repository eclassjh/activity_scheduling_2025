import pandas as pd

def save_to_csv(result_dict, activity_dict, base_date, filepath='schedule_result.csv'):
    rows = []

    for task_name, result in result_dict.items():
        activity = activity_dict[task_name]

        start_offset = result['start']
        end_offset = result['end']
        start_date = base_date + pd.Timedelta(days=start_offset)
        end_date = base_date + pd.Timedelta(days=end_offset)

        # M/D/YYYY 형식으로 변환
        start_date_str = start_date.strftime('%m/%d/%Y').lstrip("0").replace("/0", "/") 
        end_date_str = end_date.strftime('%m/%d/%Y').lstrip("0").replace("/0", "/")

        rows.append({
            '작업명': task_name,
            '시작일': start_date_str,
            '종료일': end_date_str,
            '계획공기': activity.duration,
            '사용량': activity.load_size,
            '소요기간(일)': end_offset - start_offset
        })

    result_df = pd.DataFrame(rows)
    result_df.sort_values(by='시작일', inplace=True)

    result_df.to_csv(filepath, index=False, encoding='utf-8-sig')  # 한글 깨짐 방지용
    print(f"CSV file saved in :: {filepath}")