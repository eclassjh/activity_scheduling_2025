import pandas as pd

# 엑셀(.xlsx) 파일을 CSV(.csv) 파일로 변환하고, 변환된 경로를 반환하는 함수
def convert_xlsx_to_csv(filepath) :
    csv_path = filepath.replace('.xlsx', '.csv')
    df = pd.read_excel(filepath, engine='openpyxl')
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    
    print(f"Converted '{filepath}' to '{csv_path}'")
    return csv_path