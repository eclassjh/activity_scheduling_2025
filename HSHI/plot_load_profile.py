import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

def plot_load_profile(result_dict, activity_dict, savepath="load_profile.png"):
    """
    해(result_dict)와 activity_dict를 이용해 시간대별 총 부하(=동시 수요 합)를 라인 그래프로 시각화.

    Args:
        result_dict (Dict[str, Dict]): solve_model()이 반환한 스케줄 결과 {key: {'start','end','duration'}}
        activity_dict (Dict[str, Activity]): 각 Activity 객체(여기서 .load_size, .duration를 사용)
        savepath (str|None): 저장 경로. None이면 화면에 표시만 함.

    동작:
        - 전체 스케줄 구간 [t=0 .. makespan)에서 각 시점 t마다
        active한 작업들의 load_size를 합산하여 profile[t]로 기록.
    """

    # 1) 프로파일 계산
    makespan = max(v['end'] for v in result_dict.values())
    profile = [0] * (makespan + 1)
    for key, res in result_dict.items():
        start, end = res['start'], res['end']
        demand = getattr(activity_dict[key], "load_size", 1)
        for t in range(start, end):
            profile[t] += demand

    # 2) 플롯 설정
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(
        range(len(profile)), profile,
        color="#C00000",
        linewidth=2.5
    )

    # 축 라벨
    ax.set_xlabel("Day", fontsize=15, labelpad=8)
    ax.set_ylabel("Workload", fontsize=15, labelpad=8)

    # x축: 정수 눈금
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.tick_params(axis='x', labelsize=12)


    # y축: 숫자 라벨 숨기고, 점선 그리드 표시
    ax.set_yticklabels([])
    ax.yaxis.grid(True, linestyle='--', alpha=0.5)

    # 테두리 제거
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # 폰트 & 레이아웃 정리
    plt.tight_layout()

    # 저장 or 표시
    if savepath:
        fig.savefig(savepath, dpi=150, bbox_inches='tight')
        plt.close(fig)
    else:
        plt.show()

def plot_initial_load_profile(activity_dict, savepath="initial_load_profile.png"):
    """
    스케줄링 전(착수일에 바로 배치) 부하 프로파일 라인그래프
    - activity_dict: 각 Activity 객체 (earliest_start_time, duration, load_size 필요)
    - x축: Day
    - y축: Workload (y축 숫자 숨기고 그리드 표시)
    """
    if not activity_dict:
        print("activity_dict가 비어 있습니다.")
        return

    # 1) makespan 계산
    makespan = max(a.earliest_start_time + a.duration for a in activity_dict.values())
    profile = [0] * (makespan + 1)

    # 2) 각 작업을 earliest_start_time에 배치
    for act in activity_dict.values():
        start = act.earliest_start_time
        end = start + act.duration
        demand = getattr(act, "load_size", 1)
        for t in range(start, end):
            profile[t] += demand

    # 3) 그래프 그리기
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(
        range(len(profile)), profile,
        color="#3A7520",         # 빨강 계열
        linewidth=2.5
    )

    ax.set_xlabel("Day", fontsize=15, labelpad=8)
    ax.set_ylabel("Workload", fontsize=15, labelpad=8)

    # x축 정수 눈금
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.tick_params(axis='x', labelsize=12)

    # y축 숫자 숨기고, 그리드 표시
    ax.set_yticklabels([])
    ax.yaxis.grid(True, linestyle='--', alpha=0.5)

    # 테두리 제거
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()

    if savepath:
        fig.savefig(savepath, dpi=150, bbox_inches='tight')
        plt.close(fig)
    else:
        plt.show()

def plot_load_comparison(result_dict, activity_dict, savepath="load_comparison.png"):
    """
    스케줄링 전/후 부하 프로파일을 한 그래프에 비교해서 표시.
    
    - 빨간색: 스케줄링 전 (earliest_start_time에 배치)
    - 파란색: 스케줄링 후 (result_dict 기반)
    - x축: Day, y축: Workload (숫자 숨기고 그리드 표시)
    """
    if not activity_dict or not result_dict:
        print("activity_dict 또는 result_dict가 비어 있습니다.")
        return

    # 1) 스케줄링 전 부하 (earliest_start_time 기준)
    pre_makespan = max(a.earliest_start_time + a.duration for a in activity_dict.values())
    pre_profile = [0] * (pre_makespan + 1)
    for act in activity_dict.values():
        start = act.earliest_start_time
        end = start + act.duration
        demand = getattr(act, "load_size", 1)
        for t in range(start, end):
            pre_profile[t] += demand

    # 2) 스케줄링 후 부하 (result_dict 기반)
    post_makespan = max(v['end'] for v in result_dict.values())
    post_profile = [0] * (post_makespan + 1)
    for key, res in result_dict.items():
        start, end = res['start'], res['end']
        demand = getattr(activity_dict[key], "load_size", 1)
        for t in range(start, end):
            post_profile[t] += demand

    # 3) 두 프로파일 길이 맞추기
    max_len = max(len(pre_profile), len(post_profile))
    pre_profile += [0] * (max_len - len(pre_profile))
    post_profile += [0] * (max_len - len(post_profile))

    fig, ax = plt.subplots(figsize=(15, 4))

    blue_color = "#224C7A"   # 파란 계열
    green_color = "#3A7520"  # 초록 계열
    red_color = "#C00000"
    
    ax.plot(range(max_len), pre_profile, color=blue_color, linewidth=2.5, label="Before Optimization")
    ax.plot(range(max_len), post_profile, color=red_color, linewidth=2.5, label="After Optimization")

    # 축 라벨
    ax.set_xlabel("Day", fontsize=16, labelpad=8)
    ax.set_ylabel("Workload", fontsize=16, labelpad=8)

    # x축: 정수 눈금 + 폰트 크기
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.tick_params(axis='x', labelsize=14)

    # y축: 숫자 숨기고, 점선 그리드 표시
    ax.set_yticklabels([])
    ax.yaxis.grid(True, linestyle='--', alpha=0.5)

    # 테두리 정리
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # 범례
    ax.legend(frameon=False, fontsize=14)

    plt.tight_layout()

    if savepath:
        fig.savefig(savepath, dpi=150, bbox_inches='tight')
        plt.close(fig)
    else:
        plt.show()