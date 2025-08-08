import matplotlib.pyplot as plt
import random
import numpy as np
import pandas as pd

import time

# SA는 우선해 선택 관련 !
class Activity:
    """작업에 대한 정보 클래스"""
    def __init__(self, duration, earliest_start_date, latest_start_date, predecessors=None):
        self.duration = duration
        self.earliest_start_date = earliest_start_date
        self.latest_start_date = latest_start_date
        self.predecessors = predecessors if predecessors else []

# pandas를 활용하여 csv 파일 불러오기
def data_preprocess():
    df = pd.read_csv("Activity_study_data.csv")

    activity_dict = dict()
    precedence_dict = dict()

    for _, row in df.iterrows():
        act_name = row["activity_name"]
        duration = int(row["duration"])
        earliest = int(row["earliest_start_time"])
        latest = int(row["latest_start_time"])

        precedence_value = str(row["precedence"])
        if precedence_value.lower() != "nan":
            preds = ["a" + p.strip() for p in precedence_value.split(",")]
        else:
            preds = []

        activity_dict[act_name] = Activity(
            duration = duration,
            earliest_start_date = earliest,
            latest_start_date = latest,
            # predecessors=preds
        )
        precedence_dict[act_name] = preds
        
    return activity_dict, precedence_dict

def encode_precedence_constraints(activity_dict, precedence_dict):
    """
        선행 activity에 대하여 후행 activity의 범위를 조정하는 data encoding 함수
        : 선후행 제약(Finish to Start)을 고려하여 각 후행 작업의 earliest_start_time을 조정
        - 선행 latest_start_time + duration 중 최대값을 반영하여 activity의 earliest_start_date를 update
    """
    for act, preds in precedence_dict.items():
        if preds:
            latest_finish_times = [
                activity_dict[p].latest_start_date + activity_dict[p].duration
                for p in preds
            ]
            required_earliest = max(latest_finish_times)
            activity_dict[act].earliest_start_date = max(
                activity_dict[act].earliest_start_date, required_earliest
            )

def initial_solution(activity_dict):
    x = {}
    for act, a in activity_dict.items():
        if a.earliest_start_date > a.latest_start_date:
            raise ValueError(
                f"[ERROR] '{act}' has invalid range: earliest({a.earliest_start_date}) > latest({a.latest_start_date})"
            )
        elif a.earliest_start_date == a.latest_start_date:
            x[act] = a.earliest_start_date
        else:
            x[act] = random.randint(a.earliest_start_date, a.latest_start_date)
    return x

def generate_new_solution(x, activity_dict, precedence_dict, max_shift=3, max_tries=50, prob=0.3):
    """
        새로운 이웃해를 생성하는 함수
        - prob의 확률로 부하 평준화 시도
        - 나머지는 일반 랜덤 이동
    """
    for _ in range(max_tries):
        new_x = x.copy()
        acts = list(x.keys())

        # 특정확률에 따라 ..
        if random.random() < prob:
            # 최대 부하 시간대에서 부하를 줄이는 방향으로 activity 이동
            new_x = smart_shift_by_load(x, activity_dict, precedence_dict, max_shift)
        else:
            # 일반적인 랜덤 이동
            selected = random.choice(acts)
            act = activity_dict[selected]
            shift = random.randint(-max_shift, max_shift)
            new_start = new_x[selected] + shift

            # 범위 제한
            new_start = max(act.earliest_start_date, new_start)
            new_start = min(act.latest_start_date, new_start)
            new_x[selected] = new_start

        # 간접적인 선후행관계 만족 확인을 위한 함수
        if is_valid_solution(new_x, precedence_dict, activity_dict) and new_x != x:
            return new_x

    return x  # 변경 불가능 시 기존 해 반환

def load_timeline(x, activity_dict) :
    """ 타임라인에 따른 부하 계산 함수"""
    end_times = {act: x[act] + activity_dict[act].duration for act in x}
    max_time = max(end_times.values())
    timeline = [0] * (max_time + 1)
    
    for act in x:
        for t in range(x[act], end_times[act]):
            timeline[t] += 1
    
    return timeline


def smart_shift_by_load(x, activity_dict, precedence_dict, max_shift=3):
    """
        최대 부하 시간대에 속한 작업 중 하나를 골라서 
        에너지가 가장 낮은 위치를 찾아 이동시킴
    """
    timeline=load_timeline(x, activity_dict)
    # 최대 부하 시간대 찾기
    max_load_time = np.argmax(timeline)

    # 해당 시간대에 실행 중인 작업 후보
    candidates = [
        act for act in x
        if x[act] <= max_load_time < x[act] + activity_dict[act].duration
    ]
    if not candidates:
        return x  # 이동할 작업이 없는 경우 원래 해 return

    # 가능한 후보 중 random activity를 선택하여 shift
    selected = random.choice(candidates)
    act_info = activity_dict[selected]
    best_energy = float('inf')
    best_x = x.copy()

    for shift in range(-max_shift, max_shift + 1):
        new_start = x[selected] + shift
        new_start = max(act_info.earliest_start_date, new_start)
        new_start = min(act_info.latest_start_date, new_start)

        candidate_x = x.copy()
        candidate_x[selected] = new_start

        if is_valid_solution(candidate_x, precedence_dict, activity_dict):
            energy = calculate_energy(candidate_x, activity_dict)
            if energy < best_energy:
                best_energy = energy
                best_x = candidate_x
        else :
            return # error code
    return best_x


