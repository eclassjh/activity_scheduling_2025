from dataclasses import dataclass
import random
import pandas as pd
import numpy as np

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

def pso(activity_dict, fitness_fn, n_particles=30, max_iter=10000,
        w=0.5, c1=1.5, c2=1.5, max_valid_attempts=10000):
    """
    PSO 기반 스케줄링 최적화 함수 (선후행 제약 포함)

    Args:
        activity_dict: 작업 이름과 Activity 객체 딕셔너리
        fitness_fn: position, activity_dict -> float 반환하는 함수
        n_particles: 입자 개수
        max_iter: 반복 횟수
        w, c1, c2: PSO 파라미터
        max_valid_attempts: 제약 만족 위해 반복 이동 시도 최대 횟수
    """

    particles = [Particle(activity_dict) for _ in range(n_particles)]
    gbest = None
    gbest_value = float('inf')

    # 초기 유효한 particle로 gbest 강제 초기화
    for p in particles:
        if is_valid_solution(p.position, activity_dict):
            fitness = fitness_fn(p.position, activity_dict)
            gbest = p.position.copy()
            gbest_value = fitness
            break

    for _ in range(max_iter):
        for p in particles:
            # 유효하지 않으면 PSO update를 최대 N회 반복 시도
            attempt = 0
            while not is_valid_solution(p.position, activity_dict) and attempt < max_valid_attempts:
                for i in range(len(p.position)):
                    r1 = random.random()
                    r2 = random.random()
                    inertia = w * p.velocity[i]
                    cognitive = c1 * r1 * (p.pbest[i] - p.position[i])
                    social = 0
                    if gbest is not None:
                        social = c2 * r2 * (gbest[i] - p.position[i])

                    p.velocity[i] = inertia + cognitive + social
                    new_pos = round(p.position[i] + p.velocity[i])

                    key = p.activity_keys[i]
                    act = activity_dict[key]
                    new_pos = max(act.earliest_start, min(new_pos, act.latest_start))
                    p.position[i] = new_pos
                attempt += 1

            # 유효한 해가 되었을 때만 fitness 평가
            if is_valid_solution(p.position, activity_dict):
                fitness = fitness_fn(p.position, activity_dict)

                if fitness < p.pbest_value:
                    p.pbest = p.position.copy()
                    p.pbest_value = fitness

                if fitness < gbest_value:
                    gbest = p.position.copy()
                    gbest_value = fitness

    return gbest, gbest_value

def calculate_fitness(position, activity_dict):
    max_time = 0
    
    for idx, key in enumerate(activity_dict.keys()):
        start = position[idx]
        duration = activity_dict[key].duration
        end = start + duration
        max_time = max(max_time, end)

    # 각 시간별 부하 저장 리스트
    load_per_time = [0] * (max_time + 1)

    # 각 activity의 실행 구간에 부하 누적
    for idx, key in enumerate(activity_dict.keys()):
        start = position[idx]
        duration = activity_dict[key].duration

        for t in range(start, start + duration):
            load_per_time[t] += 1

    # 부하의 표준편차를 계산
    std_dev = np.std(load_per_time)

    return std_dev

def is_valid_solution(position, activity_dict):
    """
    주어진 position이 Start-to-Start 선후행 제약을 만족하는지 검사하는 함수
    Args:
        position (list[int]): 각 activity의 시작시간 리스트
        activity_dict (dict[str, Activity]): 각 activity 정보

    Returns:
        bool: 제약을 모두 만족하면 True, 위반하면 False
    """
    start_times = {key: position[idx] for idx, key in enumerate(activity_dict.keys())}
    
    for key, activity in activity_dict.items():
        act_start = start_times[key]
        for pred in activity.predecessors:
            pred_start = start_times[pred]
            if act_start < pred_start:  # Start-to-Start 제약
                return False
    return True

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

def main() : 
    activity_dict = data_preprocess("C:/Users/eclas/source/repos/constraint_programming/basic_optimization_AS/Activity_study_data.csv")
    best_position, best_value = pso(activity_dict, calculate_fitness, n_particles=20, max_iter=50)
    print("Best Position:", best_position)
    print("Best Fitness:", best_value)
    
if __name__ == "__main__":
    main()