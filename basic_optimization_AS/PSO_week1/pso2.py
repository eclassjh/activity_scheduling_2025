from dataclasses import dataclass
import random
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

@dataclass
class Activity:
    duration: int
    earliest_start: int
    latest_start: int
    predecessors: list[str]

class Particle:
    def __init__(self, activity_dict):
        """
        각 particle은 스케줄링 된 액티비티들의 시작 시간을 묶어둔 list
            self.activity_keys : activity 이름
            self.position : 각 particle의 위치 (초기 위치 = initialize_position()으로 지정)
            self.velocity : 각 particle의 속도 (초기속도 : 0.0)
            self.pbest : 현 입자가 경험한 최상의 position
            self.pbest_value : 최상의 position에서의 fitness value
        """
        self.activity_keys = list(activity_dict.keys())
        self.position = self._initialize_position(activity_dict)
        self.velocity = [0.0 for _ in self.activity_keys]
        self.pbest = self.position.copy()
        self.pbest_value = float('inf')
    
    def _initialize_position(self, activity_dict):
        position = []
        for key in self.activity_keys:
            act = activity_dict[key]
            pos = random.randint(act.earliest_start, act.latest_start)
            position.append(pos)
        return position

def pso(activity_dict, fitness_fn, n_particles, max_iter, w=0.5, c1=1.5, c2=1.5):
    """
    PSO 기반 스케줄링 최적화 함수

    Args:
        - activity_dict (dict[str, Activity]): 작업 이름과 Activity 객체를 담은 딕셔너리
        - fitness_fn (Callable): fitness(position, activity_dict, activity_keys)를 입력받아 float을 반환하는 함수
        - n_particles (int, optional): 사용할 particle 수. 기본값 30
        - max_iter (int, optional): 반복 횟수. 기본값 100
        - w (float, optional): 관성 계수
        - c1 (float, optional): 개인 최적 위치에 대한 신뢰도 가중치
        - c2 (float, optional): 전역 최적 위치에 대한 신뢰도 가중치

    Returns:
        - best_position (list[int]): 최적의 시작 시간 리스트
        - best_value (float): 최적의 fitness 값
    """
    # Particle 초기화
    particles = [Particle(activity_dict) for _ in range(n_particles)]
    gbest = None
    gbest_value = float('inf')

    for _ in range(max_iter):
        for p in particles:
            # 1. 속도 및 위치 업데이트
            for i, key in enumerate(p.activity_keys):
                r1 = random.random()
                r2 = random.random()

                inertia = w * p.velocity[i]
                cognitive = c1 * r1 * (p.pbest[i] - p.position[i])
                social = c2 * r2 * ((gbest[i] - p.position[i]) if gbest else 0)

                p.velocity[i] = inertia + cognitive + social
                p.position[i] = round(p.position[i] + p.velocity[i])

                # 시작 시간 범위 보정 
                ## earliest_start ≤ p.position[i] ≤ latest_start 을 만족하도록
                act = activity_dict[key]
                p.position[i] = max(act.earliest_start, min(p.position[i], act.latest_start))

            # 2. 제약 조건 보정 (선후행 등)
            p.position = repair_position(p.position, activity_dict, p.activity_keys)

            # 3. fitness 평가
            fitness = fitness_fn(p.position, activity_dict, p.activity_keys)

            # 4. 개인 최적해 갱신
            if fitness < p.pbest_value:
                p.pbest = p.position.copy()
                p.pbest_value = fitness

            # 5. 전역 최적해 갱신
            if fitness < gbest_value:
                gbest = p.position.copy()
                gbest_value = fitness

    return gbest, gbest_value

def repair_position(position, activity_dict, activity_keys):
    """
    position에서 선후행 제약과 시작 제한을 만족하도록 수정
    """
    pos_dict = dict(zip(activity_keys, position))
    sorted_keys = topological_sort(activity_dict)

    for act_key in sorted_keys:
        act = activity_dict[act_key]
        max_pred_end = 0
        for pred in act.predecessors:
            pred_end = pos_dict[pred] + activity_dict[pred].duration
            max_pred_end = max(max_pred_end, pred_end)

        # 선행종료시간, est, lst 조건을 고려한 시간 보정
        earliest_feasible = max(act.earliest_start, max_pred_end)
        pos_dict[act_key] = max(pos_dict[act_key], earliest_feasible)
        pos_dict[act_key] = min(pos_dict[act_key], act.latest_start)

    return [pos_dict[k] for k in activity_keys]


