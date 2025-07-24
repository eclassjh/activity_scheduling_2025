# terminal 결과 출력 함수

def print_workload_result(result_dict, cumulative_workload):
    print("=" * 40)
    print("Activity Scheduling Result")
    print("=" * 40)
        
    total_end = 0
    for key, val in result_dict.items():
        start = val['start']
        end = val['end']
        duration = val['duration']
        calc_duration = end - start
        total_end = max(total_end, end)
        print(f"Activity {key}: Start = {start}, End = {end}, Calc_Duration = {calc_duration}, Duration = {duration}")
    
    print("=" * 40)
    print(f" Total Makespan : {total_end}")
    print("=" * 40)
    
    # 시간별 작업 부하 로그
    print("Time-wise Workload Log")
    print(cumulative_workload)