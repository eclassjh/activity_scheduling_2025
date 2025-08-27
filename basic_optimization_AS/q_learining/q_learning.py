import numpy as np
import time
import random
import math

from priority_algorithm import *

def epsilon_greedy_selection(activity_name, T,Q , eps):
    if not T:  # 복구 로직
        return None
    
    if random.random() < eps:
        return random.choice(T)
    
    # exploit
    best_t, best_q = None, -math.inf
    
    for t in T:
        q = Q.get((activity_name, t), 0.0)
        if q > best_q:
            best_q, best_t = q, t
            
    return best_t

def commit_schedule(a, a_name, t, schedule, resources):
    start = t
    end = start + a.duration

    # 자원 누적 및 과부하 체크
    demand = getattr(a, "demand", 1)
    for tau in range(start, end): # [start, end)
        resources[tau] += demand

    # 기록
    schedule[a_name] = start

    return start, end


def train(activity_dict, order, capacity = 3, E_MAX = 200, eps_start = 0.3, eps_end = 0.05, eps_decay = 0.98):
    Q = {}  # [ (activity_name, t), cumulated_rewards ]
    best_schedule, best_obj = None, float('inf')
    eps = eps_start

    for episode in range(E_MAX):
        # 1) LST 조정
        adjust_lst_by_order(activity_dict, order)

        # 2) 에피소드 초기화
        schedule = {}
        resources = [] # 시간별 사용량 리스트
        # scheduled = set()

        # 3) 작업 배치 루프
        for i, a_name in enumerate(order):
            a = activity_dict[a_name]

            # 유효 시작시각 집합 T 정의
            T = []
            t_min = a.earliest_start_date
            t_max = a.latest_start_date
            for t in range(t_min, t_max+1):
                T.append(t)
            
            # 복구/패널티: 불가능하면 작은 idle 삽입 등(여긴 단순 패널티만 예시)
            if not T:
                r = -100.0
                # Q 업데이트를 하려면 상태키/다음상태키가 필요하지만,
                # 여기선 단순히 패널티만 주고 다음으로 넘어가도 됨 (혹은 idle 삽입 로직 구현)
                # continue 또는 강제로 t = max(ES, pred_end) 배치 후 과부하 허용 패널티 부여 등
                break

            # ε-greedy로 시작시각 t 선택
            t = epsilon_greedy_selection(a_name, T, Q, eps)

            # 스케줄 반영
            commit_schedule(a, t, schedule)
            # scheduled.add(a_name)

            # 보상 계산(peak-load 최소화 예시)
            r = reward_peakload(resources)

            # 다음 상태키: 다음 배치될 activity name(없으면 None)
            if i + 1 < len(order):
                next_a_name = order[i + 1]
                next_T = valid_start_time(activity_dict[next_a_name], schedule, resources, capacity)
                next_key = next_a_name
            else:
                next_T, next_key = [], None

            # Q 업데이트
            q_update(Q, a_name, t, r, next_T, next_key)

        # 한 에피소드의 목적함수 평가(예: peak-load or makespan)
        episode_obj = max(resources) if resources else float('inf')
        if episode_obj < best_obj:
            best_obj, best_schedule = episode_obj, dict(schedule)

        # ε 감소
        eps = max(eps_end, eps * eps_decay)

        # 조기 종료(수렴) 예시
        # if ...: break

    return best_schedule, best_obj, Q

# 선행 작업들에 의해 est도 조절되어야 하는건가? if yes :
def valid_start_time(a, activity_dict, schedule):
    """
    하한 = max(ES_i, max_p (S_p + d_p - d_i)) 
    """
    T =[]
    if getattr(a, "predecessors", None):
        pred_bound = max(
            schedule[p] + activity_dict[p].duration - a.duration
            for p in a.predecessors
        )
    else:
        pred_bound = 0

    t_min = max(a.earliest_start_date, pred_bound)
    t_max = a.latest_start_date

    t_min = max(0, t_min)
    if t_min > t_max:
        return ValueError

    for t in range(t_min, t_max+1):
        T.append(t)
    return t_min, t_max
