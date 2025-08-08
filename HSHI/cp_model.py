from ortools.sat.python import cp_model

from data_preprocessing import *
from plot_gantt import *
from print_result import *
from plot_load_profile import *
from save_to_xlsx import *
from save_to_csv import *

# 1. CP모델 관련 함수
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
def model_variables(model, activity_dict): 
    """
        활동별 변수 선언 함수
        순서 :
            1. 기존 데이터셋 (activity_dict)에서 활동별 변수를 추출하여 모델에 적용 가능한 변수로 정리
            2. 기존 데이터셋에서 '데이터' 와 '변수'를 분리하여, 변수로 사용되는 데이터(추후 모델이 정해주는 값)만 모델변수로 정의
            3. 모델 변수를 묶어서 다시 activity_var_dict에 저장
        """
    activity_var_dict = dict()
    
    for key, value in activity_dict.items():
        start_var = model.NewIntVar(value.earliest_start_time, value.latest_start_time, f'{key}_start')
        duration = value.duration
        end_var = model.NewIntVar(value.earliest_start_time + value.duration, value.latest_start_time + value.duration, f'{key}_end')

        interval_var = model.NewIntervalVar(start_var, duration, end_var, f'{key}_interval')
        
        activity_var_dict[key] = interval_var
        
    return activity_var_dict

## C. 목적함수 정의
def workload_objective(model, activity_dict, activity_var_dict):
    """
        최대 작업 부하를 최소화하는 목적함수를 정의하는 함수
        - 각 Activity에 해당하는 구간(interval) 변수와 작업량(load_size)을 기반으로 누적 부하(cumulative_workload) 계산
        - AddCumulative 제약을 이용하여 모든 시간 구간에서의 부하가 max_workload를 초과하지 않도록 설정
        - max_workload를 최소화하는 것을 모델의 목적함수로 설정
    """
    interval_vars = []
    cumulative_workload = []
    total_load = sum(activity.load_size for activity in activity_dict.values())
    
    max_workload = model.NewIntVar(0, int(total_load+1), 'max_workload')
    
    for key, interval_var in activity_var_dict.items():
        # activity_info = activity_dict[key]
        load_size = activity_dict[key].load_size
        cumulative_workload.append(load_size)
        interval_vars.append(interval_var)
                
    model.AddCumulative(interval_vars, cumulative_workload, max_workload)
    model.Minimize(max_workload)
    
    return max_workload, cumulative_workload


# 2. main 함수
def main_workload(filepath) :
    """
        최대 부하 최소화를 목표로 하는 CP 모델 실행 함수
        순서 :
            1. 데이터 전처리 및 작업 정보(Activity) 생성
            2. CP 모델(cp_model.CpModel) 정의
            3. 변수 정의 (시작, 종료 등)
            4. 최대 부하 최소화 목적함수 설정 및 누적 부하 계산
            5. CP-SAT Solver 실행 및 결과 추출
            6. 해가 존재할 경우:
                - 간트차트 시각화
                - 일별 리소스 부하 출력
                - 스케줄 결과 CSV 저장
            7. 해가 존재하지 않을 경우:
                - 해가 없음을 출력
    """
    activity_dict, base_date = data_preprocessing(filepath)
    model = cp_model.CpModel()
    
    activity_var_dict = model_variables(model, activity_dict)
    max_loads, cumulative_workload  = workload_objective(model, activity_dict, activity_var_dict)
    
    solver = cp_model.CpSolver()
    solver.parameters.log_search_progress = True
    solver.parameters.max_time_in_seconds = 10.0
    
    result_dict, status = solve_model(model, solver, activity_var_dict, max_loads)
    
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):        
        # plot_schedule(result_dict)
        plot_load_profile(result_dict, activity_dict)
        plot_initial_load_profile(activity_dict)
        plot_load_comparison(result_dict, activity_dict)
        print_workload_result(result_dict, cumulative_workload)
        save_to_xlsx(result_dict, activity_dict, base_date)
    else :
        print("Cannot find a feasible solution")
