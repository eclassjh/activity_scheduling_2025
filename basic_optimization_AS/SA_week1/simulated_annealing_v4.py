"""
목적함수에도 제약이 반영되어있던 이전 버전 수정
"""

import matplotlib.pyplot as plt
import random
import numpy as np
import pandas as pd

import time

class Activity :
    """작업에 대한 정보 클래스"""
    def __init__(self, duration, earliest_start_date, latest_start_date, predecessors=None):
        # 작업 소요 시간
        self.duration = duration
        # 작업 최초 시작 가능일
        self.earliest_start_date = earliest_start_date
        # 작업 최종 종료 기한
        self.latest_start_date = latest_start_date
        # 작업간 선후행 관계 정보 리스트 (기본값: 빈 리스트)
        self.predecessors = predecessors if predecessors else []

# pandas를 활용하여 csv 파일 불러오기
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
            duration = duration,
            earliest_start_date = earliest,
            latest_start_date = latest,
            # predecessors=preds
        )
        precedence_dict[act_name] = preds
        
    return activity_dict, precedence_dict

def initial_solution(activity_dict, precedence_dict, max_tries=100):
    for _ in range(max_tries):
        x = {}
        for act, a in activity_dict.items():
            latest_start = a.latest_start_date
            x[act] = random.randint(a.earliest_start_date, latest_start)

        if is_valid_solution(x, precedence_dict, activity_dict):
            return x


def generate_new_solution(x, activity_dict, precedence_dict, max_shift=3, max_tries=50, multi_prob=0.3):
    for _ in range(max_tries):
        new_x = x.copy()
        acts = list(x.keys())

        # 복수 작업 이동 확률
        if random.random() < multi_prob:
            # 두 개 작업 선택해 무작위 재배치
            selected = random.sample(acts, 2)
        else:
            # 한 작업만 선택
            selected = [random.choice(acts)]

        for act in selected:
            a = activity_dict[act]
            shift = random.randint(-max_shift, max_shift)
            new_start = new_x[act] + shift

            # 범위 제한
            new_start = max(a.earliest_start_date, new_start)
            new_start = min(a.latest_start_date, new_start)
            new_x[act] = new_start

        if is_valid_solution(new_x, precedence_dict, activity_dict):
            if new_x != x:
                print("[DEBUG] 완전히 새로운 해 생성됨")
            else:
                print("[DEBUG] 유효하지만 기존 해와 동일")
            
            return new_x

    return x

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
    end_times = {
        act: x[act] + activity_dict[act].duration
        for act in x
    }
    max_time = max(end_times.values())

    cumulated_loads_timeline = [0] * (max_time + 1)
    for act in x:
        for t in range(x[act], end_times[act]):
            cumulated_loads_timeline[t] += 1

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
    x = initial_solution(activity_dict, precedence_dict)
    
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