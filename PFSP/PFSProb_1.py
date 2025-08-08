from ortools.sat.python import cp_model

def data_information():
    return [
        [8, 7, 6, 5],
        [6, 9, 5, 6],
        [9, 5, 7, 4],
        [7, 6, 8, 5]
    ]

def solve_pfsp(model, job_data):
    num_jobs = len(job_data)
    num_machines = len(job_data[0])
    
    # model = cp_model.CpModel()

    upper_bound = 50
    # upper_bound = sum(sum(row) for row in job_data)

    # 변수 정의
    start_vars, end_vars, interval_vars = {}, {}, {}
    for job in range(num_jobs):
        for machine in range(num_machines):
            suffix = f'_{job}_{machine}'
            start = model.NewIntVar(0, upper_bound, f'start{suffix}')
            duration = job_data[job][machine]
            end = model.NewIntVar(0, upper_bound, f'end{suffix}')
            interval = model.NewIntervalVar(start, duration, end, f'interval{suffix}')

            start_vars[(job, machine)] = start
            end_vars[(job, machine)] = end
            interval_vars[(job, machine)] = interval

    # 작업 내 순차 제약
    for job in range(num_jobs):
        for machine in range(num_machines - 1):
            model.Add(start_vars[(job, machine + 1)] >= end_vars[(job, machine)])

    # 머신별 NoOverlap 제약
    for machine in range(num_machines):
        machine_intervals = [interval_vars[(job, machine)] for job in range(num_jobs)]
        model.AddNoOverlap(machine_intervals)

    # 목적함수: makespan 최소화
    makespan = model.NewIntVar(0, upper_bound, 'makespan')
    model.AddMaxEquality(makespan, [end_vars[(job, num_machines - 1)] for job in range(num_jobs)])
    model.Minimize(makespan)

    # Solver 실행
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    # 결과 출력
    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        # 각 job의 첫 머신 start 시간으로 정렬
        job_start_times = [(job, solver.Value(start_vars[(job, 0)])) for job in range(num_jobs)]
        job_start_times.sort(key=lambda x: x[1])
        best_order = [job for job, _ in job_start_times]

        print("Best order:", best_order)
        print("Makespan:", solver.Value(makespan))
        
    else:
        print("No feasible solution")

def main():
    job_data = data_information()
    model = cp_model.CpModel()
    solve_pfsp(model, job_data)

if __name__ == "__main__":
    main()
