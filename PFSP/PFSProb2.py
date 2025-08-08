from ortools.sat.python import cp_model
import matplotlib.pyplot as plt

class PFSP:
    def __init__(self, job_data):
        self.job_data = job_data
        self.num_jobs = len(job_data)
        self.num_machines = len(job_data[0])
        self.horizon = sum(sum(row) for row in job_data)
        self.model = cp_model.CpModel()

        self.job_order = []
        self.start = {}
        self.end = {}
        self.duration = {}
        self.makespan = None

    def define_variables(self):
        self.job_order = [self.model.NewIntVar(0, self.num_jobs - 1, f'job_order_{i}') for i in range(self.num_jobs)]
        self.model.AddAllDifferent(self.job_order)

        for i in range(self.num_jobs):
            for j in range(self.num_machines):
                self.start[i, j] = self.model.NewIntVar(0, self.horizon, f'start_{i}, {j}')
                self.end[i, j] = self.model.NewIntVar(0, self.horizon, f'end_{i}, {j}')
                self.duration[i, j] = self.model.NewIntVar(0, self.horizon, f'duration_{i}, {j}')

    def add_constraints(self):
        for i in range(self.num_jobs):
            for j in range(self.num_machines):
                # duration[i, j]에 대한 제약
                self.model.AddElement(self.job_order[i], [self.job_data[k][j] for k in range(self.num_jobs)], self.duration[i, j])
                # end [i, j]에 대한 제약
                self.model.Add(self.end[i, j] == self.start[i, j] + self.duration[i, j])
                """
                def AddElement(self, index, variables, target) :
                    Adds the element constraint: variables[index] == target
                """           
                # start time에 대한 제약 추가
                if i > 0:
                    self.model.Add(self.start[i, j] >= self.end[i - 1, j])
                if j > 0:
                    self.model.Add(self.start[i, j] >= self.end[i, j - 1])

    def set_objective(self):
        self.makespan = self.model.NewIntVar(0, self.horizon, 'makespan')
        self.model.AddMaxEquality(self.makespan, [self.end[i, self.num_machines - 1] for i in range(self.num_jobs)])
        self.model.Minimize(self.makespan)
        """
        def AddMaxEquality(self, target, variables)
            Adds target == Max(variables).
        """

    def get_model(self):
        return self.model
    
    def print_solution(self, solver):
        # print(f"\nOptimal Makespan: {solver.Value(self.makespan)}")

        # # Job 순서 출력
        job_order_str = ", ".join([f"Job {solver.Value(job)}" for job in self.job_order])
        # print("\nJob Order:") 
        # print(f"  {job_order_str}")

        print("\nSchedule:")

        for i in range(self.num_jobs):
            job_id = solver.Value(self.job_order[i])
            print(f"\nJob {job_id} (Position {i}):")
            for j in range(self.num_machines): 
                s = solver.Value(self.start[i, j])
                e = solver.Value(self.end[i, j]) 
                print(f"  Machine {j}: {s} → {e}")
                
        # Job 순서 출력
        print("\nJob Order:") 
        print(f"  {job_order_str}")

        print(f"\nOptimal Makespan: {solver.Value(self.makespan)}")


    # # 스케줄링 결과 Gantt Chart로 시각화 함수 (matplotlib)
    # def plot_gantt_chart(self, solver):
    #     fig, ax = plt.subplots(figsize=(12, 6))
    #     colors = plt.cm.Paired.colors  # Job별 색상 자동 설정

    #     # 기계별 작업 스케줄 수집
    #     machine_schedule = {j: [] for j in range(self.num_machines)}

    #     for i in range(self.num_jobs):
    #         job_id = solver.Value(self.job_order[i])
    #         for j in range(self.num_machines):
    #             start = solver.Value(self.start[i, j])
    #             end = solver.Value(self.end[i, j])
    #             machine_schedule[j].append((start, end, job_id))

    #     # 각 기계에 대해 작업 막대 출력
    #     for machine_id, tasks in machine_schedule.items():
    #         tasks.sort()  # 시작 시간 기준 정렬
    #         for start, end, job_id in tasks:
    #             ax.barh(machine_id, end - start, left=start,
    #                     color=colors[job_id % len(colors)], edgecolor='black')
    #             ax.text(start + (end - start) / 2, machine_id,
    #                     f'J{job_id}\n({start}-{end})',
    #                     ha='center', va='center', fontsize=8, color='black')

    #     # 축 및 스타일 설정
    #     ax.set_yticks(range(self.num_machines))
    #     ax.set_yticklabels([f"Machine {j}" for j in range(self.num_machines)])
    #     ax.set_xlabel("Time")
    #     ax.set_title("Gantt Chart for PFSP Schedule")
    #     ax.grid(True, axis='x', linestyle='--', alpha=0.6)

    #     plt.tight_layout()
    #     plt.savefig('pfsp_gantt_chart.png', dpi=300)
    #     plt.show()

    ## terminal에 간트차트 출력 (text-based)
    
    # def print_gantt_chart(self, solver):
    #     print("\nGantt Chart :\n")

    #     # 기계별로 시간순으로 정렬된 작업 리스트 생성
    #     machine_schedule = {j: [] for j in range(self.num_machines)}

    #     for i in range(self.num_jobs):
    #         job_id = solver.Value(self.job_order[i])
    #         for j in range(self.num_machines):
    #             start = solver.Value(self.start[i, j])
    #             end = solver.Value(self.end[i, j])
    #             machine_schedule[j].append((start, end, job_id))

    #     # 각 기계별 작업을 시작 시간 기준으로 정렬
    #     for j in range(self.num_machines):
    #         machine_schedule[j].sort()

    #     # Gantt Chart 출력
    #     for j in range(self.num_machines):
    #         print(f"Machine {j}: ", end='')
    #         current_time = 0
    #         for start, end, job in machine_schedule[j]:
    #             # 공백 출력 (idle time)
    #             if start > current_time:
    #                 print(" " * (start - current_time), end='')

    #             # 작업 출력
    #             duration = end - start
    #             print(f"|J{job}" + "-" * (duration - 2) + "|", end='')
    #             current_time = end
    #         print() # \n

