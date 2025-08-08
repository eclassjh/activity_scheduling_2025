from ortools.sat.python import cp_model
import matplotlib.pyplot as plt
# import random
# import math
# import copy
import numpy as np

class PFSP:
    def __init__(self, job_data, permutation):
        self.job_data = job_data
        self.permutation = permutation
        self.num_jobs = len(job_data)
        self.num_machines = len(job_data[0])

    def processing_time(self, i, j):
        # i번째 job의 j번째 machine에서의 소요시간 return
        job = self.permutation[i]
        return self.job_data[job][j]

    def completion_time(self):
        # 전체 completion time(C_ij) 을 계산하는 함수

        C = [[0 for _ in range(self.num_machines)] for _ in range(self.num_jobs)]

        for i in range(self.num_jobs):
            for j in range(self.num_machines):
                if i == 0 and j == 0:
                    C[i][j] = self.processing_time(i, j)
                elif i == 0:
                    C[i][j] = C[i][j - 1] + self.processing_time(i, j)
                elif j == 0:
                    C[i][j] = C[i - 1][j] + self.processing_time(i, j)
                else:
                    C[i][j] = max(C[i - 1][j], C[i][j - 1]) + self.processing_time(i, j)
        
        return C[-1][-1]

def data_information() :
    # job_data: 2차원원 list, 각 작업의 각 기계에서의 처리 시간
    job_data = [
        [8, 7, 6, 5], 
        [6, 9, 5, 6],
        [9, 5, 7, 4], 
        [7, 6, 8, 5]
    ]
    return job_data

def add_permutation_constraints(model, job_data):
    # job의 순서를 나타내는 순열 생성
    # 변수 배열 형태로만 solve가 가능하기 때문에 추후에 순서만을 list 형태로 받아야 함
    
    n = len(job_data)
    # 순서를 나타내는 변수 배열 생성 : (job의 개수 만큼)
    permutation = [model.NewIntVar(0, n - 1, f'order_{i}') for i in range(n)]
    # 제약조건(AllDifferent) : job의 번호는 모두 달라야 함
    model.AddAllDifferent(permutation)

    return permutation
  
    """
    solver.Solve(model)
    actual_order = [solver.Value(var) for var in permutation]
    print(actual_order)  # 예: [2, 0, 3, 1]
    """

def add_objective_makespan(model, completion_time) :
    # makespan을 최소화 하는 목적함수 정의
    
    # 전체 프로젝트 기간을 나타내는 makespan 변수 정의
    makespan = model.NewIntVar(0, completion_time, 'makespan')
    
    model.Add(makespan >= completion_time)
    
    # makespan 최소화를 목적함수로 설정
    model.Minimize(makespan)
    return makespan

def main():
    # 1. 데이터 불러오기
    job_data = data_information()
    
    # 2. CP-SAT 모델 생성
    model = cp_model.CpModel()

    # 3. 순열 변수 및 제약 추가
    order_vars = add_permutation_constraints(model, job_data)

    # 4. Solver 선언 및 실행
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    # 5. 결과 해석
    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        best_order = [solver.Value(v) for v in order_vars]
        pfsp = PFSP(job_data, best_order)
        completion_time = pfsp.completion_time()  # or pfsp.makespan()
        ## here
        makespan = add_objective_makespan(model, completion_time)
        print("Best order:", best_order)
        print("makespan:", makespan)
        # print("Final makespan:", makespan)
    else:
        print("No feasible solution found.")


if __name__ == "__main__":
    main()