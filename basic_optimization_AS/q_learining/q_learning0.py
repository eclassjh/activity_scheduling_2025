from dataclasses import dataclass
from collections import defaultdict, deque
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import random

@dataclass
class Activity:
    duration: int
    earliest_start: int
    latest_start: int
    predecessors: list[str]

def _parse_pred_cell(cell) -> list[str]:
    """precedence 셀 파싱: '1, 2' or 'a1, a2' 모두 허용 → ['a1','a2']로 정규화"""
    if pd.isna(cell):
        return []
    tokens = str(cell).split(',')
    preds = []
    for t in tokens:
        s = t.strip()
        if not s:
            continue
        if s.isdigit():
            preds.append(f"a{int(s)}")
        else:
            # 'a1' 같은 형식 처리
            if s.lower().startswith('a') and s[1:].isdigit():
                preds.append(f"a{int(s[1:])}")
            else:
                # 형식이 애매하면 그대로 두고 후에 검증에서 잡히게 함
                preds.append(s)
    return preds

def data_preprocessing(filepath: str):
    df = pd.read_csv(filepath)

    # 1) Activity dict 구성
    activities: dict[str, Activity] = {}
    for _, row in df.iterrows():
        name = str(row["activity_name"]).strip()
        duration = int(row["duration"])
        earliest = int(row["earliest_start_time"])
        latest = int(row["latest_start_time"])
        predecessors = _parse_pred_cell(row.get("precedence", None))

        activities[name] = Activity(
            duration=duration,
            earliest_start=earliest,
            latest_start=latest,
            predecessors=predecessors
        )

    # 2) 노드 목록
    nodes = set(activities.keys())

    # 3) 그래프(후속), 역그래프(선행), in_degree 초기화
    succ: dict[str, list[str]] = {u: [] for u in nodes}
    pred: dict[str, set[str]] = {u: set() for u in nodes}
    in_degree: dict[str, int] = {u: 0 for u in nodes}

    # 4) 간선 생성: p -> u (p가 선행, u가 후속)
    #    - 존재하지 않는 선행이 있으면 경고/무시 등 정책 정해서 처리
    for u, act in activities.items():
        for p in act.predecessors:
            if p not in nodes:
                # 필요하면 raise로 강하게 체크 가능
                # raise ValueError(f"Unknown predecessor {p} for {u}")
                # 일단은 스킵
                continue
            succ[p].append(u)
            pred[u].add(p)
            in_degree[u] += 1

    # 5) 초기 가용 집합(=in_degree==0)
    zero_in = {u for u, deg in in_degree.items() if deg == 0}

    # 6) 모두 하나의 dict로 묶어 반환 (네가 선호한 형태)
    return {
        "activities": activities,  # Activity dataclass들
        "succ": succ,              # u -> [후속들]
        "pred": pred,              # u -> {선행들}
        "in_degree": in_degree,    # u -> 미충족 선행 수
        "available": zero_in       # 시작 가능 집합 (tie-breaker 풀)
    }
    
def extract_priority_list(successors: dict, in_deg: dict, mode="fifo", score_fn=None, rng=None):
    """
    mode: 'fifo' | 'argmin' | 'random'
      - fifo    : 큐(FIFO)로 처리 (안정적)
      - argmin  : 매 스텝 score_fn로 최소값 선택 (tie-breaker 자주 바뀔 때)
      - random  : 가용 집합에서 무작위 선택
    score_fn(u): argmin용 점수 함수. 없으면 문자열 기준(min).
    """
    n = len(in_deg)
    order = []

    if mode == "fifo":
        Q = deque(sorted([u for u,d in in_deg.items() if d == 0]))  # 초기 안정적 순서
        in_deg = in_deg.copy()
        while Q:
            u = Q.popleft()
            order.append(u)
            for v in successors.get(u, []):
                in_deg[v] -= 1
                if in_deg[v] == 0:
                    Q.append(v)
    else:
        avail = {u for u,d in in_deg.items() if d == 0}
        in_deg = in_deg.copy()
        rnd = rng or random
        while avail:
            if mode == "random":
                u = rnd.choice(tuple(avail))
            elif mode == "argmin":
                key = score_fn or (lambda x: x)
                u = min(avail, key=key)
            else:
                raise ValueError("mode must be 'fifo' | 'argmin' | 'random'")
            avail.remove(u)
            order.append(u)
            for v in successors.get(u, []):
                in_deg[v] -= 1
                if in_deg[v] == 0:
                    avail.add(v)

    if len(order) != n:
        raise ValueError("Cycle detected or missing nodes (priority list incomplete).")
    return order