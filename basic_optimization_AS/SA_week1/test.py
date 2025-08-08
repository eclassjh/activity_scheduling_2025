import dataclasses
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time
from typing import Union, Dict, List

class Activity :
    """작업에 대한 정보 클래스"""
    def __init__(self, duration, earliest_start_date, latest_start_date, predecessors=None):
        self.duration = duration
        self.earliest_start_date = earliest_start_date
        self.latest_start_date = latest_start_date
        self.predecessors = predecessors if predecessors else []

def data_preprocess():
    """csv 파일에서 데이터를 불러와 전처리"""
    try:
        df = pd.read_csv("activity_custom_defined.csv")
    except FileNotFoundError:
        print("Error: 'activity_custom_defined.csv' 파일을 찾을 수 없습니다. 테스트용 더미 데이터를 생성합니다.")
        # 더미 데이터 생성 (테스트용)
        data = {
            'activity_name': ['a1', 'a2', 'a3', 'a4', 'a5', 'a6'],
            'duration': [5, 3, 4, 6, 2, 8],
            'earliest_start_time': [0, 0, 0, 0, 0, 0],
            'latest_start_time': [20, 20, 20, 20, 20, 20],
            'precedence': [np.nan, 'a1', 'a1', 'a2', 'a3', 'a4, a5']
        }
        df = pd.DataFrame(data)

    activity_dict = {}
    precedence_dict = {}

    for _, row in df.iterrows():
        act_name = str(row["activity_name"])
        duration = int(row["duration"])
        earliest = int(row["earliest_start_time"])
        latest = int(row["latest_start_time"])
        precedence_value = str(row["precedence"])
        
        preds = []
        if precedence_value.lower() != "nan":
            preds = [p.strip() for p in precedence_value.split(",")]

        activity_dict[act_name] = Activity(
            duration=duration,
            earliest_start_date=earliest,
            latest_start_date=latest
        )
        precedence_dict[act_name] = preds
        
    return activity_dict, precedence_dict

def find_cycle(activities, precedence_dict):
    """
    선후행 관계에서 순환 고리(cycle)를 찾아 출력합니다.
    """
    path = set()
    visited = set()
    
    adj = {act: [] for act in activities}
    for act, preds in precedence_dict.items():
        for pred in preds:
            if pred in adj:
                adj[pred].append(act)

    def dfs_visit(node):
        visited.add(node)
        path.add(node)
        
        for neighbor in adj.get(node, []):
            if neighbor not in visited:
                if dfs_visit(neighbor):
                    return True
            elif neighbor in path:
                return True
        
        path.remove(node)
        return False

    for activity in activities:
        if activity not in visited:
            if dfs_visit(activity):
                print("\n[순환 감지] 데이터에 순환되는 선후행 관계가 있습니다.")
                print("순환 고리(Cycle)에 포함된 작업:")
                print(" -> ".join(list(path)))
                return True
                
    return False

def topological_sort(activities, precedence_dict):
    """위상 정렬을 통해 선후행 관계를 만족하는 순열을 생성합니다."""
    in_degree = {act: 0 for act in activities}
    adj = {act: [] for act in activities}
    for act, preds in precedence_dict.items():
        for pred in preds:
            if pred in in_degree:
                adj[pred].append(act)
            in_degree[act] += 1
    queue = [act for act in activities if in_degree[act] == 0]
    random.shuffle(queue)
    sorted_list = []
    while queue:
        current = queue.pop(0)
        sorted_list.append(current)
        for neighbor in adj[current]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    if len(sorted_list) != len(activities):
        return []
    return sorted_list

def initial_solution(activity_dict, precedence_dict):
    """
    모든 제약 조건을 만족하는 유효한 초기 해를 확정적으로 생성합니다.
    """
    activities_list = list(activity_dict.keys())
    
    sorted_list = topological_sort(activities_list, precedence_dict)
    if not sorted_list:
        print("Error: 순환 그래프가 감지되어 초기 해를 생성할 수 없습니다. 데이터의 선행 관계를 확인하세요.")
        return None
    
    earliest_start_times = {}
    for act in sorted_list:
        activity = activity_dict[act]
        preds = precedence_dict.get(act, [])
        earliest_by_preds = max(earliest_start_times[p] + activity_dict[p].duration for p in preds) if preds else 0
        earliest_start_times[act] = max(activity.earliest_start_date, earliest_by_preds)
        
    latest_start_times = {}
    for act in reversed(sorted_list):
        activity = activity_dict[act]
        succs = [succ for succ, preds in precedence_dict.items() if act in preds]
        latest_by_succs = min(latest_start_times[s] - activity_dict[act].duration for s in succs) if succs else float('inf')
        latest_start_times[act] = min(activity.latest_start_date, latest_by_succs)
        
    x = {}
    for act in sorted_list:
        lower_bound = earliest_start_times[act]
        upper_bound = latest_start_times[act]
        
        if lower_bound > upper_bound:
            print(f"Error: {act} 작업의 시작 시간 범위가 유효하지 않습니다. [{lower_bound}, {upper_bound}]")
            return None
        
        x[act] = random.randint(lower_bound, upper_bound)
        
    print("[InitialSolution] 유효한 해를 성공적으로 생성했습니다.")
    return x

