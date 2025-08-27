import pandas as pd
from collections import deque
# import random

class Activity:
    """작업에 대한 정보 클래스"""
    def __init__(self, duration, earliest_start_date, latest_start_date, predecessors=None):
        self.duration = duration
        self.earliest_start_date = earliest_start_date
        self.latest_start_date = latest_start_date
        self.predecessors = predecessors if predecessors else []

# 선행 작업들은 별도로 저장 X
def data_preprocess(filepath):
    df = pd.read_csv(filepath)
    activity_dict = dict()

    for _, row in df.iterrows():
        act_name = row["activity_name"]
        duration = int(row["duration"])
        earliest = int(row["earliest_start_time"])
        latest = int(row["latest_start_time"])

        activity_dict[act_name] = Activity(
            duration = duration,
            earliest_start_date = earliest,
            latest_start_date = latest)
    return activity_dict
        
def _parse_preds(cell):
    """
    선행 작업 파싱 함수(return : list) 
        실행 순서
        - cell 안에 있는 값을 ',' 기준으로 분리하여 얻은 모든 list 항목에 대해 반복
            1. 띄어쓰기 제거
            2. 선행 작업이 있는 경우 parse_out list에 append
                - 숫자만 있는 경우 :  a를 붙여 append
                - a가 있는 경우 : a + 숫자 형태로 append
                - 그 외의 경우 : 일단 append (필요시 디버깅)
    """
    if pd.isna(cell): 
        return []
    
    parse_out = []
    for acts in str(cell).split(','):
        act = acts.strip()
        if not act:
            continue
        if act.isdigit():
            parse_out.append(f"a{int(act)}")
        elif act[0].lower() == 'a' and act[1:].isdigit():
            parse_out.append(f"a{int(act[1:])}")
        else:
            parse_out.append(act)
    
    return parse_out

def build_descendant_graph_from_csv(filepath):
    """
    .csv 파일에서 선후행 작업 관련 graph type의 데이터를 생성하는 함수
        - activities(graph) 정의
        # - act_node(set) 정의
        - succesor(list) 정의
        - in_degree(list) 정의
    """
    df = pd.read_csv(filepath)

    # activities: {작업이름: [선행 작업들 list]} (dtype : dict)
    activities = {}
    for row in df.itertuples(index=False):
        name = str(row.activity_name).strip()
        preds = _parse_preds(getattr(row, "precedence", None)) # getattr():객체의 속성을 문자열로 가져오는 내장함수
        activities[name] = preds

    act_nodes = set(activities.keys())
        # dtype: set ## 순서 없는 자료형, 중복 자동 제거, 빠른 탐색 연산

    # successor, in_degree list 초기화
    successors = {i: [] for i in act_nodes}
    in_deg = {i: 0  for i in act_nodes}
    
    # in_deg 채우기
    for act_name, preds in activities.items():
        for p in dict.fromkeys(preds): # preds의 요소로 만든(중복제거) dict 내 모든 key에 대해 반복
            if p in act_nodes:  # 유효한 선행
                successors[p].append(act_name)
                in_deg[act_name] += 1               
            # else: 모르는 선행

    return successors, in_deg

def extract_priority_list(successors, in_deg):
    """
    Kahn의 위상정렬을 이용해 priority list를 뽑는 함수
    """
    n = len(in_deg)
    order = []

    # 자료형 : Queue
    Q = deque([u for u,d in in_deg.items() if d == 0])
    
    in_deg = in_deg.copy()
    while Q:
        u = Q.popleft()
        order.append(u)
        for v in successors.get(u, []):
            in_deg[v] -= 1
            if in_deg[v] == 0:
                Q.append(v)
    if len(order) != n:
        raise ValueError("Priority list incomplete")
    
    return order

def adjust_lst(activity_dict, order):    
    for i in range(len(order)-2, -1, -1): # (시작, 끝, step)
            u, v = order[i], order[i + 1]
            if activity_dict[u].latest_start_date > activity_dict[v].latest_start_date - activity_dict[u].duration:
                activity_dict[u].latest_start_date = activity_dict[v].latest_start_date - activity_dict[u].duration

    return activity_dict

def main():
    filepath = "C:/Users/eclas/repos/src/activity_scheduling_2025/basic_optimization_AS/Activity_study_data.csv"
    # 선행 제약 고려 순서 배정
    successors, in_deg = build_descendant_graph_from_csv(filepath)
    order = extract_priority_list(successors, in_deg)
    # 배정된 순서에 따른 lst 조정
    activity_dict =data_preprocess(filepath)
    adjust_lst(activity_dict, order)
    
    print("Priority list:", order)
