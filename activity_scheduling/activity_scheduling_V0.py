from ortools.sat.python import cp_model
import matplotlib.pyplot as plt
# import random
# import math
# import copy
import numpy as np

class Activity:
    def __init__(self, duration, earliest_start_date, latest_end_date, load_size, predecessors = None):
        self.duration = duration
        self.earliest_start_date = earliest_start_date
        self.latest_end_date = latest_end_date
        self.load_size = load_size
        self.predecessors = predecessors
    
# data loading 함수
def data_information():
    activity_dict = dict()

    activity_dict['A'] = Activity(duration=1, earliest_start_date=1, latest_end_date=9, load_size=1, predecessors=None)
    activity_dict['B'] = Activity(duration=2, earliest_start_date=8, latest_end_date=19, load_size=1, predecessors=None)
    activity_dict['C'] = Activity(duration=3, earliest_start_date=6, latest_end_date=16, load_size=3, predecessors=None)
    activity_dict['D'] = Activity(duration=2, earliest_start_date=8, latest_end_date=17, load_size=3, predecessors=None)
    activity_dict['E'] = Activity(duration=1, earliest_start_date=0, latest_end_date=8, load_size=1, predecessors=None)
    activity_dict['F'] = Activity(duration=2, earliest_start_date=7, latest_end_date=15, load_size=2, predecessors=None)
    activity_dict['G'] = Activity(duration=3, earliest_start_date=2, latest_end_date=14, load_size=1, predecessors=None)
    activity_dict['H'] = Activity(duration=2, earliest_start_date=4, latest_end_date=16, load_size=1, predecessors=None)
    activity_dict['I'] = Activity(duration=1, earliest_start_date=10, latest_end_date=19, load_size=2, predecessors=None)
    activity_dict['J'] = Activity(duration=2, earliest_start_date=9, latest_end_date=19, load_size=3, predecessors=None)
    activity_dict['K'] = Activity(duration=3, earliest_start_date=2, latest_end_date=15, load_size=2, predecessors=None)
    activity_dict['L'] = Activity(duration=2, earliest_start_date=1, latest_end_date=12, load_size=3, predecessors=None)
    activity_dict['M'] = Activity(duration=1, earliest_start_date=3, latest_end_date=14, load_size=2, predecessors=None)
    activity_dict['N'] = Activity(duration=2, earliest_start_date=6, latest_end_date=17, load_size=2, predecessors=None)
    activity_dict['O'] = Activity(duration=3, earliest_start_date=0, latest_end_date=14, load_size=2, predecessors=None)
    activity_dict['P'] = Activity(duration=4, earliest_start_date=0, latest_end_date=14, load_size=1, predecessors=None)
    activity_dict['Q'] = Activity(duration=1, earliest_start_date=1, latest_end_date=8, load_size=1, predecessors=None)
    activity_dict['R'] = Activity(duration=3, earliest_start_date=5, latest_end_date=16, load_size=2, predecessors=None)
    activity_dict['S'] = Activity(duration=4, earliest_start_date=3, latest_end_date=18, load_size=3, predecessors=None)
    activity_dict['T'] = Activity(duration=1, earliest_start_date=0, latest_end_date=7, load_size=1, predecessors=None)

    return activity_dict

# a = activity_dict['A']
# print(a.duration) ## 1

# 간트차트 생성 함수
def plot_schedule(results_dict):
    # 기본 설정
    fig, ax = plt.subplots(figsize=(15, 6))
    colors = ['skyblue', 'lightgreen', 'lightcoral']

    # 각 활동별 막대 차트 생성
    for i, (key, data) in enumerate(results_dict.items()):
        start, end = data['start'], data['end']
        duration = end - start
        ax.barh(i, duration, left=start, color=colors[i % len(colors)],
                alpha=0.8, label=key)
        ax.text(start + duration / 2, i, f'{key}\n({start}-{end})',
                ha='center', va='center')

    # 차트 커스터마이징
    ax.set_title('Schedule Gantt Chart')
    ax.set_xlabel('Time')
    ax.grid(True, axis='x', linestyle='--', alpha=0.7)

    # x축 범위 1-5로 고정, y축 눈금 제거
    ax.set_xlim(1, 5)
    ax.set_xticks([1, 2, 3, 4, 5])
    ax.set_yticks([])

    # 범례 설정
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=5)

    # 저장 및 표시
    plt.savefig('gantt_chart.png', bbox_inches='tight', dpi=300)
    plt.show()


