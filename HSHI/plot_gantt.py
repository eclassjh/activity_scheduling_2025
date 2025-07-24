import matplotlib.pyplot as plt

# 간트차트 생성 함수
import matplotlib.pyplot as plt

# 간트차트 생성 함수
def plot_schedule(results_dict):
        num_tasks = len(results_dict)

        # figsize를 작업 수에 따라 동적으로 설정 (너비 제한 포함)
        width = min(40, num_tasks * 0.5)
        height = min(15, max(6, num_tasks * 0.4))
        fig, ax = plt.subplots(figsize=(width, height))

        colors = ['red', 'blue', 'green', 'orange', 'purple', 'cyan', 'brown']

        # 각 활동별 막대 차트 생성
        for i, (key, data) in enumerate(results_dict.items()):
                start, end = data['start'], data['end']
                duration = end - start
                ax.barh(i, duration, left=start, color=colors[i % len(colors)],
                        alpha=0.8, label=key)
                ax.text(start + duration / 2, i, f'{key}\n({start}-{end})',
                        ha='center', va='center', fontsize=8)

        # 차트 커스터마이징
        ax.set_title('Schedule Gantt Chart')
        ax.set_xlabel('Time')
        ax.grid(True, axis='x', linestyle='--', alpha=0.7)

        # X축 범위 자동 지정 (start~end 중 최대값 기준)
        min_x = min(data['start'] for data in results_dict.values())
        max_x = max(data['end'] for data in results_dict.values())
        ax.set_xlim(min_x - 1, max_x + 1)
        ax.set_xticks(range(min_x, max_x + 2))

        # Y축 제거
        ax.set_yticks([])

        # 범례 (최대 7개까지 한 줄에 표시)
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=min(7, num_tasks))

        # 저장 및 표시 (dpi 줄이기!)
        plt.tight_layout()
        plt.savefig('gantt_chart.png', bbox_inches='tight', dpi=100)
        plt.show()
