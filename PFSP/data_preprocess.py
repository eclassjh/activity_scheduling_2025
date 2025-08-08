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
    

    return {
        # "layout_type": layout_type,
        "num_of_machines": num_of_machines,
        "num_of_sorts": num_of_sorts,
        "num_of_jobs" : num_of_jobs,
        "processing_time" : processing_times_dataset
    }

# 실행확인
data = data_preprocess('C:/Users/eclas/source/repos/constraint_programming/Tai_PFSP_2L_4/t14_20_10_10_7.mix') # type : dict

# print(data["processing_time"])
print("Total number of jobs : ", data["num_of_jobs"])
print("Total number of machines : ", data["num_of_machines"])

# print("Shape of processed data :", len(data["processing_time"]), len(data["processing_time"][0]))
print(f"Shape of processed data : {len(data['processing_time'])}, {len(data['processing_time'][0])}")