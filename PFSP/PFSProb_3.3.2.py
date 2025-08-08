# 리팩토링된 PFSPModel 클래스 (position ↔ job 매핑 포함, IntVar 키 오류 수정)
from ortools.sat.python import cp_model

class PFSPModel:
    def __init__(self, job_data):
        self.job_data = job_data
        self.num_jobs = len(job_data)
        self.num_machines = len(job_data[0])
        self.horizon = sum(sum(row) for row in job_data)
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()

        self.job_in_position = []
        self.position_of_job = []

        self.start_time = {}  # (position, machine)
        self.end_time = {}    # (position, machine)

        self.makespan = None

    def build_model(self):
        # 순열결정변수 
        # i번째로 실행되는 job 정의
        self.job_in_position = [self.model.NewIntVar(0, self.num_jobs - 1, f'job_in_position_{i}') for i in range(self.num_jobs)]
        # job n이이 몇번째로 실행되는지 정의
        self.position_of_job = [self.model.NewIntVar(0, self.num_jobs - 1, f'position_of_job_{n}') for n in range(self.num_jobs)]
        self.model.AddAllDifferent(self.job_in_position)
        self.model.AddAllDifferent(self.position_of_job)
        # 서로 역의 관계에 있음을 정의 (제약조건 #1)
        self.model.AddInverse(self.job_in_position, self.position_of_job)

        for i in range(self.num_jobs):
            for j in range(self.num_machines):
                self.start_time[i, j] = self.model.NewIntVar(0, self.horizon, f'start_{i}_{j}')
                self.end_time[i, j] = self.model.NewIntVar(0, self.horizon, f'end_{i}_{j}')

        for i in range(self.num_jobs):
            job = self.job_in_position[i]
            for m in range(self.num_machines):
                duration = self.model.NewIntVar(0, self.horizon, f'duration_{i}_{m}')
                self.model.AddElement(job, [self.job_data[k][m] for k in range(self.num_jobs)], duration)
                self.model.Add(self.end_time[i, m] == self.start_time[i, m] + duration)

                if m > 0:
                    self.model.Add(self.start_time[i, m] >= self.end_time[i, m - 1])
                if i > 0:
                    self.model.Add(self.start_time[i, m] >= self.end_time[i - 1, m])

        self.makespan = self.model.NewIntVar(0, self.horizon, 'makespan')
        self.model.AddMaxEquality(self.makespan, [self.end_time[i, self.num_machines - 1] for i in range(self.num_jobs)])
        self.model.Minimize(self.makespan)

    def solve(self):
        status = self.solver.Solve(self.model)
        return status in (cp_model.OPTIMAL, cp_model.FEASIBLE)

    def print_solution(self):
        if self.makespan is None:
            print("Model not built yet.")
            return

        print(f"\nOptimal Makespan: {self.solver.Value(self.makespan)}")
        print("Job Order:")
        for pos in range(self.num_jobs):
            job = self.solver.Value(self.job_in_position[pos])
            print(f"  Position {pos}: Job {job}")

        print("\nSchedule:")
        for pos in range(self.num_jobs):
            job = self.solver.Value(self.job_in_position[pos])
            print(f"\nJob {job} (Position {pos}):")
            for m in range(self.num_machines):
                s = self.solver.Value(self.start_time[pos, m])
                e = self.solver.Value(self.end_time[pos, m])
                print(f"  Machine {m}: {s} → {e}")

# 실행부

def data_information():
    return [
        [8, 7, 6, 5],
        [6, 9, 5, 6],
        [9, 5, 7, 4],
        [7, 6, 8, 5]
    ]

if __name__ == '__main__':
    job_data = data_information()
    pfsp = PFSPModel(job_data)
    pfsp.build_model()
    if pfsp.solve():
        pfsp.print_solution()
    else:
        print("No feasible solution found.")