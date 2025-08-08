from ortools.sat.python import cp_model

class PFSP:
    def __init__(self, job_data, upper_bound=None):
        self.job_data = job_data
        self.num_jobs = len(job_data)
        self.num_machines = len(job_data[0])
        self.upper_bound = upper_bound or sum(sum(row) for row in job_data)

        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()

        self.start_vars = {}
        self.end_vars = {}
        self.interval_vars = {}
        self.makespan = None
        self.best_order = []

    def build_model(self):
        # 작업-기계별 시작, 종료, 간격 변수 생성
        for job in range(self.num_jobs):
            for machine in range(self.num_machines):
                suffix = f'_{job}_{machine}'
                duration = self.job_data[job][machine]

                start = self.model.NewIntVar(0, self.upper_bound, f'start{suffix}')
                end = self.model.NewIntVar(0, self.upper_bound, f'end{suffix}')
                interval = self.model.NewIntervalVar(start, duration, end, f'interval{suffix}')

                self.start_vars[(job, machine)] = start
                self.end_vars[(job, machine)] = end
                self.interval_vars[(job, machine)] = interval

        # 각 작업의 순차 흐름 보장
        for job in range(self.num_jobs):
            for machine in range(self.num_machines - 1):
                self.model.Add(self.start_vars[(job, machine + 1)] >= self.end_vars[(job, machine)])

        # 각 머신에선 동시에 한 작업만 수행 가능
        for machine in range(self.num_machines):
            intervals = [self.interval_vars[(job, machine)] for job in range(self.num_jobs)]
            self.model.AddNoOverlap(intervals)

        # makespan 정의 및 최소화
        self.makespan = self.model.NewIntVar(0, self.upper_bound, 'makespan')
        final_tasks = [self.end_vars[(job, self.num_machines - 1)] for job in range(self.num_jobs)]
        self.model.AddMaxEquality(self.makespan, final_tasks)
        self.model.Minimize(self.makespan)

    def solve(self):
        status = self.solver.Solve(self.model)
        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            # 각 job의 첫 머신 시작 시간으로 best order 추출
            job_starts = [(job, self.solver.Value(self.start_vars[(job, 0)])) for job in range(self.num_jobs)]
            job_starts.sort(key=lambda x: x[1])
            self.best_order = [job for job, _ in job_starts]
            return True
        return False

    def get_results(self):
        return {
            'best_order': self.best_order,
            'makespan': self.solver.Value(self.makespan) if self.makespan is not None else None
        }


def data_information():
    return [
        [8, 7, 6, 5],
        [6, 9, 5, 6],
        [9, 5, 7, 4],
        [7, 6, 8, 5]
    ]

def main():
    job_data = data_information()
    pfsp = PFSP(job_data, upper_bound=50)
    pfsp.build_model()
    if pfsp.solve():
        result = pfsp.get_results()
        print("Best order:", result['best_order'])
        print("Makespan:", result['makespan'])
    else:
        print("No feasible solution")

if __name__ == "__main__":
    main()