def generate_new_solution(x, activity_dict, precedence_dict, max_shift=3, max_tries=50, multi_prob=0.3):
    """
    현재 해 x를 기반으로 선후행 조건을 만족하는 새로운 해를 생성합니다.
    """
    for _ in range(max_tries):
        new_x = x.copy()
        acts = list(x.keys())
        
        if random.random() < multi_prob:
            selected = random.sample(acts, min(2, len(acts)))
        else:
            selected = [random.choice(acts)]
            
        for act in selected:
            a = activity_dict[act]
            shift = random.randint(-max_shift, max_shift)
            new_start = new_x[act] + shift
            
            new_start = max(a.earliest_start_date, new_start)
            new_start = min(a.latest_start_date, new_start)
            new_x[act] = new_start
            
        if is_valid_solution(new_x, precedence_dict, activity_dict):
            return new_x
            
    return x

def is_valid_solution(x, precedence_dict, activity_dict):
    """
    주어진 x가 모든 제약을 만족하는지 확인합니다.
    """
    for act, start_time in x.items():
        activity = activity_dict[act]
        if not (activity.earliest_start_date <= start_time <= activity.latest_start_date):
            return False

    for act, start_time in x.items():
        preds = precedence_dict.get(act, [])
        for pred in preds:
            if pred not in x:
                return False
            pred_end_time = x[pred] + activity_dict[pred].duration
            if pred_end_time > start_time:
                return False
    return True

def calculate_energy(x, activity_dict, precedence_dict):
    """
    입력된 해 x에 대해 시간별 누적 부하의 표준편차를 계산합니다.
    """
    end_times = {act: x[act] + activity_dict[act].duration for act in x}
    max_time = max(end_times.values()) if end_times else 0
    cumulated_loads_timeline = [0] * (max_time + 1)
    
    for act in x:
        start_time = x[act]
        end_time = end_times[act]
        for t in range(start_time, end_time):
            if t < len(cumulated_loads_timeline):
                cumulated_loads_timeline[t] += 1
            
    standard_deviation = np.std(cumulated_loads_timeline)
    return standard_deviation

def update_x(x, x_new, E_x, E_x_new, T) :
    """Simulated Annealing의 해 업데이트 로직"""
    if E_x_new < E_x:
        return x_new
    else:
        P = np.exp((E_x - E_x_new) / T)
        if random.random() < P:
            return x_new
        return x

def plot_gantt(best_x, activity_dict):
    """간트 차트를 그립니다."""
    sorted_acts = sorted(best_x.items(), key=lambda item: item[1])
    
    fig, ax = plt.subplots(figsize=(12, 6))
    colors = plt.cm.tab20(np.linspace(0, 1, len(sorted_acts)))
    
    for i, (act, start) in enumerate(sorted_acts):
        duration = activity_dict[act].duration
        ax.barh(y=i, width=duration, left=start, height=0.6, color=colors[i], alpha=0.8)
        ax.text(start + duration / 2, i, f"{act}\n({duration}일)", va='center', ha='center', color='black', fontsize=9)

    ax.set_yticks(range(len(sorted_acts)))
    ax.set_yticklabels([act for act, _ in sorted_acts])
    ax.set_xlabel("시간 (일)")
    ax.set_ylabel("작업")
    ax.set_title("최적 해의 간트 차트")
    plt.tight_layout()
    plt.grid(True, axis='x', linestyle='--', alpha=0.5)
    plt.show()

def run_SA(T, T_min, Niteration):
    """SA 실행 함수"""
    activity_dict, precedence_dict = data_preprocess()
    
    if find_cycle(list(activity_dict.keys()), precedence_dict):
        print("순환 문제를 해결한 후 다시 실행해 주세요.")
        return None, None, None

    x = initial_solution(activity_dict, precedence_dict)
    if not x:
        print("초기 해를 찾을 수 없어 프로그램을 종료합니다.")
        return None, None, None
        
    best_x = x
    best_E = calculate_energy(x, activity_dict, precedence_dict)
    
    iteration = 0
    while iteration < Niteration and T > T_min :
        x_new = generate_new_solution(x, activity_dict, precedence_dict)
        if x_new is None:
            iteration += 1
            continue
        
        E_x = calculate_energy(x, activity_dict, precedence_dict)
        E_x_new = calculate_energy(x_new, activity_dict, precedence_dict)
        
        x = update_x(x, x_new, E_x, E_x_new, T)
        
        if E_x_new < best_E:
            best_E = E_x_new
            best_x = x_new
        
        T *= 0.999
        iteration += 1
        print(f"[Iter {iteration}] Energy(standard deviation) = {E_x:.4f}, T = {T:.4f}")
    
    return best_x, best_E, activity_dict

if __name__ == "__main__":
    try:
        start_time = time.time()
        
        best_x, best_E, activity_dict = run_SA(
            T=1000,
            T_min=0.001,
            Niteration=10000
        )
        
        if best_x:
            elapsed_time = time.time() - start_time
            print("\n--- 결과 ---")
            print("최적 해 (Best Solution):", best_x)
            print(f"최적 Energy (부하 표준편차): {best_E:.4f}")
            print(f"총 소요 시간: {elapsed_time:.2f}초")
            
            plot_gantt(best_x, activity_dict)
            
    except KeyboardInterrupt:
        elapsed = time.time() - start_time
        print(f"\n사용자가 실행을 중단했습니다. 경과 시간: {elapsed:.2f}초")
    except Exception as e:
        print(f"오류가 발생했습니다: {e}")