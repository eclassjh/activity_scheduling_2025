import numpy as np
import time
import random

from priority_algorithm import * # run_priority_algorithm() 참고


# Q table 생성 함수
def Qtable(state_space, action_space, bin_size = 30) :
    bins = [np.linspace(-4, 4, bin_size), np.linspace(-4, 4, bin_size)] # State
    q_table = np.random.uniform(low=-1, high=1,size=9[bin_size]* state_space + [action_space])
    
    return q_table, bins

# 이산화 함수
# Q table이 지나치게 방대해 지는 것을 막기 위한 단순화 작업
def Discrete(state, bins) :
    index = []
    for i in range(len(state)) : index.append(np.digitalize(state[i], bins[i] - 1))
    
    return tuple(index)


def Q_learning(q_table, bins, episodes=5000, gamma=0.95, lr=0.1, timestep=5000, epsilon=0.2) :
    reward=0
    data= {'score' : [0]}
    
    for episodes in range(1, episodes+1):
        # 초기값 설정
        current_state = Discrete([-58000, 4.11099952], bins)
        score = 0
        
        done=False
        
        temp_start = time.time()
        
        for index, next_stock in enumerate() :
            if not done :
                # 액션 선택
                # epsilon-greedy 정책에 따라 어느 정도 확률로 무작위 액션 시행
                if np.random.uniform(0, 1) < epsilon :
                    action = random.choice([0, 1, 2])
                else :
                    action = np.argmax(q_table[current_state])
                
                
                if action == 1 :
                    # 리워드 지급
                elif action == 2 :
                    # 리워드 지급
                else :
                    # 리워드 지급
                
                # 상태 설정
                next_state = Discrete([next_stock['tradePrice']-current_stock['tradePrice'], next_stock['candleAccTradeVolume']], bins)
                
                score += reward
                
                # 받은 reward를 감안한 Q value 업데이트
                
                max_future_q = np.max(q_table[next_state])
                current_q =  q_table[current_state + (action,)]
                new_q = (1-lr)*current_q + lr*(reward + gamma*max_future_q)
                q_table[current_state+(action,)] = new_q
                
            if epsilon%100 == 0 and epsilon > 0.001 :
                epsilon -= (epsilon*episode)/episodes