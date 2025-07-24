from datetime import timedelta
from dataclasses import dataclass
from convert_xlsx_to_csv import *
import pandas as pd
# import numpy as np

@dataclass
class Activity:
    duration: int
    earliest_start_date: int
    latest_end_date: int
    load_size: float

def data_preprocessing(filepath):
    """
        - earliest_start_time = 착수계획 - 2일
        - latest_end_time = 완료계획 + 후버퍼_보정
        - duration = 계획공기
        - 일별 사용량 = ( H01 + H02 ) / duration
    """
    
    # xlsx 파일일 경우 csv파일로로 변환
    if filepath.endswith('.xlsx'):
        filepath = convert_xlsx_to_csv(filepath)
    
    # 필요한 컬럼만 불러오기, 타입 명시 :: 데이터 처리 성능 향상
    usecols = ['착수계획', '완료계획', '계획공기', '후버퍼_보정', 'H01', 'H02'] # type: ignore :: pyright 검사 생략
    dtype = { # type: ignore :: pyright 검사 생략
        '계획공기': 'int32',    
        '후버퍼_보정': 'int32',
        'H01': 'float32',
        'H02': 'float32'
    }

    df = pd.read_csv(filepath, usecols=usecols, dtype=dtype, parse_dates=['착수계획', '완료계획']) # type: ignore :: pyright 검사 생략
    # df = pd.read_excel(filepath, header=0)

    # 결측값 처리
    df['후버퍼_보정'] = df['후버퍼_보정'].fillna(0)
    df['계획공기'] = df['계획공기'].fillna(0)
    df['H01'] = df['H01'].fillna(0)
    df['H02'] = df['H02'].fillna(0)

    # 필요한 변수 column 추가
    df['raw_est'] = (df['착수계획'] - timedelta(days=2))
    df['raw_let'] = (df['완료계획'] + df['후버퍼_보정'].apply(lambda x: pd.Timedelta(days=x)))
    
    # date type -> int indexing
    # 기준일자로부터의 상대 일수(int) 계산
    base_date = pd.to_datetime(df[['raw_est', 'raw_let']].min().min())
    df['indexed_est'] = (df['raw_est'] - base_date).dt.days
    df['indexed_let'] = (df['raw_let'] - base_date).dt.days

    # 딕셔너리 생성
    activity_dict = {}
    for idx, row in df.iterrows():
        activity_name = f'ACT{idx:03d}'
        duration = int(row['계획공기'])
        earliest = int(row['indexed_est'])
        latest = int(row['indexed_let'])
        load = float((row['H01'] + row['H02']) / duration) if duration > 0 else 0.0

        activity_dict[activity_name] = Activity(
            duration = duration,
            earliest_start_date = earliest,
            latest_end_date = latest,
            load_size = round(load)
        )

    return activity_dict, base_date