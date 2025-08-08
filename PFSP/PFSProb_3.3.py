from ortools.sat.python import cp_model

class PFSPModel:
    def __init__(self, job_data):
        self.job_data = job_data
        self.num_jobs = len(job_data)
        self.num_machines = len(job_data[0])
        self.horizon = sum(sum(row) for row in job_data)
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        self.job_order = []
        self.start = {}
        self.end = {}
        self.duration = {}
        self.makespan = None

    def build_model(self):
        # 순열 결정 변수
        self.job_order = [self.model.NewIntVar(0, self.num_jobs - 1, f'job_order_{i}') for i in range(self.num_jobs)]
        self.model.AddAllDifferent(self.job_order)

        # start, end, duration 변수 생성 및 제약
        for i in range(self.num_jobs):
            for j in range(self.num_machines):
                self.start[i, j] = self.model.NewIntVar(0, self.horizon, f'start_{i}_{j}')
                self.end[i, j] = self.model.NewIntVar(0, self.horizon, f'end_{i}_{j}')
                self.duration[i, j] = self.model.NewIntVar(0, self.horizon, f'duration_{i}_{j}')
                self.model.AddElement(self.job_order[i], [self.job_data[k][j] for k in range(self.num_jobs)], self.duration[i, j])
                self.model.Add(self.end[i, j] == self.start[i, j] + self.duration[i, j])

        # 제약 조건 정의
        for i in range(self.num_jobs) :
            for j in range(self.num_machines) :
                if i==0 and j==0 :
                    pass
                elif i==0 :
                    self.model.Add(self.end[i, j] == self.end[i, j-1] + self.duration[i, j])
                elif j==0 :
                    self.model.Add(self.end[i, j] == self.end[i-1, j] + self.duration[i, j])
                else :
                    self.model.Add(self.start[i, j] >= self.end[i-1, j])
                    self.model.Add(self.start[i, j] >= self.end[i, j-1])

        # makespan 정의 및 최소화
        self.makespan = self.model.NewIntVar(0, self.horizon, 'makespan')
        self.model.AddMaxEquality(self.makespan, [self.end[i, self.num_machines - 1] for i in range(self.num_jobs)])
        self.model.Minimize(self.makespan)

    def solve(self):
        status = self.solver.Solve(self.model)
        return status in (cp_model.OPTIMAL, cp_model.FEASIBLE)

    def print_solution(self):
        if self.makespan is None:
            print("Model not built yet.")
            return
        print(f"\n Optimal Makespan: {self.solver.Value(self.makespan)}")
        print(" Job Order:")
        order = [self.solver.Value(self.job_order[i]) for i in range(self.num_jobs)]
        print(order)
        print("\n Schedule:")
        for i in range(self.num_jobs):
            job_id = self.solver.Value(self.job_order[i])
            print(f"\nJob {job_id} (Position {i}):")
            for j in range(self.num_machines):
                s = self.solver.Value(self.start[i, j])
                e = self.solver.Value(self.end[i, j])
                print(f"  Machine {j}: {s} → {e}")

# 실행부
if __name__ == '__main__':
    job_data = [
        [8, 7, 6, 5],
        [6, 9, 5, 6],
        [9, 5, 7, 4],
        [7, 6, 8, 5]
    ]
    pfsp = PFSPModel(job_data)
    pfsp.build_model()
    if pfsp.solve():
        pfsp.print_solution()
    else:
        print("No feasible solution found.")