def topological_sort(activity_dict):
    from collections import defaultdict, deque

    indegree = defaultdict(int)
    graph = defaultdict(list)

    for key, act in activity_dict.items():
        for pred in act.predecessors:
            graph[pred].append(key)
            indegree[key] += 1

    queue = deque([k for k in activity_dict.keys() if indegree[k] == 0])
    result = []

    while queue:
        node = queue.popleft()
        result.append(node)
        for neighbor in graph[node]:
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                queue.append(neighbor)

    return result

def calculate_fitness(position, activity_dict, activity_keys):
    pos_dict = dict(zip(activity_keys, position))
    max_time = 0

    for act_key in activity_dict:
        start = pos_dict[act_key]
        duration = activity_dict[act_key].duration
        end = start + duration
        max_time = max(max_time, end)

    load_per_time = [0] * (max_time + 1)

    for act_key in activity_dict:
        start = pos_dict[act_key]
        duration = activity_dict[act_key].duration
        for t in range(start, start + duration):
            load_per_time[t] += 1

    return np.std(load_per_time)

def fitness_with_penalty(position, activity_dict, activity_keys, penalty_weight=1000):
    fitness = calculate_fitness(position, activity_dict, activity_keys)
    penalty = calculate_penalty(position, activity_dict, activity_keys)
    return fitness + penalty_weight * penalty


def calculate_penalty(position, activity_dict, activity_keys):
    """
    현재 position이 선후행 제약을 몇 개 위반했는지 카운트
    """
    pos_dict = dict(zip(activity_keys, position))
    penalty = 0

    for act_key, act in activity_dict.items():
        for pred in act.predecessors:
            pred_end = pos_dict[pred] + activity_dict[pred].duration
            if pos_dict[act_key] < pred_end:
                penalty += 10000

    return penalty


def data_preprocess(filepath) :
    df = pd.read_csv(filepath)
    activity_dict = {}

    for _, row in df.iterrows():
        name = row['activity_name']
        duration = int(row['duration'])
        earliest = int(row['earliest_start_time'])
        latest = int(row['latest_start_time'])

        raw_preds = str(row['precedence']) if pd.notna(row['precedence']) else ''
        predecessors = [f"a{int(p.strip())}" for p in raw_preds.split(',') if p.strip().isdigit()]

        activity_dict[name] = Activity(
            duration=duration,
            earliest_start=earliest,
            latest_start=latest,
            predecessors=predecessors
        )

    return activity_dict

def plot_gantt(best_position, activity_dict, activity_keys):
    """
    PSO 최적화 결과를 Gantt 차트 형식으로 시각화

    Args:
        - best_position (list[int]): 각 작업의 시작 시간 리스트
        - activity_dict (dict[str, Activity]): 작업 이름과 정보가 담긴 딕셔너리
        - activity_keys (list[str]): 작업 순서를 정의하는 키 리스트 (position과 매핑)
    """
    fig, ax = plt.subplots(figsize=(10, len(activity_keys) * 0.5 + 2))

    yticks = []
    ylabels = []

    for i, key in enumerate(activity_keys):
        act = activity_dict[key]
        start = best_position[i]
        duration = act.duration

        ax.broken_barh([(start, duration)], (i - 0.4, 0.8), facecolors='tab:blue')
        ax.text(start + duration / 2, i, key, va='center', ha='center', color='white', fontsize=9)

        yticks.append(i)
        ylabels.append(key)

    ax.set_yticks(yticks)
    ax.set_yticklabels(ylabels)
    ax.set_xlabel("Time")
    ax.set_title("Gantt Chart of Activity Schedule")
    ax.grid(True)
    plt.tight_layout()
    plt.show()



def main():
    # 1. 데이터 전처리
    activity_dict = data_preprocess("C:/Users/eclas/source/repos/constraint_programming/basic_optimization_AS/Activity_study_data.csv")

    # 2. PSO 실행
    best_position, best_value = pso(activity_dict, fitness_with_penalty, n_particles=500, max_iter=10000)

    # 3. 결과 평가용 activity 순서 (position과 매칭되는 정확한 순서)
    activity_keys = Particle(activity_dict).activity_keys

    # 4. 부하 기준 fitness와 penalty 분리 계산
    fitness = calculate_fitness(best_position, activity_dict, activity_keys)
    penalty = calculate_penalty(best_position, activity_dict, activity_keys)

    # 5. 결과 출력
    print("Best Position:", best_position)
    print(f"Fitness (std of load): {fitness:.4f}")
    print(f"Constraint Violations (penalty count): {penalty}")
    print(f"Total Fitness (with penalty): {fitness + 1000 * penalty:.4f}")

    # 6. Gantt 차트 시각화
    plot_gantt(best_position, activity_dict, activity_keys)

if __name__ == "__main__":
    main()
