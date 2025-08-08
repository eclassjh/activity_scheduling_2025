from ortools.sat.python import cp_model

# PFSP 클래스 정의
class PFSP:
    def __init__(self, job_data, permutation):
        self.job_data = job_data
        self.permutation = permutation
        self.num_jobs = len(job_data)
        self.num_machines = len(job_data[0])

    def processing_time(self, i, j):
        # i번째 순서에 오는 작업의 j번째 기계에서 소요 시간
        job = self.permutation[i]
        return self.job_data[job][j]

    def completion_time(self):
        # PFSP Completion Time 계산
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

def data_information():
    job_data = [
        [8, 7, 6, 5], 
        [6, 9, 5, 6],
        [9, 5, 7, 4], 
        [7, 6, 8, 5]
    ]
    return job_data

def add_permutation_constraints(model, job_data):
    # permutation 결정변수 정의 및 제약 추가
    n = len(job_data)

    # 각 job의 순서를 정의한 job_permuataion 정의 (IntVar이 묶인 List type)
    job_permutation = [model.NewIntVar(0, n - 1, f'order_{i}') for i in range(n)] 
    # n번째 해야 할 Job의 number가 정의 된 형태
    # order_i : 각 IntVar 변수의 이름. 디버깅용 ..

    model.AddAllDifferent(job_permutation) # 각 순서는 달라야 한다는 조건 추가

    return job_permutation

# 각 해마다 PFSP completion time을 평가하기 위한 callback class 정의
# 해를 하나 찾을 때마다 자동으로 호출되는 콜백 (class 형태)
class PermutationEvaluationCallback(cp_model.CpSolverSolutionCallback):
    def __init__(self, job_permutation, job_data):
        cp_model.CpSolverSolutionCallback.__init__(self) # 부모 class 생성자 호출
        self.job_permutation = job_permutation
        self.job_data = job_data
        self.best_makespan = None
        self.best_order = None
        self.solution_count = 0

    # solver가 계산한 각 permutation별 makespan 계산값을 print하고 best_makespan값을 update하는 형식
    # 내부적으로 SearchForAllSolutions() 실행 시 자동으로 callback되는 함수로 정의 되어 있음음
    def on_solution_callback(self):
        self.solution_count += 1
        current_order = [self.Value(v) for v in self.job_permutation] # 각 permutation 변수(line 47의 result)의 값을 읽어서 리스트로 만듦 ## [2,0,1,3]
        pfsp = PFSP(self.job_data, current_order)
        makespan = pfsp.completion_time()

        print(f"[{self.solution_count}th] Permutation: {current_order} , makespan = {makespan}")

        if self.best_makespan is None or makespan < self.best_makespan:
            self.best_makespan = makespan
            self.best_order = current_order

# main 함수
def main():
    job_data = data_information()    
    model = cp_model.CpModel()
    job_permutation = add_permutation_constraints(model,job_data)

    solver = cp_model.CpSolver()
    solution_evaluation = PermutationEvaluationCallback(job_permutation, job_data)

    # 모든 가능한 순열을 탐색하면서 PFSP makespan 평가
    solver.SearchForAllSolutions(model, solution_evaluation)
        
    print("\n" + "="*40)
    print("Best order:", solution_evaluation.best_order)
    print("Makespan:", solution_evaluation.best_makespan)
    print("="*40)

if __name__ == '__main__':
    main()
