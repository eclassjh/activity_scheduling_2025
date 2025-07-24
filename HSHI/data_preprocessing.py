from datetime import timedelta
from dataclasses import dataclass
from convert_xlsx_to_csv import *
import pandas as pd
# import numpy as np


# masking 처리 된 data에 대한 data preprocess 함수
# let -> lst 기반 일정 제약으로 변경되었음
@dataclass
class Activity:
    duration: int
    earliest_start_time: int
    latest_start_time: int
    load_size: float

def data_preprocessing(filepath):
    """
        - earliest_start_time = due_date - duration - pre_buffer
        - latest_start_time = due_date - duration
        - duration = 계획공기
        - 일별 사용량 = ( H01 + H02 ) / duration
    """
    
    # 필요한 컬럼만 불러오기, 타입 명시 :: 데이터 처리 성능 향상
    usecols = ['block_name', 'workload_h1', 'workload_h2', 'due_date', 'duration', 'pre_buffer'] # type: ignore :: pyright 검사 생략
    dtype = { # type: ignore :: pyright 검사 생략
        'block_name' : 'str',
        'due_date': 'int32',    
        'duration': 'int32',
        'pre_buffer' : 'int32',
        'workload_h1': 'float32',
        'workload_h2': 'float32'
    }

    df = pd.read_excel(filepath, usecols=usecols, dtype=dtype, header=0) # type: ignore :: pyright 검사 생략

    # 결측값 처리
    df['due_date'] = df['due_date'].fillna(0)
    df['duration'] = df['duration'].fillna(0)
    df['pre_buffer'] = df['pre_buffer'].fillna(0)
    df['workload_h1'] = df['workload_h1'].fillna(0)
    df['workload_h2'] = df['workload_h2'].fillna(0)

    # 필요한 변수 column 추가
    df['raw_est'] = (df['due_date'] - df['duration'] - df['pre_buffer'])
    df['raw_lst'] = (df['due_date'] - df['duration'])
    
    # 기준일자로부터의 상대 일수(int) 계산
    base_date = df[['raw_est', 'raw_lst']].min().min()
    df['indexed_est'] = (df['raw_est'] - base_date)
    df['indexed_lst'] = (df['raw_lst'] - base_date)

    # 딕셔너리 생성
    activity_dict = {}
    for idx, row in df.iterrows():
        activity_name = str(row['block_name'])
        duration = int(row['duration'])
        earliest = int(row['indexed_est'])
        latest = int(row['indexed_lst'])
        load = float((row['workload_h1'] + row['workload_h2']) / duration) if duration > 0 else 0.0

        activity_dict[activity_name] = Activity(
            duration = duration,
            earliest_start_time = earliest,
            latest_start_time = latest,
            load_size = round(load)
        )

    return activity_dict, base_date