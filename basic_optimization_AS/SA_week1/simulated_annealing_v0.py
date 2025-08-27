import matplotlib.pyplot as plt
import random
import numpy as np
import pandas as pd

class Activity :
    """작업에 대한 정보 클래스"""
    def __init__(self, duration, earliest_start_date, latest_end_date, predecessors=None):
        # 작업 소요 시간
        self.duration = duration
        # 작업 최초 시작 가능일
        self.earliest_start_date = earliest_start_date
        # 작업 최종 종료 기한
        self.latest_end_date = latest_end_date
        # 작업간 선후행 관계 정보 리스트 (기본값: 빈 리스트)
        self.predecessors = predecessors if predecessors else []

# pandas를 활용하여 csv 파일 불러오기 # 추후 수정요망
def data_preprocess():
    df = pd.read_csv("activity_custom_defined.csv")

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
            duration=duration,
            earliest_start_date=earliest,
            latest_end_date=latest,
            # predecessors=preds
        )
        precedence_dict[act_name] = preds
        
    return activity_dict, precedence_dict

def generate_new_solution(x, precedence_dict, max_tries=50) :
    n = len(x)
    for _ in range(max_tries):
        i, j = sorted(random.sample(range(n), 2))
        new_x = x[:]
        new_x[i], new_x[j] = new_x[j], new_x[i]

        if is_valid_solution(new_x, precedence_dict):
            return new_x
    return x

# solution이 선후행 제약을 만족하는지 확인하는 함수
def is_valid_solution(x, precedence_dict):
    pos = {action: i for i, action in enumerate(x)}
    for action, preds in precedence_dict.items():
        for pred in preds:
            if pos[pred] > pos[action]:
                return False
    return True

# 입력된 순열의 load size에 대한 표준편차 게산 ## earliest start date, lateset start date 제약 고려
def calculate_energy(x, activity_dict):
    """
    1. start_times (dict) 정의 (action, start_time); 현재 시간과 earliest start date중 더 큰 값으로 지정 (earliest_start_date 제약 고려)
    2. end_time (float) 정의; 해당 시나리오에서 제일 마지막 activity가 끝나는 시간 계산 (각 시간별 load계산을 위함)
    3. cumulated_loads_timeline (list) 정의; 모든 activity가 끝나는 마지막 timeline까지의 누적 load값을 저장하는 list
    4. penalty 정의; 작업이 latest time을 초과한 경우 부여하는 penalty (latest_start_date 제약 고려)
    5. standard_deviation 정의; cumulated_loads_timeline의 표준편차 계산
    """
    
    start_times = dict()
    current_time = 0
    
    for action in x:
        duration = activity_dict[action].duration
        earliest_start_date = activity_dict[action].earliest_start_date

        # 시작시간 결정
        start_time = max(current_time, earliest_start_date)
        start_times[action] = start_time
        current_time = start_time + duration

    end_time = max(start_times[action] + activity_dict[action].duration for action in x)
    cumulated_loads_timeline = [0] * (end_time + 1)

    # timeline.에 대한 load size 계산
    for action in x:
        start = start_times[action]
        end = start + activity_dict[action].duration
        for t in range(start, end):
            cumulated_loads_timeline[t] += 1

    penalty = 0
    for action in x:
        end_time = start_times[action] + activity_dict[action].duration
        latest = activity_dict[action].latest_end_date
        if end_time > latest:
            penalty += 1000000 * (end_time - latest)

    # timeline별 load(cumulated_loads_timeline)의 표준편차 계산
    standard_deviation = np.std(cumulated_loads_timeline)
    
    return standard_deviation + penalty

def update_x(x, x_new, E_x, E_x_new, T) :  
    if E_x_new < E_x :
        return x_new
    else :
        P = np.exp((E_x - E_x_new) / T)
        if random.random() < P :
            x = x_new   
    return x

def initial_solution(precedence_dict):
    activities = list(precedence_dict.keys())
    while True :
        x = random.sample(activities, len(activities))
        if is_valid_solution(x, precedence_dict) :
            return x

# Gantt Chart plotting 함수
def plot_gantt(best_x, activity_dict):
    start_times = {}
    current_time = 0
    for action in best_x:
        start_time = max(current_time, activity_dict[action].earliest_start_date)
        start_times[action] = start_time
        current_time = start_time + activity_dict[action].duration

    fig, ax = plt.subplots(figsize=(10, 5))
    for i, act in enumerate(best_x):
        start = start_times[act]
        duration = activity_dict[act].duration
        ax.barh(y=i, width=duration, left=start, height=0.5, label=act)
        ax.text(start + duration/2, i, act, va='center', ha='center', color='white')

    ax.set_yticks(range(len(best_x)))
    ax.set_yticklabels(best_x)
    ax.set_xlabel("Time")
    ax.set_title("Gantt Chart of Best Solution")
    plt.tight_layout()
    plt.show()

# SA 실행함수
def run_SA(T, T_min, Niteration) : #T=10, T_min=1e-3, Niteration=1000
    activity_dict, precedence_dict = data_preprocess() # data 받아오기
    x = initial_solution(precedence_dict)
    
    best_x = x
    best_E = calculate_energy(x, activity_dict)
    
    iteration = 1
    while iteration < Niteration and T > T_min : # 반복해 조건 정의
        x_new = generate_new_solution(x, precedence_dict) # x_new 정의
        
        E_x = calculate_energy(x, activity_dict)
        E_x_new = calculate_energy(x_new, activity_dict)
        
        x = update_x(x, x_new, E_x, E_x_new, T) # 최적해 x update, T 초기해 = 10
        
        if E_x < best_E:
            best_E = E_x
            best_x = x

        print(f"[Iter {iteration + 1}] Energy = {E_x:.2f}, T = {T:.4f}")
        
        T0 = 10**(-5/(iteration))
        T *= T0
        iteration += 1
    
    return best_x, best_E, activity_dict


if __name__ == "__main__":
    best_x, best_E, activity_dict = run_SA(
        T=10,
        T_min=1e-10000,
        Niteration=1000000000,
    )

    print("최적 해 (Best Solution):", best_x)
    print(f"최적 Energy: {best_E:.4f}")

    plot_gantt(best_x, activity_dict)


## 선후행 조건을 만족하는 x_new 정의하는 함수 :: 탐색 범위 자체가 좁아져서 더 복잡한 제약이 있는 경우에 효율적임
# def generate_smart_neighbor(x, precedence_dict, max_tries=50):
#     import random

#     n = len(x)
#     pos = {act: i for i, act in enumerate(x)}  # 위치 맵

#     for _ in range(max_tries):
#         i, j = sorted(random.sample(range(n), 2))
#         a, b = x[i], x[j]

#         # 조건 1: a는 b의 후행작업이 아니어야 함 (즉, b가 a의 선행자가 아님)
#         if a in precedence_dict[b]:
#             continue

#         # 조건 2: b는 a의 후행작업이 아니어야 함
#         if b in precedence_dict[a]:
#             continue

#         # 조건 만족 시 swap
#         new_x = x[:]
#         new_x[i], new_x[j] = new_x[j], new_x[i]
#         return new_x

#     # 실패 시 원래 해 반환
#     return x