# CP모델 관련 함수
## A. 모델 실행 함수 정의
def solve_model(model, solver, activity_var_dict, objective_var) :
    
    result_dict = {}
    status = solver.Solve(model)
    
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print(f"Solution found: {solver.Value(objective_var)}")
        for key in activity_var_dict.keys():
            start = solver.Value(activity_var_dict[key].StartExpr())
            end = solver.Value(activity_var_dict[key].EndExpr())
            
            result_dict[key] = { 'start': start, 'end': end, 'duration': end - start }
    else :
        print("Cannot find a feasible solution")
    
    return result_dict, status

## B. 변수 정의
def model_variables(model, activity_dict): # 활동별 변수 선언 함수
    # 기존 데이터셋 (activity_dict)에서 활동별 변수를 추출하여 모델에 적용 가능한 변수로 정리
    # 기존 데이터셋에서 '데이터' 와 '변수'를 분리하여, 변수로 사용되는 데이터(추후 모델이 정해주는 값)만 모델변수로 정의
    # 모델 변수를 묶어서 다시 activity_var_dict에 저장
    activity_var_dict = dict()
    
    for key, value in activity_dict.items():
        start_var = model.NewIntVar(value.earliest_start_date, value.latest_end_date - value.duration, f'{key}_start')
        duration = value.duration
        end_var = model.NewIntVar(value.earliest_start_date + value.duration, value.latest_end_date, f'{key}_end')

        interval_var = model.NewIntervalVar(start_var, duration, end_var, f'{key}_interval')
        
        activity_var_dict[key] = interval_var
        
    return activity_var_dict

## C. 선후행 제약조건 정의
def add_precedence_constraints(model, activity_dict, activity_var_dict): 
    # precedence 정보는 activity_dict에만 있음 -> 데이터와 변수를 확실히 분리해서 정리하고 있는 중중
    for key, value in activity_dict.items():
        for predecessor in value.predecessors:
            model.Add(activity_var_dict[key].StartExpr() >= activity_var_dict[predecessor].EndExpr())
            
    return activity_var_dict

## D. 목적함수 정의
### 1. 작업부하 최소화
def workload_objective(model, activity_dict, activity_var_dict):
    interval_vars = []
    cumulative_workload = []
    total_load = sum(activity.load_size for activity in activity_dict.values())
    
    max_workload = model.NewIntVar(0, total_load, 'max_workload')
    
    for key, interval_var in activity_var_dict.items():
        # activity_info = activity_dict[key]
        load_size = activity_dict[key].load_size
        cumulative_workload.append(load_size)
        interval_vars.append(interval_var)
                
    model.AddCumulative(interval_vars, cumulative_workload, max_workload)
    model.Minimize(max_workload)
    
    return max_workload

###  2. makespan 최소화
def makespan_objective(model, activity_dict, activity_var_dict):
    latest_end_date_horizon = 0
    for id, activity in activity_dict.items():
        if activity.latest_end_date > latest_end_date_horizon:
            latest_end_date_horizon = activity.latest_end_date
    
    makespan = model.NewIntVar(0, latest_end_date_horizon, 'makespan')
    
    for key, interval_var in activity_dict.items():
        model.Add(makespan >= interval_var.EndExpr())
    
    model.Minimize(makespan)
    return makespan

# main 함수
## 1. worload 최소화
def main_workload() :
    activity_dict = data_information()
    model = cp_model.CpModel()
    
    activity_var_dict = model_variables(model, activity_dict)
    add_precedence_constraints(model, activity_dict, activity_var_dict)
    max_loads = workload_objective(model, activity_dict, activity_var_dict)
    
    solver = cp_model.CpSolver()
    result_dict, status = solve_model(model, solver, activity_var_dict, max_loads)
    
    if status == cp_model.OPTIMAL :
        plot_schedule(result_dict)
    else :
        print("Cannot find a feasible solution")

## 2. makespan 최소화
def main_makespan() :
    activity_dict = data_information()
    model = cp_model.CpModel()
    
    activity_var_dict = model_variables(model, activity_dict)
    add_precedence_constraints(model, activity_dict, activity_var_dict)
    makespan = makespan_objective(model, activity_dict, activity_var_dict)
    
    solver = cp_model.CpSolver()
    
    result_dict, status = solve_model(model, solver, activity_var_dict, makespan)
    
    if status == cp_model.OPTIMAL :
        plot_schedule(result_dict)
    else :
        print("Cannot find a feasible solution")
        

# 실행부
if __name__ == '__main__':
    # main_workload()
    main_makespan()