def data_preprocess(filepath):
    with open(filepath, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]  # 공백 제거

    # Line별 추출
    demand_plan = list(map(int, lines[0].split()))
    # layout_type = lines[1] # line개수를 의미하는 듯 (?)
    num_of_jobs = int(lines[2]) # total job의 개수
    # num_of_machines_per_line = int(lines[3])
    num_of_machines = int(lines[4]) # machine의 개수
    num_of_sorts = int(lines[5]) # == job의 종류

    # Line 6~ : machine 별 처리 시간 ( row : machine, coulumn: Job type)
    raw_processing_time = []
    for line in lines[6 : 6 + num_of_machines]: # line[6] ~ 6 + num_of_machines 까지
        times = list(map(int, line.split()))
        raw_processing_time.append(times)  # 각 줄: 각 machine의 job 당 수행 시간

    # 각 job의 demand를 고려한 계산용 dataset 정의
    transposed_raw_processing_time = list(map(list, zip(*raw_processing_time))) # [machine, job] -> [job, machine]
    # 3. demand_plan 기반 복제
    processing_times_dataset = []
    for i, count in enumerate(demand_plan):
        for _ in range(count):
            processing_times_dataset.append(transposed_raw_processing_time[i])
    

    # return {
    #     # "layout_type": layout_type,
    #     "num_of_machines": num_of_machines,
    #     "num_of_sorts": num_of_sorts,
    #     "num_of_jobs" : num_of_jobs,
    #     "processing_time" : processing_times_dataset
    # }

    return processing_times_dataset

# 실행부
def data_information():
    return [
        [8, 7, 6, 5],
        [6, 9, 5, 6],
        [9, 5, 7, 4],
        [7, 6, 8, 5]
    ]

if __name__ == '__main__':
    
    job_data = data_preprocess('C:/Users/eclas/source/repos/constraint_programming/Tai_PFSP_1L_3/t17_100_20_10_3.mix')
    
    pfsp = PFSP(job_data)
    pfsp.define_variables()
    pfsp.add_constraints()
    pfsp.set_objective()

    solver = cp_model.CpSolver()
    solver.parameters.log_search_progress = True 
    solver.parameters.max_time_in_seconds = 600.0
    status = solver.Solve(pfsp.get_model())

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        pfsp.print_solution(solver)
        # pfsp.plot_gantt_chart(solver)
        # pfsp.print_gantt_chart(solver)
    else:
        print("No feasible solution found.")