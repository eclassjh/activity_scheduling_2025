import pandas as pd

def save_to_xlsx(result_dict, activity_dict, base_date, filepath='schedule_result.xlsx'):
    rows = []

    # 가장 이른 작업 시작시간을 기준으로 offset 보정
    min_offset = min(result['start'] for result in result_dict.values())
    print(f"[DEBUG] 최소 시작 offset: {min_offset}")
    
    for task_name, result in result_dict.items():
        activity = activity_dict[task_name]

        start_date = result['start'] - min_offset
        end_date = result['end'] - min_offset
        
        ## 기존에 넘어온 base_date 기준으로 보정된 날짜 출력하고 싶을 때
        # start_offset = result['start']
        # end_offset = result['end']
        # start_date = base_date + start_offset
        # end_date = base_date + end_offset

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

    print(f"출력 결과 보정 기준(min start offset): {min_offset}, base_date: {base_date}")
