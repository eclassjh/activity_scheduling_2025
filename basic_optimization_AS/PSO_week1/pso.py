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

def pso(activity_dict, fitness_fn, n_particles=30, max_iter=100, w=0.5, c1=1.5, c2=1.5):
    # n_particles 만큼의 particle 생성 (list)
    particles = [Particle(activity_dict) for _ in range(n_particles)]

    # 초기 gbest 설정
    gbest = None
    gbest_value = float('inf')

    for _ in range(max_iter):
        for p in particles:  # 전체 입자에 대해 ; 현재 위치 평가 및 기억 업데이트
            fitness = fitness_fn(p.position, activity_dict)  # 현재 위치의 성능 평가

            # 개인 최고 해(pbest)보다 현재 위치가 더 나으면 갱신
            if fitness < p.pbest_value:
                p.pbest = p.position.copy()
                p.pbest_value = fitness

            # 전체 swarm 최고 해(gbest)보다 현재 위치가 더 나으면 갱신
            if fitness < gbest_value:
                gbest = p.position.copy()
                gbest_value = fitness

        for p in particles:  # 전체 입자에 대해 ;
            for i in range(len(p.position)):  # 각 작업(Activity)에 대해 반복

                # 무작위 계수 r1, r2 생성
                r1 = random.random()  # 개인 경험 계수
                r2 = random.random()  # 사회적 경험 계수

                # 속도 구성 요소
                inertia = w * p.velocity[i]  # 이전 속도 유지 성분 (관성)
                cognitive = c1 * r1 * (p.pbest[i] - p.position[i])  # 개인 최적 방향 성분 ## C1 : p_best 신뢰도 가중치
                social = c2 * r2 * (gbest[i] - p.position[i])  # 전역 최적 방향 성분 ## C2 : g_best 신뢰도 가중치

                # 속도 및 위치 계산
                p.velocity[i] = inertia + cognitive + social
                new_pos = round(p.position[i] + p.velocity[i])

                # 범위 보정
                key = p.activity_keys[i]
                act = activity_dict[key]
                new_pos = max(act.earliest_start, min(new_pos, act.latest_start))

                p.position[i] = new_pos  # 새로운 시작시간으로 반영

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
    activity_dict = data_preprocess("/Users/joohyun/Documents/repos/PSO/Activity_study_data.csv")
    best_position, best_value = pso(activity_dict, calculate_fitness, n_particles=20, max_iter=50)
    print("Best Position:", best_position)
    print("Best Fitness:", best_value)
    
if __name__ == "__main__":
    main()