def is_valid_solution(x, precedence_dict, activity_dict):
    start_times = dict()

    for i, act in enumerate(x):
        activity = activity_dict[act]
        preds = precedence_dict.get(act, [])

        # 선행 작업이 아직 정의되지 않은 경우 → 순서가 잘못된 것
        for pred in preds:
            if pred not in start_times:
                return False

        # 선행작업들의 시작시간
        preds_start = [start_times[p] for p in preds] if preds else [0]

        # 시작시간 계산
        start_time = max(max(preds_start), activity.earliest_start_date)
        start_times[act] = start_time

        # latest_start_date 제약 위반 시 False
        if start_time > activity.latest_start_date:
            return False

        # 선행작업이 후행작업보다 늦게 시작하면 False
        for pred in preds:
            if start_times[pred] > start_time:
                return False
    return True

def calculate_energy(x , activity_dict): # x는 각 activity의 start_time이 정의되어 있는 list
    """
    주어진 start_times(x)와 activity_dict를 기반으로 시간대별 누적 부하의 표준편차 계산

    """
    cumulated_loads_timeline = load_timeline(x, activity_dict)
    return np.std(cumulated_loads_timeline)

def update_x(x, x_new, E_x, E_x_new, T) :  
    if E_x_new < E_x :
        return x_new
    else :
        P = np.exp((E_x - E_x_new) / T)
        if random.random() < P :
            x = x_new   
    return x

# Gantt Chart plotting 함수
def plot_gantt(best_x, activity_dict):
    # 시작시간 기준으로 정렬
    sorted_acts = sorted(best_x.items(), key=lambda x: x[1])

    fig, ax = plt.subplots(figsize=(10, 5))
    
    for i, (act, start) in enumerate(sorted_acts):
        duration = activity_dict[act].duration
        ax.barh(y=i, width=duration, left=start, height=0.5, color='skyblue')
        ax.text(start + duration / 2, i, act, va='center', ha='center', color='black')

    ax.set_yticks(range(len(sorted_acts)))
    ax.set_yticklabels([act for act, _ in sorted_acts])
    ax.set_xlabel("Time")
    ax.set_title("Gantt Chart of Best Solution")
    plt.tight_layout()
    plt.grid(True, axis='x', linestyle='--', alpha=0.5)
    plt.show()

# SA 실행함수
def run_SA(T, T_min, Niteration, log_interval=100) : # T=10, T_min=1e-3, Niteration=1000
    activity_dict, precedence_dict = data_preprocess() # data 받아오기
    encode_precedence_constraints(activity_dict, precedence_dict) # 선후행 제약을 만족하도록 data encoding
    x = initial_solution(activity_dict)
    
    best_x = x
    best_E = calculate_energy(x, activity_dict)   
    
    iteration = 1
    while iteration < Niteration or T > T_min : # 반복해 조건 정의
        x_new = generate_new_solution(x, activity_dict, precedence_dict) # x_new 정의
                
        E_x = calculate_energy(x, activity_dict)
        E_x_new = calculate_energy(x_new, activity_dict)
        
        x = update_x(x, x_new, E_x, E_x_new, T) # 최적해 x update, T 초기해 = 10
        
        if E_x < best_E:
            best_E = E_x
            best_x = x

        print(f"[Iter {iteration + 1}] Energy(standard deviation) = {E_x:.10f}, T = {T:.10f}")
        
        T0 = 10**(-5/(iteration))
        T *= T0
        iteration += 1
    return best_x, best_E, activity_dict

if __name__ == "__main__":

    try:
        start_time = time.time()  # 시작 시간 기록

        best_x, best_E, activity_dict = run_SA(
            T=10,
            T_min=1e-50,
            Niteration=10000,
            log_interval=100  # 매 100회마다 상태 출력
        )

        print("\n최적 해 (Best Solution):", best_x)
        print(f"최적 Energy: {best_E:.4f}")

        plot_gantt(best_x, activity_dict)
    
    # terminal에서 Ctrl+c 눌러서 임의로 실행을 종료했을 경우
    except KeyboardInterrupt:
        elapsed = time.time() - start_time
        print(f"\n사용자가 실행을 중단했습니다. 경과 시간: {elapsed:.2f}초")