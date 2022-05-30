# 1. 일사량 이상치 검출 배경 및 목적   

## 1.1 배경   
* 인터뷰 진행 중 시간별 통계 테이블의 일사량 정보가 모든 발전소에서 정확하지 않음을 확인
* 발전량 예측 모델을 학습하기 위해 지역별 일사량의 정합성 확인 필요

## 1.2 목적   
* 시간별 통계 테이블을 조히하여 지역 발전소별 일사량 데이터의 정합성 조사
* 데이터 분포를 확인하여 이상치에 대한 전처리 진행 용이
* 가장 적은 이상치를 가진 발전소를 선택하여 지역 대표 발전소로 선택하기 위함


```python
# 공통 모듈

import pymysql
import numpy as np
import pandas as pd
from tqdm import tqdm
import matplotlib.pyplot as plt

#DB 연결
def select(sql):
    conn = pymysql.connect(host='dev-dp-db1-poc-1-instance.cq2k6z7cdszn.ap-northeast-2.rds.amazonaws.com',
                       port=33060,
                       user='root',
                       password='gksghk12!',
                       db='homdb',
                       charset='utf8',
                         cursorclass=pymysql.cursors.DictCursor)

    cursor = conn.cursor()

    cursor.execute(sql)
    return pd.DataFrame(cursor.fetchall())

#SELECT {columns}, {table_name}, {조건}
select_ = "SELECT {} FROM {} WHERE 1=1 {}"

#날짜, 시간 분리
def time_split(x, t_type):
    temp = str(x).split(" ")
    if t_type == "date":
        return temp[0]
    else:
        return int(temp[1].replace(":00:00", ""))

def print_solar_plot(pv_list):
    plt.figure(figsize=(16,9))
    for i in range(len(pv_list)):
        pv_tmp = pd.read_csv('dataset/pv_data/pv_'+ pv_list[i] +'.csv')
        plt.plot(pv_tmp[(pv_tmp.STATS_ITEM_CD == 'STS02')].tail(24*10).reset_index().STATS_VAL)
    plt.title('PV solar plot')
    plt.ylabel('Value')
    plt.xlabel('DATE')
    plt.legend(pv_list)
    plt.show() 
```

# 2. 데이터셋 조회   

## 2-1. 일사량 조회 테이블 및 조건   
*  Table: TB_~   
*  조건   
   - 시간별 일사량 조회 조건
   - SERVICE_STATUS : SS04 (HEIS)
   - BIZ_TY : BSN01
   - NATION_ID : KR
 
## 2-2. 지역별 구분 방식   
* from 시 ~ to 시 동안의 일사량이 check_val 이상 또는 이하인지 확인


```python
# 통계 data
df_join = select(select_.format("a.PV_ID, AREA_ID, NATION_ID, PV_KOR_NM, FCLTY_CPCTY, STATS_DT, STATS_VAL, DETL_ADDR",
                                "tb_pv_stdr_info a JOIN tb_tmcl_stats b on a.PV_ID = b.PV_ID", 
                                "AND STATS_ITEM_CD = 'STS02' AND usg_at = 'Y' AND service_sttus = 'SS04' AND biz_ty = 'BSN01' AND nation_id = 'KR'  ")) 

# 통계 backup data
df_back = select(select_.format("a.PV_ID, AREA_ID, NATION_ID, PV_KOR_NM, FCLTY_CPCTY, STATS_DT, STATS_VAL, DETL_ADDR",
                                "tb_pv_stdr_info a JOIN tb_tmcl_stats_backup_data b on a.PV_ID = b.PV_ID", 
                                "AND STATS_ITEM_CD = 'STS02' AND usg_at = 'Y' AND service_sttus = 'SS04' AND biz_ty = 'BSN01' AND nation_id = 'KR' ")) 

# 데이터 병합
df_new = pd.concat([df_back,df_join]).reset_index(drop = True)

# 시간데이터 변환
df_new['DATE'] = df_new.STATS_DT.map(lambda x : time_split(x, "date"))
df_new['TIME'] = df_new.STATS_DT.map(lambda x : time_split(x, "time"))

# 불필요한 컬럼 제거
df_new.drop(columns=['STATS_DT','NATION_ID'], inplace = True)
df_new.STATS_VAL = df_new.STATS_VAL.astype(float)

# 데이터 확인
df_new.head()
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>PV_ID</th>
      <th>AREA_ID</th>
      <th>PV_KOR_NM</th>
      <th>FCLTY_CPCTY</th>
      <th>STATS_VAL</th>
      <th>DETL_ADDR</th>
      <th>DATE</th>
      <th>TIME</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>AA003</td>
      <td>1832257</td>
      <td>㈜영월에너지스테이션 제2공구</td>
      <td>19060.1100</td>
      <td>-0.1670</td>
      <td>대한민국 강원도 영월군 남면 창원리 산2</td>
      <td>2019-12-01</td>
      <td>0</td>
    </tr>
    <tr>
      <th>1</th>
      <td>AA003</td>
      <td>1832257</td>
      <td>㈜영월에너지스테이션 제2공구</td>
      <td>19060.1100</td>
      <td>-0.4008</td>
      <td>대한민국 강원도 영월군 남면 창원리 산2</td>
      <td>2019-12-01</td>
      <td>1</td>
    </tr>
    <tr>
      <th>2</th>
      <td>AA003</td>
      <td>1832257</td>
      <td>㈜영월에너지스테이션 제2공구</td>
      <td>19060.1100</td>
      <td>-0.3841</td>
      <td>대한민국 강원도 영월군 남면 창원리 산2</td>
      <td>2019-12-01</td>
      <td>2</td>
    </tr>
    <tr>
      <th>3</th>
      <td>AA003</td>
      <td>1832257</td>
      <td>㈜영월에너지스테이션 제2공구</td>
      <td>19060.1100</td>
      <td>-0.8349</td>
      <td>대한민국 강원도 영월군 남면 창원리 산2</td>
      <td>2019-12-01</td>
      <td>3</td>
    </tr>
    <tr>
      <th>4</th>
      <td>AA003</td>
      <td>1832257</td>
      <td>㈜영월에너지스테이션 제2공구</td>
      <td>19060.1100</td>
      <td>-1.5015</td>
      <td>대한민국 강원도 영월군 남면 창원리 산2</td>
      <td>2019-12-01</td>
      <td>4</td>
    </tr>
  </tbody>
</table>
</div>




```python
# 지역별 발전소 수 및 일사량 데이터 수 (현재 데이터 + 백업 데이터)
area_list = {'전라남도':'jn', '전라북도':'jb','경상남도':'kn','경상북도':'kb','충청북도':'cb','대전광역':'dj','경기도':'kk','강원도':'kw'}
for key in list(area_list.keys()):
    pv = pd.DataFrame(df_new[df_new['DETL_ADDR'].str.contains(key)].PV_ID).drop_duplicates().reset_index(drop=True)
    df = df_new[df_new['DETL_ADDR'].str.contains(key)]
    print(key+"지역 발전소 개수 : ", pv.shape[0])
    print(key+"지역 시간별 일사량 총 데이터 개수 : ", df.shape[0])
    print("_______________________________________")
```

    전라남도지역 발전소 개수 :  20
    전라남도지역 시간별 일사량 총 데이터 개수 :  656743
    _______________________________________
    전라북도지역 발전소 개수 :  1
    전라북도지역 시간별 일사량 총 데이터 개수 :  35867
    _______________________________________
    경상남도지역 발전소 개수 :  3
    경상남도지역 시간별 일사량 총 데이터 개수 :  48891
    _______________________________________
    경상북도지역 발전소 개수 :  1
    경상북도지역 시간별 일사량 총 데이터 개수 :  40476
    _______________________________________
    충청북도지역 발전소 개수 :  2
    충청북도지역 시간별 일사량 총 데이터 개수 :  60368
    _______________________________________
    대전광역지역 발전소 개수 :  1
    대전광역지역 시간별 일사량 총 데이터 개수 :  40855
    _______________________________________
    경기도지역 발전소 개수 :  2
    경기도지역 시간별 일사량 총 데이터 개수 :  79606
    _______________________________________
    강원도지역 발전소 개수 :  3
    강원도지역 시간별 일사량 총 데이터 개수 :  79452
    _______________________________________


# 3. 이상치 검출 기준 및 방식   

## 3-1. 이상치 검출 기준   
*  인터뷰 내용   
   - 8~18시 이외에 발생한 일사량은 시스템 오류로 간주
   - 일사량 Boundary는 약 0~1000   
   
   
*  본 검출 과정에서 이상치 기준
   - 20시 ~ 05시는 20 이상
   - 08시 ~ 18시는 10 이하
   
## 3-2. 이상치 검출 방식   
*  이상치 검출 로직을 통해 검출
   - FROM (time) ~ TO (time) 간 일사량이 일정 기준 이상 또는 이하인지 확인


```python
# 시간별 이상 발전량 이상치 검출 함수 생성
def check_stats_val(from_time, to_time, check_val, types, df):
    # 총 건수
    total_count = 0 
    count = 0
    # param 시간 분배하여 check_time 생성
    if from_time > to_time :
        check_time = [i for i in range(from_time, 24)]
        check_time += [i for i in range(0, to_time+1)]
    else :
        check_time = [i for i in range(from_time, to_time+1)]
    
    print("시간 :", check_time)
    
    df_sum = pd.DataFrame()
    # 비교연산자에 따라 건수 print
    for time in check_time :
        _df = df.copy()
        _df = df[df.TIME == time]
        abnormal = _df[(_df.STATS_VAL > 1200) | (_df.STATS_VAL < -5)]
        normal = _df[(_df.STATS_VAL < 1200 ) & (_df.STATS_VAL > -5)] 
        
        if types == '>' :
            ab_tmp = normal[normal.STATS_VAL > check_val]
        elif types == '<' : 
            ab_tmp = normal[normal.STATS_VAL < check_val]
        
        total_count += abnormal.shape[0]
        total_count += ab_tmp.shape[0]
        
        print(time , "시 기준 이상치 : ", ab_tmp.shape[0] , ", Boundary 이상치 : " , abnormal.shape[0])
        
        df_sum = pd.concat([df_sum, abnormal])
        df_sum = pd.concat([df_sum, ab_tmp])
    
    #총 건수 print
    print("======총 ",total_count, "건 ======")
    
    return total_count, df_sum.sort_values(by=['DATE', 'TIME'], axis=0)
```

# 4. 이상치 검출 수행
    - Control+F로 발전소 명 혹은 지역명으로 검색하여 확인
    
## 4-1. 전라남도 지역 이상치 검출 수행


```python
# 전라남도 발전소 시간별 일사량 데이터
df_jn = df_new[df_new['DETL_ADDR'].str.contains('전라남도')]

# 전라남도 발전소 리스트 확인
df_jn.drop_duplicates(subset=['PV_ID']).reset_index(drop=True).drop(columns=['STATS_VAL', 'DATE','TIME'])
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>PV_ID</th>
      <th>AREA_ID</th>
      <th>PV_KOR_NM</th>
      <th>FCLTY_CPCTY</th>
      <th>DETL_ADDR</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>AE017</td>
      <td>1844751</td>
      <td>송지1호 태양광발전소</td>
      <td>1749.6000</td>
      <td>대한민국 전라남도 해남군 송지면 가차리 253-9</td>
    </tr>
    <tr>
      <th>1</th>
      <td>AE018</td>
      <td>1844751</td>
      <td>송지2호 태양광발전소</td>
      <td>1749.6000</td>
      <td>대한민국 전라남도 해남군 송지면 가차리 336-2</td>
    </tr>
    <tr>
      <th>2</th>
      <td>AE019</td>
      <td>1844751</td>
      <td>영지 태양광발전소</td>
      <td>1749.6000</td>
      <td>대한민국 전라남도 해남군 송지면 가차리 253-13</td>
    </tr>
    <tr>
      <th>3</th>
      <td>AI004</td>
      <td>1842859</td>
      <td>원덕폐도로 태양광발전소</td>
      <td>877.8000</td>
      <td>대한민국 전라남도 장성군 북이면 원덕리 808-2</td>
    </tr>
    <tr>
      <th>4</th>
      <td>AI005</td>
      <td>1842859</td>
      <td>도시개발폐도로 태양광발전소</td>
      <td>579.1200</td>
      <td>대한민국 전라남도 장성군 북이면 원덕리 69-2</td>
    </tr>
    <tr>
      <th>5</th>
      <td>AI009</td>
      <td>1842859</td>
      <td>신월폐도로</td>
      <td>974.7000</td>
      <td>대한민국 전라남도 장성군 북이면 신월리 426-2</td>
    </tr>
    <tr>
      <th>6</th>
      <td>AI027</td>
      <td>1832157</td>
      <td>삼성03호 태양광발전소</td>
      <td>997.9200</td>
      <td>대한민국 전라남도 고흥군 도덕면 신양리 2406-4</td>
    </tr>
    <tr>
      <th>7</th>
      <td>AI028</td>
      <td>1832157</td>
      <td>삼성01호 태양광발전소</td>
      <td>997.9200</td>
      <td>대한민국 전라남도 고흥군 도덕면 신양리 2406</td>
    </tr>
    <tr>
      <th>8</th>
      <td>AI029</td>
      <td>1832157</td>
      <td>삼성02호 태양광발전소</td>
      <td>997.9200</td>
      <td>대한민국 전라남도 고흥군 도덕면 신양리 2406-3</td>
    </tr>
    <tr>
      <th>9</th>
      <td>AI030</td>
      <td>1832157</td>
      <td>삼성04호 태양광발전소</td>
      <td>972.3600</td>
      <td>대한민국 전라남도 고흥군 도덕면 신양리 2406</td>
    </tr>
    <tr>
      <th>10</th>
      <td>AI031</td>
      <td>1832157</td>
      <td>삼성05호 태양광발전소</td>
      <td>972.3600</td>
      <td>대한민국 전라남도 고흥군 도덕면 신양리 2406</td>
    </tr>
    <tr>
      <th>11</th>
      <td>AI032</td>
      <td>1832157</td>
      <td>삼성06호 태양광발전소</td>
      <td>998.6400</td>
      <td>대한민국 전라남도 고흥군 도덕면 신양리 2406-2</td>
    </tr>
    <tr>
      <th>12</th>
      <td>AI036</td>
      <td>1832157</td>
      <td>삼성11호 태양광발전소</td>
      <td>905.6000</td>
      <td>대한민국 전라남도 고흥군 두원면 학곡리 산250-3</td>
    </tr>
    <tr>
      <th>13</th>
      <td>AM009</td>
      <td>1832157</td>
      <td>도덕2호 태양광발전소</td>
      <td>498.9600</td>
      <td>대한민국 전라남도 고흥군 도덕면 용동리 산178</td>
    </tr>
    <tr>
      <th>14</th>
      <td>AM011</td>
      <td>1832157</td>
      <td>도덕3호 태양광발전소</td>
      <td>498.9600</td>
      <td>대한민국 전라남도 고흥군 도덕면 용동리 산178</td>
    </tr>
    <tr>
      <th>15</th>
      <td>AM012</td>
      <td>1832157</td>
      <td>삼성08A 태양광발전소</td>
      <td>453.6000</td>
      <td>대한민국 전라남도 고흥군 두원면 학곡리 1008</td>
    </tr>
    <tr>
      <th>16</th>
      <td>AM013</td>
      <td>1832157</td>
      <td>삼성09B 태양광발전소</td>
      <td>492.5000</td>
      <td>대한민국 전라남도 고흥군 두원면 학곡리 1000</td>
    </tr>
    <tr>
      <th>17</th>
      <td>AM014</td>
      <td>1832157</td>
      <td>삼성09A 태양광발전소</td>
      <td>492.5000</td>
      <td>대한민국 전라남도 고흥군 두원면 학곡리 1015</td>
    </tr>
    <tr>
      <th>18</th>
      <td>AM015</td>
      <td>1832157</td>
      <td>도덕1호 태양광발전소</td>
      <td>492.8000</td>
      <td>대한민국 전라남도 고흥군 도덕면 용동리 산178</td>
    </tr>
    <tr>
      <th>19</th>
      <td>AM016</td>
      <td>1832157</td>
      <td>삼성08B 태양광발전소</td>
      <td>466.4700</td>
      <td>대한민국 전라남도 고흥군 두원면 학곡리 1008</td>
    </tr>
  </tbody>
</table>
</div>



### AE017 / 송지1호 태양광발전소	


```python
pv_id = 'AE017'

# 해당 발전소 데이터 추출
df_tmp = df_jn[df_jn.PV_ID == pv_id]
df = df_tmp.copy()
df.drop(columns=['DETL_ADDR'], inplace = True)

# 발전소 데이터 요약정보 확인
print(df.STATS_VAL.describe())
print()

# 20시 부터 5시까지 일사량이 20 이상인 데이터 수
print("-------밤시간 이상치 확인---------")
night, df_night = check_stats_val(20, 5, 20, '>', df)
print()

# 6시부터 18시까지 일사량이 10 이하인 데이터 수
print("-------낮시간 이상치 확인---------")
daytime, df_day = check_stats_val(8, 17, 10, '<', df)
print()

# 이상치 검출율
print("-------이상치 검출---------")
print("총 데이터 :", df.shape[0], " 이상치 : ", night+daytime)
print("이상치 검출율 : ", ((night+daytime) / df.shape[0])*100, "%" )
print("낮 기준 이상치 : ", (daytime/ df.shape[0])*100, "%")
print("밤 기준 이상치 : ", (night/ df.shape[0])*100, "%")

# 이상치로 검출된 데이터 저장
df_sum = pd.concat([df_day, df_night]).sort_values(by=['DATE', 'TIME'], axis=0)
df_sum.to_csv('dataset/abnormal/' + pv_id + '_abnormal.csv', index=False, encoding="utf-8-sig")
```

    count    35757.000000
    mean       147.329527
    std        252.694193
    min          0.000000
    25%          0.000000
    50%          0.918500
    75%        191.949800
    max        998.916800
    Name: STATS_VAL, dtype: float64
    
    -------밤시간 이상치 확인---------
    시간 : [20, 21, 22, 23, 0, 1, 2, 3, 4, 5]
    20 시 기준 이상치 :  0 , Boundary 이상치 :  0
    21 시 기준 이상치 :  0 , Boundary 이상치 :  0
    22 시 기준 이상치 :  0 , Boundary 이상치 :  0
    23 시 기준 이상치 :  0 , Boundary 이상치 :  0
    0 시 기준 이상치 :  0 , Boundary 이상치 :  0
    1 시 기준 이상치 :  0 , Boundary 이상치 :  0
    2 시 기준 이상치 :  0 , Boundary 이상치 :  0
    3 시 기준 이상치 :  0 , Boundary 이상치 :  0
    4 시 기준 이상치 :  0 , Boundary 이상치 :  0
    5 시 기준 이상치 :  0 , Boundary 이상치 :  0
    ======총  0 건 ======
    
    -------낮시간 이상치 확인---------
    시간 : [8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
    8 시 기준 이상치 :  261 , Boundary 이상치 :  0
    9 시 기준 이상치 :  249 , Boundary 이상치 :  0
    10 시 기준 이상치 :  252 , Boundary 이상치 :  0
    11 시 기준 이상치 :  250 , Boundary 이상치 :  0
    12 시 기준 이상치 :  251 , Boundary 이상치 :  0
    13 시 기준 이상치 :  250 , Boundary 이상치 :  0
    14 시 기준 이상치 :  251 , Boundary 이상치 :  0
    15 시 기준 이상치 :  254 , Boundary 이상치 :  0
    16 시 기준 이상치 :  259 , Boundary 이상치 :  0
    17 시 기준 이상치 :  413 , Boundary 이상치 :  0
    ======총  2690 건 ======
    
    -------이상치 검출---------
    총 데이터 : 35757  이상치 :  2690
    이상치 검출율 :  7.523002489023129 %
    낮 기준 이상치 :  7.523002489023129 %
    밤 기준 이상치 :  0.0 %


### AE018	/ 송지2호 태양광발전소


```python
pv_id = 'AE018'

# 해당 발전소 데이터 추출
df_tmp = df_jn[df_jn.PV_ID == pv_id]
df = df_tmp.copy()
df.drop(columns=['DETL_ADDR'], inplace = True)

# 발전소 데이터 요약정보 확인
print(df.STATS_VAL.describe())
print()

# 20시 부터 5시까지 일사량이 20 이상인 데이터 수
print("-------밤시간 이상치 확인---------")
night, df_night = check_stats_val(20, 5, 20, '>', df)
print()

# 6시부터 18시까지 일사량이 10 이하인 데이터 수
print("-------낮시간 이상치 확인---------")
daytime, df_day = check_stats_val(8, 17, 10, '<', df)
print()

# 이상치 검출율
print("-------이상치 검출---------")
print("총 데이터 :", df.shape[0], " 이상치 : ", night+daytime)
print("이상치 검출율 : ", ((night+daytime) / df.shape[0])*100, "%" )
print("낮 기준 이상치 : ", (daytime/ df.shape[0])*100, "%")
print("밤 기준 이상치 : ", (night/ df.shape[0])*100, "%")

# 이상치로 검출된 데이터 저장
df_sum = pd.concat([df_day, df_night]).sort_values(by=['DATE', 'TIME'], axis=0)
df_sum.to_csv('dataset/abnormal/' + pv_id + '_abnormal.csv', index=False, encoding="utf-8-sig")
```

    count    35757.000000
    mean       146.909836
    std        251.974583
    min          0.000000
    25%          0.000000
    50%          0.918500
    75%        191.399600
    max        998.916800
    Name: STATS_VAL, dtype: float64
    
    -------밤시간 이상치 확인---------
    시간 : [20, 21, 22, 23, 0, 1, 2, 3, 4, 5]
    20 시 기준 이상치 :  0 , Boundary 이상치 :  0
    21 시 기준 이상치 :  0 , Boundary 이상치 :  0
    22 시 기준 이상치 :  0 , Boundary 이상치 :  0
    23 시 기준 이상치 :  0 , Boundary 이상치 :  0
    0 시 기준 이상치 :  0 , Boundary 이상치 :  0
    1 시 기준 이상치 :  0 , Boundary 이상치 :  0
    2 시 기준 이상치 :  0 , Boundary 이상치 :  0
    3 시 기준 이상치 :  0 , Boundary 이상치 :  0
    4 시 기준 이상치 :  0 , Boundary 이상치 :  0
    5 시 기준 이상치 :  0 , Boundary 이상치 :  0
    ======총  0 건 ======
    
    -------낮시간 이상치 확인---------
    시간 : [8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
    8 시 기준 이상치 :  261 , Boundary 이상치 :  0
    9 시 기준 이상치 :  249 , Boundary 이상치 :  0
    10 시 기준 이상치 :  252 , Boundary 이상치 :  0
    11 시 기준 이상치 :  251 , Boundary 이상치 :  0
    12 시 기준 이상치 :  251 , Boundary 이상치 :  0
    13 시 기준 이상치 :  250 , Boundary 이상치 :  0
    14 시 기준 이상치 :  251 , Boundary 이상치 :  0
    15 시 기준 이상치 :  254 , Boundary 이상치 :  0
    16 시 기준 이상치 :  259 , Boundary 이상치 :  0
    17 시 기준 이상치 :  413 , Boundary 이상치 :  0
    ======총  2691 건 ======
    
    -------이상치 검출---------
    총 데이터 : 35757  이상치 :  2691
    이상치 검출율 :  7.525799144223509 %
    낮 기준 이상치 :  7.525799144223509 %
    밤 기준 이상치 :  0.0 %


### AE019	/ 영지 태양광발전소


```python
pv_id = 'AE019'

# 해당 발전소 데이터 추출
df_tmp = df_jn[df_jn.PV_ID == pv_id]
df = df_tmp.copy()
df.drop(columns=['DETL_ADDR'], inplace = True)

# 발전소 데이터 요약정보 확인
print(df.STATS_VAL.describe())
print()

# 20시 부터 5시까지 일사량이 20 이상인 데이터 수
print("-------밤시간 이상치 확인---------")
night, df_night = check_stats_val(20, 5, 20, '>', df)
print()

# 6시부터 18시까지 일사량이 10 이하인 데이터 수
print("-------낮시간 이상치 확인---------")
daytime, df_day = check_stats_val(8, 17, 10, '<', df)
print()

# 이상치 검출율
print("-------이상치 검출---------")
print("총 데이터 :", df.shape[0], " 이상치 : ", night+daytime)
print("이상치 검출율 : ", ((night+daytime) / df.shape[0])*100, "%" )
print("낮 기준 이상치 : ", (daytime/ df.shape[0])*100, "%")
print("밤 기준 이상치 : ", (night/ df.shape[0])*100, "%")

# 이상치로 검출된 데이터 저장
df_sum = pd.concat([df_day, df_night]).sort_values(by=['DATE', 'TIME'], axis=0)
df_sum.to_csv('dataset/abnormal/' + pv_id + '_abnormal.csv', index=False, encoding="utf-8-sig")
```

    count    37166.000000
    mean       176.498223
    std        265.866108
    min          0.000000
    25%          0.000000
    50%          6.908600
    75%        286.912375
    max       1029.682900
    Name: STATS_VAL, dtype: float64
    
    -------밤시간 이상치 확인---------
    시간 : [20, 21, 22, 23, 0, 1, 2, 3, 4, 5]
    20 시 기준 이상치 :  0 , Boundary 이상치 :  0
    21 시 기준 이상치 :  0 , Boundary 이상치 :  0
    22 시 기준 이상치 :  0 , Boundary 이상치 :  0
    23 시 기준 이상치 :  0 , Boundary 이상치 :  0
    0 시 기준 이상치 :  0 , Boundary 이상치 :  0
    1 시 기준 이상치 :  0 , Boundary 이상치 :  0
    2 시 기준 이상치 :  0 , Boundary 이상치 :  0
    3 시 기준 이상치 :  0 , Boundary 이상치 :  0
    4 시 기준 이상치 :  0 , Boundary 이상치 :  0
    5 시 기준 이상치 :  0 , Boundary 이상치 :  0
    ======총  0 건 ======
    
    -------낮시간 이상치 확인---------
    시간 : [8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
    8 시 기준 이상치 :  16 , Boundary 이상치 :  0
    9 시 기준 이상치 :  4 , Boundary 이상치 :  0
    10 시 기준 이상치 :  2 , Boundary 이상치 :  0
    11 시 기준 이상치 :  2 , Boundary 이상치 :  0
    12 시 기준 이상치 :  1 , Boundary 이상치 :  0
    13 시 기준 이상치 :  0 , Boundary 이상치 :  0
    14 시 기준 이상치 :  1 , Boundary 이상치 :  0
    15 시 기준 이상치 :  2 , Boundary 이상치 :  0
    16 시 기준 이상치 :  7 , Boundary 이상치 :  0
    17 시 기준 이상치 :  217 , Boundary 이상치 :  0
    ======총  252 건 ======
    
    -------이상치 검출---------
    총 데이터 : 37166  이상치 :  252
    이상치 검출율 :  0.6780390679653447 %
    낮 기준 이상치 :  0.6780390679653447 %
    밤 기준 이상치 :  0.0 %


### AI004	/ 원덕폐도로 태양광발전소


```python
pv_id = 'AI004'

# 해당 발전소 데이터 추출
df_tmp = df_jn[df_jn.PV_ID == pv_id]
df = df_tmp.copy()
df.drop(columns=['DETL_ADDR'], inplace = True)

# 발전소 데이터 요약정보 확인
print(df.STATS_VAL.describe())
print()

# 20시 부터 5시까지 일사량이 20 이상인 데이터 수
print("-------밤시간 이상치 확인---------")
night, df_night = check_stats_val(20, 5, 20, '>', df)
print()

# 6시부터 18시까지 일사량이 10 이하인 데이터 수
print("-------낮시간 이상치 확인---------")
daytime, df_day = check_stats_val(8, 17, 10, '<', df)
print()

# 이상치 검출율
print("-------이상치 검출---------")
print("총 데이터 :", df.shape[0], " 이상치 : ", night+daytime)
print("이상치 검출율 : ", ((night+daytime) / df.shape[0])*100, "%" )
print("낮 기준 이상치 : ", (daytime/ df.shape[0])*100, "%")
print("밤 기준 이상치 : ", (night/ df.shape[0])*100, "%")

# 이상치로 검출된 데이터 저장
df_sum = pd.concat([df_day, df_night]).sort_values(by=['DATE', 'TIME'], axis=0)
df_sum.to_csv('dataset/abnormal/' + pv_id + '_abnormal.csv', index=False, encoding="utf-8-sig")
```

    count    38382.000000
    mean       151.690375
    std        254.385583
    min          0.000000
    25%          0.000000
    50%          0.000000
    75%        203.683750
    max       1028.628100
    Name: STATS_VAL, dtype: float64
    
    -------밤시간 이상치 확인---------
    시간 : [20, 21, 22, 23, 0, 1, 2, 3, 4, 5]
    20 시 기준 이상치 :  0 , Boundary 이상치 :  0
    21 시 기준 이상치 :  0 , Boundary 이상치 :  0
    22 시 기준 이상치 :  0 , Boundary 이상치 :  0
    23 시 기준 이상치 :  0 , Boundary 이상치 :  0
    0 시 기준 이상치 :  0 , Boundary 이상치 :  0
    1 시 기준 이상치 :  0 , Boundary 이상치 :  0
    2 시 기준 이상치 :  0 , Boundary 이상치 :  0
    3 시 기준 이상치 :  0 , Boundary 이상치 :  0
    4 시 기준 이상치 :  0 , Boundary 이상치 :  0
    5 시 기준 이상치 :  0 , Boundary 이상치 :  0
    ======총  0 건 ======
    
    -------낮시간 이상치 확인---------
    시간 : [8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
    8 시 기준 이상치 :  170 , Boundary 이상치 :  0
    9 시 기준 이상치 :  130 , Boundary 이상치 :  0
    10 시 기준 이상치 :  124 , Boundary 이상치 :  0
    11 시 기준 이상치 :  123 , Boundary 이상치 :  0
    12 시 기준 이상치 :  121 , Boundary 이상치 :  0
    13 시 기준 이상치 :  123 , Boundary 이상치 :  0
    14 시 기준 이상치 :  124 , Boundary 이상치 :  0
    15 시 기준 이상치 :  129 , Boundary 이상치 :  0
    16 시 기준 이상치 :  153 , Boundary 이상치 :  0
    17 시 기준 이상치 :  537 , Boundary 이상치 :  0
    ======총  1734 건 ======
    
    -------이상치 검출---------
    총 데이터 : 38382  이상치 :  1734
    이상치 검출율 :  4.517742691886822 %
    낮 기준 이상치 :  4.517742691886822 %
    밤 기준 이상치 :  0.0 %


### AI005	/ 도시개발폐도로 태양광발전소


```python
pv_id = 'AI005'

# 해당 발전소 데이터 추출
df_tmp = df_jn[df_jn.PV_ID == pv_id]
df = df_tmp.copy()
df.drop(columns=['DETL_ADDR'], inplace = True)

# 발전소 데이터 요약정보 확인
print(df.STATS_VAL.describe())
print()

# 20시 부터 5시까지 일사량이 20 이상인 데이터 수
print("-------밤시간 이상치 확인---------")
night, df_night = check_stats_val(20, 5, 20, '>', df)
print()

# 6시부터 18시까지 일사량이 10 이하인 데이터 수
print("-------낮시간 이상치 확인---------")
daytime, df_day = check_stats_val(8, 17, 10, '<', df)
print()

# 이상치 검출율
print("-------이상치 검출---------")
print("총 데이터 :", df.shape[0], " 이상치 : ", night+daytime)
print("이상치 검출율 : ", ((night+daytime) / df.shape[0])*100, "%" )
print("낮 기준 이상치 : ", (daytime/ df.shape[0])*100, "%")
print("밤 기준 이상치 : ", (night/ df.shape[0])*100, "%")

# 이상치로 검출된 데이터 저장
df_sum = pd.concat([df_day, df_night]).sort_values(by=['DATE', 'TIME'], axis=0)
df_sum.to_csv('dataset/abnormal/' + pv_id + '_abnormal.csv', index=False, encoding="utf-8-sig")
```

    count    40552.000000
    mean      1300.888607
    std        688.131857
    min          0.000000
    25%       1083.491450
    50%       1691.668600
    75%       1750.002000
    max       1750.002000
    Name: STATS_VAL, dtype: float64
    
    -------밤시간 이상치 확인---------
    시간 : [20, 21, 22, 23, 0, 1, 2, 3, 4, 5]
    20 시 기준 이상치 :  103 , Boundary 이상치 :  1280
    21 시 기준 이상치 :  111 , Boundary 이상치 :  1264
    22 시 기준 이상치 :  115 , Boundary 이상치 :  1252
    23 시 기준 이상치 :  122 , Boundary 이상치 :  1245
    0 시 기준 이상치 :  124 , Boundary 이상치 :  1227
    1 시 기준 이상치 :  125 , Boundary 이상치 :  1216
    2 시 기준 이상치 :  136 , Boundary 이상치 :  1210
    3 시 기준 이상치 :  136 , Boundary 이상치 :  1202
    4 시 기준 이상치 :  148 , Boundary 이상치 :  1197
    5 시 기준 이상치 :  149 , Boundary 이상치 :  1189
    ======총  13551 건 ======
    
    -------낮시간 이상치 확인---------
    시간 : [8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
    8 시 기준 이상치 :  289 , Boundary 이상치 :  1188
    9 시 기준 이상치 :  278 , Boundary 이상치 :  1211
    10 시 기준 이상치 :  274 , Boundary 이상치 :  1259
    11 시 기준 이상치 :  260 , Boundary 이상치 :  1288
    12 시 기준 이상치 :  254 , Boundary 이상치 :  1293
    13 시 기준 이상치 :  251 , Boundary 이상치 :  1301
    14 시 기준 이상치 :  255 , Boundary 이상치 :  1297
    15 시 기준 이상치 :  251 , Boundary 이상치 :  1294
    16 시 기준 이상치 :  252 , Boundary 이상치 :  1294
    17 시 기준 이상치 :  257 , Boundary 이상치 :  1295
    ======총  15341 건 ======
    
    -------이상치 검출---------
    총 데이터 : 40552  이상치 :  28892
    이상치 검출율 :  71.24679423949497 %
    낮 기준 이상치 :  37.83043992898008 %
    밤 기준 이상치 :  33.4163543105149 %


### AI009	/ 신월폐도로


```python
pv_id = 'AI009'

# 해당 발전소 데이터 추출
df_tmp = df_jn[df_jn.PV_ID == pv_id]
df = df_tmp.copy()
df.drop(columns=['DETL_ADDR'], inplace = True)

# 발전소 데이터 요약정보 확인
print(df.STATS_VAL.describe())
print()

# 20시 부터 5시까지 일사량이 20 이상인 데이터 수
print("-------밤시간 이상치 확인---------")
night, df_night = check_stats_val(20, 5, 20, '>', df)
print()

# 6시부터 18시까지 일사량이 10 이하인 데이터 수
print("-------낮시간 이상치 확인---------")
daytime, df_day = check_stats_val(8, 17, 10, '<', df)
print()

# 이상치 검출율
print("-------이상치 검출---------")
print("총 데이터 :", df.shape[0], " 이상치 : ", night+daytime)
print("이상치 검출율 : ", ((night+daytime) / df.shape[0])*100, "%" )
print("낮 기준 이상치 : ", (daytime/ df.shape[0])*100, "%")
print("밤 기준 이상치 : ", (night/ df.shape[0])*100, "%")

# 이상치로 검출된 데이터 저장
df_sum = pd.concat([df_day, df_night]).sort_values(by=['DATE', 'TIME'], axis=0)
df_sum.to_csv('dataset/abnormal/' + pv_id + '_abnormal.csv', index=False, encoding="utf-8-sig")
```

    count    37852.000000
    mean       156.154868
    std        247.722806
    min          0.000000
    25%          0.000000
    50%          3.281450
    75%        241.099000
    max       1750.002000
    Name: STATS_VAL, dtype: float64
    
    -------밤시간 이상치 확인---------
    시간 : [20, 21, 22, 23, 0, 1, 2, 3, 4, 5]
    20 시 기준 이상치 :  0 , Boundary 이상치 :  1
    21 시 기준 이상치 :  0 , Boundary 이상치 :  1
    22 시 기준 이상치 :  0 , Boundary 이상치 :  1
    23 시 기준 이상치 :  0 , Boundary 이상치 :  1
    0 시 기준 이상치 :  0 , Boundary 이상치 :  1
    1 시 기준 이상치 :  0 , Boundary 이상치 :  1
    2 시 기준 이상치 :  0 , Boundary 이상치 :  1
    3 시 기준 이상치 :  0 , Boundary 이상치 :  1
    4 시 기준 이상치 :  0 , Boundary 이상치 :  1
    5 시 기준 이상치 :  1 , Boundary 이상치 :  0
    ======총  10 건 ======
    
    -------낮시간 이상치 확인---------
    시간 : [8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
    8 시 기준 이상치 :  48 , Boundary 이상치 :  2
    9 시 기준 이상치 :  9 , Boundary 이상치 :  2
    10 시 기준 이상치 :  2 , Boundary 이상치 :  0
    11 시 기준 이상치 :  1 , Boundary 이상치 :  2
    12 시 기준 이상치 :  1 , Boundary 이상치 :  2
    13 시 기준 이상치 :  4 , Boundary 이상치 :  0
    14 시 기준 이상치 :  4 , Boundary 이상치 :  1
    15 시 기준 이상치 :  7 , Boundary 이상치 :  0
    16 시 기준 이상치 :  18 , Boundary 이상치 :  0
    17 시 기준 이상치 :  427 , Boundary 이상치 :  1
    ======총  531 건 ======
    
    -------이상치 검출---------
    총 데이터 : 37852  이상치 :  541
    이상치 검출율 :  1.4292507661418155 %
    낮 기준 이상치 :  1.4028320828489906 %
    밤 기준 이상치 :  0.026418683292824686 %


### AI027	/ 삼성03호 태양광발전소


```python
pv_id = 'AI027'

# 해당 발전소 데이터 추출
df_tmp = df_jn[df_jn.PV_ID == pv_id]
df = df_tmp.copy()
df.drop(columns=['DETL_ADDR'], inplace = True)

# 발전소 데이터 요약정보 확인
print(df.STATS_VAL.describe())
print()

# 20시 부터 5시까지 일사량이 20 이상인 데이터 수
print("-------밤시간 이상치 확인---------")
night, df_night = check_stats_val(20, 5, 20, '>', df)
print()

# 6시부터 18시까지 일사량이 10 이하인 데이터 수
print("-------낮시간 이상치 확인---------")
daytime, df_day = check_stats_val(8, 17, 10, '<', df)
print()

# 이상치 검출율
print("-------이상치 검출---------")
print("총 데이터 :", df.shape[0], " 이상치 : ", night+daytime)
print("이상치 검출율 : ", ((night+daytime) / df.shape[0])*100, "%" )
print("낮 기준 이상치 : ", (daytime/ df.shape[0])*100, "%")
print("밤 기준 이상치 : ", (night/ df.shape[0])*100, "%")

# 이상치로 검출된 데이터 저장
df_sum = pd.concat([df_day, df_night]).sort_values(by=['DATE', 'TIME'], axis=0)
df_sum.to_csv('dataset/abnormal/' + pv_id + '_abnormal.csv', index=False, encoding="utf-8-sig")
```

    count    31888.000000
    mean       175.779725
    std        260.455604
    min          0.000000
    25%          0.000000
    50%          5.625250
    75%        297.254425
    max       1029.350100
    Name: STATS_VAL, dtype: float64
    
    -------밤시간 이상치 확인---------
    시간 : [20, 21, 22, 23, 0, 1, 2, 3, 4, 5]
    20 시 기준 이상치 :  0 , Boundary 이상치 :  0
    21 시 기준 이상치 :  0 , Boundary 이상치 :  0
    22 시 기준 이상치 :  0 , Boundary 이상치 :  0
    23 시 기준 이상치 :  0 , Boundary 이상치 :  0
    0 시 기준 이상치 :  0 , Boundary 이상치 :  0
    1 시 기준 이상치 :  0 , Boundary 이상치 :  0
    2 시 기준 이상치 :  0 , Boundary 이상치 :  0
    3 시 기준 이상치 :  0 , Boundary 이상치 :  0
    4 시 기준 이상치 :  0 , Boundary 이상치 :  0
    5 시 기준 이상치 :  4 , Boundary 이상치 :  0
    ======총  4 건 ======
    
    -------낮시간 이상치 확인---------
    시간 : [8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
    8 시 기준 이상치 :  14 , Boundary 이상치 :  0
    9 시 기준 이상치 :  6 , Boundary 이상치 :  0
    10 시 기준 이상치 :  0 , Boundary 이상치 :  0
    11 시 기준 이상치 :  3 , Boundary 이상치 :  0
    12 시 기준 이상치 :  2 , Boundary 이상치 :  0
    13 시 기준 이상치 :  2 , Boundary 이상치 :  0
    14 시 기준 이상치 :  1 , Boundary 이상치 :  0
    15 시 기준 이상치 :  4 , Boundary 이상치 :  0
    16 시 기준 이상치 :  11 , Boundary 이상치 :  0
    17 시 기준 이상치 :  260 , Boundary 이상치 :  0
    ======총  303 건 ======
    
    -------이상치 검출---------
    총 데이터 : 31888  이상치 :  307
    이상치 검출율 :  0.962744606121425 %
    낮 기준 이상치 :  0.9502007024586052 %
    밤 기준 이상치 :  0.012543903662819869 %


### AI028	/ 삼성01호 태양광발전소


```python
pv_id = 'AI028'

# 해당 발전소 데이터 추출
df_tmp = df_jn[df_jn.PV_ID == pv_id]
df = df_tmp.copy()
df.drop(columns=['DETL_ADDR'], inplace = True)

# 발전소 데이터 요약정보 확인
print(df.STATS_VAL.describe())
print()

# 20시 부터 5시까지 일사량이 20 이상인 데이터 수
print("-------밤시간 이상치 확인---------")
night, df_night = check_stats_val(20, 5, 20, '>', df)
print()

# 6시부터 18시까지 일사량이 10 이하인 데이터 수
print("-------낮시간 이상치 확인---------")
daytime, df_day = check_stats_val(8, 17, 10, '<', df)
print()

# 이상치 검출율
print("-------이상치 검출---------")
print("총 데이터 :", df.shape[0], " 이상치 : ", night+daytime)
print("이상치 검출율 : ", ((night+daytime) / df.shape[0])*100, "%" )
print("낮 기준 이상치 : ", (daytime/ df.shape[0])*100, "%")
print("밤 기준 이상치 : ", (night/ df.shape[0])*100, "%")

# 이상치로 검출된 데이터 저장
df_sum = pd.concat([df_day, df_night]).sort_values(by=['DATE', 'TIME'], axis=0)
df_sum.to_csv('dataset/abnormal/' + pv_id + '_abnormal.csv', index=False, encoding="utf-8-sig")
```

    count    31887.000000
    mean       175.777358
    std        260.456291
    min          0.000000
    25%          0.000000
    50%          5.633500
    75%        297.350050
    max       1029.350100
    Name: STATS_VAL, dtype: float64
    
    -------밤시간 이상치 확인---------
    시간 : [20, 21, 22, 23, 0, 1, 2, 3, 4, 5]
    20 시 기준 이상치 :  0 , Boundary 이상치 :  0
    21 시 기준 이상치 :  0 , Boundary 이상치 :  0
    22 시 기준 이상치 :  0 , Boundary 이상치 :  0
    23 시 기준 이상치 :  0 , Boundary 이상치 :  0
    0 시 기준 이상치 :  0 , Boundary 이상치 :  0
    1 시 기준 이상치 :  0 , Boundary 이상치 :  0
    2 시 기준 이상치 :  0 , Boundary 이상치 :  0
    3 시 기준 이상치 :  0 , Boundary 이상치 :  0
    4 시 기준 이상치 :  0 , Boundary 이상치 :  0
    5 시 기준 이상치 :  4 , Boundary 이상치 :  0
    ======총  4 건 ======
    
    -------낮시간 이상치 확인---------
    시간 : [8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
    8 시 기준 이상치 :  14 , Boundary 이상치 :  0
    9 시 기준 이상치 :  6 , Boundary 이상치 :  0
    10 시 기준 이상치 :  0 , Boundary 이상치 :  0
    11 시 기준 이상치 :  3 , Boundary 이상치 :  0
    12 시 기준 이상치 :  2 , Boundary 이상치 :  0
    13 시 기준 이상치 :  2 , Boundary 이상치 :  0
    14 시 기준 이상치 :  1 , Boundary 이상치 :  0
    15 시 기준 이상치 :  4 , Boundary 이상치 :  0
    16 시 기준 이상치 :  11 , Boundary 이상치 :  0
    17 시 기준 이상치 :  260 , Boundary 이상치 :  0
    ======총  303 건 ======
    
    -------이상치 검출---------
    총 데이터 : 31887  이상치 :  307
    이상치 검출율 :  0.9627747985072287 %
    낮 기준 이상치 :  0.9502305014582746 %
    밤 기준 이상치 :  0.012544297048954118 %


### AI029	/ 삼성02호 태양광발전소


```python
pv_id = 'AI029'

# 해당 발전소 데이터 추출
df_tmp = df_jn[df_jn.PV_ID == pv_id]
df = df_tmp.copy()
df.drop(columns=['DETL_ADDR'], inplace = True)

# 발전소 데이터 요약정보 확인
print(df.STATS_VAL.describe())
print()

# 20시 부터 5시까지 일사량이 20 이상인 데이터 수
print("-------밤시간 이상치 확인---------")
night, df_night = check_stats_val(20, 5, 20, '>', df)
print()

# 6시부터 18시까지 일사량이 10 이하인 데이터 수
print("-------낮시간 이상치 확인---------")
daytime, df_day = check_stats_val(8, 17, 10, '<', df)
print()

# 이상치 검출율
print("-------이상치 검출---------")
print("총 데이터 :", df.shape[0], " 이상치 : ", night+daytime)
print("이상치 검출율 : ", ((night+daytime) / df.shape[0])*100, "%" )
print("낮 기준 이상치 : ", (daytime/ df.shape[0])*100, "%")
print("밤 기준 이상치 : ", (night/ df.shape[0])*100, "%")

# 이상치로 검출된 데이터 저장
df_sum = pd.concat([df_day, df_night]).sort_values(by=['DATE', 'TIME'], axis=0)
df_sum.to_csv('dataset/abnormal/' + pv_id + '_abnormal.csv', index=False, encoding="utf-8-sig")
```

    count    31875.000000
    mean       175.914936
    std        260.754396
    min          0.000000
    25%          0.000000
    50%          5.583300
    75%        297.474900
    max       1029.350100
    Name: STATS_VAL, dtype: float64
    
    -------밤시간 이상치 확인---------
    시간 : [20, 21, 22, 23, 0, 1, 2, 3, 4, 5]
    20 시 기준 이상치 :  0 , Boundary 이상치 :  0
    21 시 기준 이상치 :  0 , Boundary 이상치 :  0
    22 시 기준 이상치 :  0 , Boundary 이상치 :  0
    23 시 기준 이상치 :  0 , Boundary 이상치 :  0
    0 시 기준 이상치 :  0 , Boundary 이상치 :  0
    1 시 기준 이상치 :  0 , Boundary 이상치 :  0
    2 시 기준 이상치 :  0 , Boundary 이상치 :  0
    3 시 기준 이상치 :  0 , Boundary 이상치 :  0
    4 시 기준 이상치 :  0 , Boundary 이상치 :  0
    5 시 기준 이상치 :  4 , Boundary 이상치 :  0
    ======총  4 건 ======
    
    -------낮시간 이상치 확인---------
    시간 : [8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
    8 시 기준 이상치 :  14 , Boundary 이상치 :  0
    9 시 기준 이상치 :  6 , Boundary 이상치 :  0
    10 시 기준 이상치 :  0 , Boundary 이상치 :  0
    11 시 기준 이상치 :  3 , Boundary 이상치 :  0
    12 시 기준 이상치 :  2 , Boundary 이상치 :  0
    13 시 기준 이상치 :  2 , Boundary 이상치 :  0
    14 시 기준 이상치 :  1 , Boundary 이상치 :  0
    15 시 기준 이상치 :  4 , Boundary 이상치 :  0
    16 시 기준 이상치 :  11 , Boundary 이상치 :  0
    17 시 기준 이상치 :  259 , Boundary 이상치 :  0
    ======총  302 건 ======
    
    -------이상치 검출---------
    총 데이터 : 31875  이상치 :  306
    이상치 검출율 :  0.96 %
    낮 기준 이상치 :  0.9474509803921569 %
    밤 기준 이상치 :  0.012549019607843137 %


### AI030	/ 삼성04호 태양광발전소


```python
pv_id = 'AI030'

# 해당 발전소 데이터 추출
df_tmp = df_jn[df_jn.PV_ID == pv_id]
df = df_tmp.copy()
df.drop(columns=['DETL_ADDR'], inplace = True)

# 발전소 데이터 요약정보 확인
print(df.STATS_VAL.describe())
print()

# 20시 부터 5시까지 일사량이 20 이상인 데이터 수
print("-------밤시간 이상치 확인---------")
night, df_night = check_stats_val(20, 5, 20, '>', df)
print()

# 6시부터 18시까지 일사량이 10 이하인 데이터 수
print("-------낮시간 이상치 확인---------")
daytime, df_day = check_stats_val(8, 17, 10, '<', df)
print()

# 이상치 검출율
print("-------이상치 검출---------")
print("총 데이터 :", df.shape[0], " 이상치 : ", night+daytime)
print("이상치 검출율 : ", ((night+daytime) / df.shape[0])*100, "%" )
print("낮 기준 이상치 : ", (daytime/ df.shape[0])*100, "%")
print("밤 기준 이상치 : ", (night/ df.shape[0])*100, "%")

# 이상치로 검출된 데이터 저장
df_sum = pd.concat([df_day, df_night]).sort_values(by=['DATE', 'TIME'], axis=0)
df_sum.to_csv('dataset/abnormal/' + pv_id + '_abnormal.csv', index=False, encoding="utf-8-sig")
```

    count    30494.000000
    mean       101.948629
    std        181.835188
    min          0.000000
    25%          0.000000
    50%          0.000000
    75%        131.470650
    max        819.466400
    Name: STATS_VAL, dtype: float64
    
    -------밤시간 이상치 확인---------
    시간 : [20, 21, 22, 23, 0, 1, 2, 3, 4, 5]
    20 시 기준 이상치 :  0 , Boundary 이상치 :  0
    21 시 기준 이상치 :  0 , Boundary 이상치 :  0
    22 시 기준 이상치 :  0 , Boundary 이상치 :  0
    23 시 기준 이상치 :  0 , Boundary 이상치 :  0
    0 시 기준 이상치 :  0 , Boundary 이상치 :  0
    1 시 기준 이상치 :  0 , Boundary 이상치 :  0
    2 시 기준 이상치 :  0 , Boundary 이상치 :  0
    3 시 기준 이상치 :  0 , Boundary 이상치 :  0
    4 시 기준 이상치 :  0 , Boundary 이상치 :  0
    5 시 기준 이상치 :  0 , Boundary 이상치 :  0
    ======총  0 건 ======
    
    -------낮시간 이상치 확인---------
    시간 : [8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
    8 시 기준 이상치 :  237 , Boundary 이상치 :  0
    9 시 기준 이상치 :  175 , Boundary 이상치 :  0
    10 시 기준 이상치 :  142 , Boundary 이상치 :  0
    11 시 기준 이상치 :  130 , Boundary 이상치 :  0
    12 시 기준 이상치 :  121 , Boundary 이상치 :  0
    13 시 기준 이상치 :  121 , Boundary 이상치 :  0
    14 시 기준 이상치 :  136 , Boundary 이상치 :  0
    15 시 기준 이상치 :  154 , Boundary 이상치 :  0
    16 시 기준 이상치 :  254 , Boundary 이상치 :  0
    17 시 기준 이상치 :  659 , Boundary 이상치 :  0
    ======총  2129 건 ======
    
    -------이상치 검출---------
    총 데이터 : 30494  이상치 :  2129
    이상치 검출율 :  6.9817013182921235 %
    낮 기준 이상치 :  6.9817013182921235 %
    밤 기준 이상치 :  0.0 %


### AI031	/ 삼성05호 태양광발전소


```python
pv_id = 'AI031'

# 해당 발전소 데이터 추출
df_tmp = df_jn[df_jn.PV_ID == pv_id]
df = df_tmp.copy()
df.drop(columns=['DETL_ADDR'], inplace = True)

# 발전소 데이터 요약정보 확인
print(df.STATS_VAL.describe())
print()

# 20시 부터 5시까지 일사량이 20 이상인 데이터 수
print("-------밤시간 이상치 확인---------")
night, df_night = check_stats_val(20, 5, 20, '>', df)
print()

# 6시부터 18시까지 일사량이 10 이하인 데이터 수
print("-------낮시간 이상치 확인---------")
daytime, df_day = check_stats_val(8, 17, 10, '<', df)
print()

# 이상치 검출율
print("-------이상치 검출---------")
print("총 데이터 :", df.shape[0], " 이상치 : ", night+daytime)
print("이상치 검출율 : ", ((night+daytime) / df.shape[0])*100, "%" )
print("낮 기준 이상치 : ", (daytime/ df.shape[0])*100, "%")
print("밤 기준 이상치 : ", (night/ df.shape[0])*100, "%")

# 이상치로 검출된 데이터 저장
df_sum = pd.concat([df_day, df_night]).sort_values(by=['DATE', 'TIME'], axis=0)
df_sum.to_csv('dataset/abnormal/' + pv_id + '_abnormal.csv', index=False, encoding="utf-8-sig")
```

    count    30869.000000
    mean       105.490507
    std        193.836826
    min          0.000000
    25%          0.000000
    50%          0.000000
    75%        119.766900
    max        859.883200
    Name: STATS_VAL, dtype: float64
    
    -------밤시간 이상치 확인---------
    시간 : [20, 21, 22, 23, 0, 1, 2, 3, 4, 5]
    20 시 기준 이상치 :  0 , Boundary 이상치 :  0
    21 시 기준 이상치 :  0 , Boundary 이상치 :  0
    22 시 기준 이상치 :  0 , Boundary 이상치 :  0
    23 시 기준 이상치 :  0 , Boundary 이상치 :  0
    0 시 기준 이상치 :  0 , Boundary 이상치 :  0
    1 시 기준 이상치 :  0 , Boundary 이상치 :  0
    2 시 기준 이상치 :  0 , Boundary 이상치 :  0
    3 시 기준 이상치 :  0 , Boundary 이상치 :  0
    4 시 기준 이상치 :  0 , Boundary 이상치 :  0
    5 시 기준 이상치 :  0 , Boundary 이상치 :  0
    ======총  0 건 ======
    
    -------낮시간 이상치 확인---------
    시간 : [8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
    8 시 기준 이상치 :  327 , Boundary 이상치 :  0
    9 시 기준 이상치 :  245 , Boundary 이상치 :  0
    10 시 기준 이상치 :  209 , Boundary 이상치 :  0
    11 시 기준 이상치 :  204 , Boundary 이상치 :  0
    12 시 기준 이상치 :  182 , Boundary 이상치 :  0
    13 시 기준 이상치 :  190 , Boundary 이상치 :  0
    14 시 기준 이상치 :  219 , Boundary 이상치 :  0
    15 시 기준 이상치 :  245 , Boundary 이상치 :  0
    16 시 기준 이상치 :  349 , Boundary 이상치 :  0
    17 시 기준 이상치 :  672 , Boundary 이상치 :  0
    ======총  2842 건 ======
    
    -------이상치 검출---------
    총 데이터 : 30869  이상치 :  2842
    이상치 검출율 :  9.206647445657454 %
    낮 기준 이상치 :  9.206647445657454 %
    밤 기준 이상치 :  0.0 %


### AI032	/ 삼성06호 태양광발전소


```python
pv_id = 'AI032'

# 해당 발전소 데이터 추출
df_tmp = df_jn[df_jn.PV_ID == pv_id]
df = df_tmp.copy()
df.drop(columns=['DETL_ADDR'], inplace = True)

# 발전소 데이터 요약정보 확인
print(df.STATS_VAL.describe())
print()

# 20시 부터 5시까지 일사량이 20 이상인 데이터 수
print("-------밤시간 이상치 확인---------")
night, df_night = check_stats_val(20, 5, 20, '>', df)
print()

# 6시부터 18시까지 일사량이 10 이하인 데이터 수
print("-------낮시간 이상치 확인---------")
daytime, df_day = check_stats_val(8, 17, 10, '<', df)
print()

# 이상치 검출율
print("-------이상치 검출---------")
print("총 데이터 :", df.shape[0], " 이상치 : ", night+daytime)
print("이상치 검출율 : ", ((night+daytime) / df.shape[0])*100, "%" )
print("낮 기준 이상치 : ", (daytime/ df.shape[0])*100, "%")
print("밤 기준 이상치 : ", (night/ df.shape[0])*100, "%")

# 이상치로 검출된 데이터 저장
df_sum = pd.concat([df_day, df_night]).sort_values(by=['DATE', 'TIME'], axis=0)
df_sum.to_csv('dataset/abnormal/' + pv_id + '_abnormal.csv', index=False, encoding="utf-8-sig")
```

    count    30927.000000
    mean       104.798203
    std        194.820782
    min          0.000000
    25%          0.000000
    50%          0.000000
    75%        114.583250
    max        859.883200
    Name: STATS_VAL, dtype: float64
    
    -------밤시간 이상치 확인---------
    시간 : [20, 21, 22, 23, 0, 1, 2, 3, 4, 5]
    20 시 기준 이상치 :  0 , Boundary 이상치 :  0
    21 시 기준 이상치 :  0 , Boundary 이상치 :  0
    22 시 기준 이상치 :  0 , Boundary 이상치 :  0
    23 시 기준 이상치 :  0 , Boundary 이상치 :  0
    0 시 기준 이상치 :  0 , Boundary 이상치 :  0
    1 시 기준 이상치 :  0 , Boundary 이상치 :  0
    2 시 기준 이상치 :  0 , Boundary 이상치 :  0
    3 시 기준 이상치 :  0 , Boundary 이상치 :  0
    4 시 기준 이상치 :  0 , Boundary 이상치 :  0
    5 시 기준 이상치 :  0 , Boundary 이상치 :  0
    ======총  0 건 ======
    
    -------낮시간 이상치 확인---------
    시간 : [8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
    8 시 기준 이상치 :  364 , Boundary 이상치 :  0
    9 시 기준 이상치 :  292 , Boundary 이상치 :  0
    10 시 기준 이상치 :  264 , Boundary 이상치 :  0
    11 시 기준 이상치 :  258 , Boundary 이상치 :  0
    12 시 기준 이상치 :  247 , Boundary 이상치 :  0
    13 시 기준 이상치 :  251 , Boundary 이상치 :  0
    14 시 기준 이상치 :  260 , Boundary 이상치 :  0
    15 시 기준 이상치 :  269 , Boundary 이상치 :  0
    16 시 기준 이상치 :  355 , Boundary 이상치 :  0
    17 시 기준 이상치 :  678 , Boundary 이상치 :  0
    ======총  3238 건 ======
    
    -------이상치 검출---------
    총 데이터 : 30927  이상치 :  3238
    이상치 검출율 :  10.46981601836583 %
    낮 기준 이상치 :  10.46981601836583 %
    밤 기준 이상치 :  0.0 %


### AI036	/ 삼성11호 태양광발전소


```python
pv_id = 'AI036'

# 해당 발전소 데이터 추출
df_tmp = df_jn[df_jn.PV_ID == pv_id]
df = df_tmp.copy()
df.drop(columns=['DETL_ADDR'], inplace = True)

# 발전소 데이터 요약정보 확인
print(df.STATS_VAL.describe())
print()

# 20시 부터 5시까지 일사량이 20 이상인 데이터 수
print("-------밤시간 이상치 확인---------")
night, df_night = check_stats_val(20, 5, 20, '>', df)
print()

# 6시부터 18시까지 일사량이 10 이하인 데이터 수
print("-------낮시간 이상치 확인---------")
daytime, df_day = check_stats_val(8, 17, 10, '<', df)
print()

# 이상치 검출율
print("-------이상치 검출---------")
print("총 데이터 :", df.shape[0], " 이상치 : ", night+daytime)
print("이상치 검출율 : ", ((night+daytime) / df.shape[0])*100, "%" )
print("낮 기준 이상치 : ", (daytime/ df.shape[0])*100, "%")
print("밤 기준 이상치 : ", (night/ df.shape[0])*100, "%")

# 이상치로 검출된 데이터 저장
df_sum = pd.concat([df_day, df_night]).sort_values(by=['DATE', 'TIME'], axis=0)
df_sum.to_csv('dataset/abnormal/' + pv_id + '_abnormal.csv', index=False, encoding="utf-8-sig")
```

    count    22268.000000
    mean       107.566178
    std        187.160000
    min          0.000000
    25%          2.783200
    50%         12.158000
    75%        110.195475
    max        827.733600
    Name: STATS_VAL, dtype: float64
    
    -------밤시간 이상치 확인---------
    시간 : [20, 21, 22, 23, 0, 1, 2, 3, 4, 5]
    20 시 기준 이상치 :  67 , Boundary 이상치 :  0
    21 시 기준 이상치 :  86 , Boundary 이상치 :  0
    22 시 기준 이상치 :  75 , Boundary 이상치 :  0
    23 시 기준 이상치 :  85 , Boundary 이상치 :  0
    0 시 기준 이상치 :  78 , Boundary 이상치 :  0
    1 시 기준 이상치 :  79 , Boundary 이상치 :  0
    2 시 기준 이상치 :  84 , Boundary 이상치 :  0
    3 시 기준 이상치 :  78 , Boundary 이상치 :  0
    4 시 기준 이상치 :  72 , Boundary 이상치 :  0
    5 시 기준 이상치 :  85 , Boundary 이상치 :  0
    ======총  789 건 ======
    
    -------낮시간 이상치 확인---------
    시간 : [8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
    8 시 기준 이상치 :  264 , Boundary 이상치 :  0
    9 시 기준 이상치 :  106 , Boundary 이상치 :  0
    10 시 기준 이상치 :  73 , Boundary 이상치 :  0
    11 시 기준 이상치 :  48 , Boundary 이상치 :  0
    12 시 기준 이상치 :  45 , Boundary 이상치 :  0
    13 시 기준 이상치 :  45 , Boundary 이상치 :  0
    14 시 기준 이상치 :  53 , Boundary 이상치 :  0
    15 시 기준 이상치 :  80 , Boundary 이상치 :  0
    16 시 기준 이상치 :  130 , Boundary 이상치 :  0
    17 시 기준 이상치 :  325 , Boundary 이상치 :  0
    ======총  1169 건 ======
    
    -------이상치 검출---------
    총 데이터 : 22268  이상치 :  1958
    이상치 검출율 :  8.792886653493802 %
    낮 기준 이상치 :  5.249685647566014 %
    밤 기준 이상치 :  3.5432010059277887 %


### AM009	/ 도덕2호 태양광발전소


```python
pv_id = 'AM009'

# 해당 발전소 데이터 추출
df_tmp = df_jn[df_jn.PV_ID == pv_id]
df = df_tmp.copy()
df.drop(columns=['DETL_ADDR'], inplace = True)

# 발전소 데이터 요약정보 확인
print(df.STATS_VAL.describe())
print()

# 20시 부터 5시까지 일사량이 20 이상인 데이터 수
print("-------밤시간 이상치 확인---------")
night, df_night = check_stats_val(20, 5, 20, '>', df)
print()

# 6시부터 18시까지 일사량이 10 이하인 데이터 수
print("-------낮시간 이상치 확인---------")
daytime, df_day = check_stats_val(8, 17, 10, '<', df)
print()

# 이상치 검출율
print("-------이상치 검출---------")
print("총 데이터 :", df.shape[0], " 이상치 : ", night+daytime)
print("이상치 검출율 : ", ((night+daytime) / df.shape[0])*100, "%" )
print("낮 기준 이상치 : ", (daytime/ df.shape[0])*100, "%")
print("밤 기준 이상치 : ", (night/ df.shape[0])*100, "%")

# 이상치로 검출된 데이터 저장
df_sum = pd.concat([df_day, df_night]).sort_values(by=['DATE', 'TIME'], axis=0)
df_sum.to_csv('dataset/abnormal/' + pv_id + '_abnormal.csv', index=False, encoding="utf-8-sig")
```

    count    32194.000000
    mean       178.689002
    std        265.493112
    min          0.000000
    25%          0.000000
    50%          6.150000
    75%        301.037425
    max       1009.333700
    Name: STATS_VAL, dtype: float64
    
    -------밤시간 이상치 확인---------
    시간 : [20, 21, 22, 23, 0, 1, 2, 3, 4, 5]
    20 시 기준 이상치 :  0 , Boundary 이상치 :  0
    21 시 기준 이상치 :  0 , Boundary 이상치 :  0
    22 시 기준 이상치 :  0 , Boundary 이상치 :  0
    23 시 기준 이상치 :  0 , Boundary 이상치 :  0
    0 시 기준 이상치 :  0 , Boundary 이상치 :  0
    1 시 기준 이상치 :  0 , Boundary 이상치 :  0
    2 시 기준 이상치 :  0 , Boundary 이상치 :  0
    3 시 기준 이상치 :  0 , Boundary 이상치 :  0
    4 시 기준 이상치 :  0 , Boundary 이상치 :  0
    5 시 기준 이상치 :  4 , Boundary 이상치 :  0
    ======총  4 건 ======
    
    -------낮시간 이상치 확인---------
    시간 : [8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
    8 시 기준 이상치 :  14 , Boundary 이상치 :  0
    9 시 기준 이상치 :  5 , Boundary 이상치 :  0
    10 시 기준 이상치 :  2 , Boundary 이상치 :  0
    11 시 기준 이상치 :  1 , Boundary 이상치 :  0
    12 시 기준 이상치 :  1 , Boundary 이상치 :  0
    13 시 기준 이상치 :  1 , Boundary 이상치 :  0
    14 시 기준 이상치 :  1 , Boundary 이상치 :  0
    15 시 기준 이상치 :  2 , Boundary 이상치 :  0
    16 시 기준 이상치 :  12 , Boundary 이상치 :  0
    17 시 기준 이상치 :  248 , Boundary 이상치 :  0
    ======총  287 건 ======
    
    -------이상치 검출---------
    총 데이터 : 32194  이상치 :  291
    이상치 검출율 :  0.9038951357395788 %
    낮 기준 이상치 :  0.8914704603342238 %
    밤 기준 이상치 :  0.012424675405355034 %


### AM011	/ 도덕3호 태양광발전소


```python
pv_id = 'AM011'

# 해당 발전소 데이터 추출
df_tmp = df_jn[df_jn.PV_ID == pv_id]
df = df_tmp.copy()
df.drop(columns=['DETL_ADDR'], inplace = True)

# 발전소 데이터 요약정보 확인
print(df.STATS_VAL.describe())
print()

# 20시 부터 5시까지 일사량이 20 이상인 데이터 수
print("-------밤시간 이상치 확인---------")
night, df_night = check_stats_val(20, 5, 20, '>', df)
print()

# 6시부터 18시까지 일사량이 10 이하인 데이터 수
print("-------낮시간 이상치 확인---------")
daytime, df_day = check_stats_val(8, 17, 10, '<', df)
print()

# 이상치 검출율
print("-------이상치 검출---------")
print("총 데이터 :", df.shape[0], " 이상치 : ", night+daytime)
print("이상치 검출율 : ", ((night+daytime) / df.shape[0])*100, "%" )
print("낮 기준 이상치 : ", (daytime/ df.shape[0])*100, "%")
print("밤 기준 이상치 : ", (night/ df.shape[0])*100, "%")

# 이상치로 검출된 데이터 저장
df_sum = pd.concat([df_day, df_night]).sort_values(by=['DATE', 'TIME'], axis=0)
df_sum.to_csv('dataset/abnormal/' + pv_id + '_abnormal.csv', index=False, encoding="utf-8-sig")
```

    count    32194.000000
    mean       178.392584
    std        265.091039
    min          0.000000
    25%          0.000000
    50%          6.150000
    75%        300.479050
    max       1009.333700
    Name: STATS_VAL, dtype: float64
    
    -------밤시간 이상치 확인---------
    시간 : [20, 21, 22, 23, 0, 1, 2, 3, 4, 5]
    20 시 기준 이상치 :  0 , Boundary 이상치 :  0
    21 시 기준 이상치 :  0 , Boundary 이상치 :  0
    22 시 기준 이상치 :  0 , Boundary 이상치 :  0
    23 시 기준 이상치 :  0 , Boundary 이상치 :  0
    0 시 기준 이상치 :  0 , Boundary 이상치 :  0
    1 시 기준 이상치 :  0 , Boundary 이상치 :  0
    2 시 기준 이상치 :  0 , Boundary 이상치 :  0
    3 시 기준 이상치 :  0 , Boundary 이상치 :  0
    4 시 기준 이상치 :  0 , Boundary 이상치 :  0
    5 시 기준 이상치 :  4 , Boundary 이상치 :  0
    ======총  4 건 ======
    
    -------낮시간 이상치 확인---------
    시간 : [8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
    8 시 기준 이상치 :  14 , Boundary 이상치 :  0
    9 시 기준 이상치 :  5 , Boundary 이상치 :  0
    10 시 기준 이상치 :  2 , Boundary 이상치 :  0
    11 시 기준 이상치 :  1 , Boundary 이상치 :  0
    12 시 기준 이상치 :  1 , Boundary 이상치 :  0
    13 시 기준 이상치 :  1 , Boundary 이상치 :  0
    14 시 기준 이상치 :  1 , Boundary 이상치 :  0
    15 시 기준 이상치 :  2 , Boundary 이상치 :  0
    16 시 기준 이상치 :  12 , Boundary 이상치 :  0
    17 시 기준 이상치 :  248 , Boundary 이상치 :  0
    ======총  287 건 ======
    
    -------이상치 검출---------
    총 데이터 : 32194  이상치 :  291
    이상치 검출율 :  0.9038951357395788 %
    낮 기준 이상치 :  0.8914704603342238 %
    밤 기준 이상치 :  0.012424675405355034 %


### AM012	/ 삼성08A 태양광발전소


```python
pv_id = 'AM012'

# 해당 발전소 데이터 추출
df_tmp = df_jn[df_jn.PV_ID == pv_id]
df = df_tmp.copy()
df.drop(columns=['DETL_ADDR'], inplace = True)

# 발전소 데이터 요약정보 확인
print(df.STATS_VAL.describe())
print()

# 20시 부터 5시까지 일사량이 20 이상인 데이터 수
print("-------밤시간 이상치 확인---------")
night, df_night = check_stats_val(20, 5, 20, '>', df)
print()

# 6시부터 18시까지 일사량이 10 이하인 데이터 수
print("-------낮시간 이상치 확인---------")
daytime, df_day = check_stats_val(8, 17, 10, '<', df)
print()

# 이상치 검출율
print("-------이상치 검출---------")
print("총 데이터 :", df.shape[0], " 이상치 : ", night+daytime)
print("이상치 검출율 : ", ((night+daytime) / df.shape[0])*100, "%" )
print("낮 기준 이상치 : ", (daytime/ df.shape[0])*100, "%")
print("밤 기준 이상치 : ", (night/ df.shape[0])*100, "%")

# 이상치로 검출된 데이터 저장
df_sum = pd.concat([df_day, df_night]).sort_values(by=['DATE', 'TIME'], axis=0)
df_sum.to_csv('dataset/abnormal/' + pv_id + '_abnormal.csv', index=False, encoding="utf-8-sig")
```

    count    32458.00000
    mean       167.69352
    std        253.67311
    min          0.00000
    25%          0.00000
    50%          4.59160
    75%        276.66275
    max        962.21650
    Name: STATS_VAL, dtype: float64
    
    -------밤시간 이상치 확인---------
    시간 : [20, 21, 22, 23, 0, 1, 2, 3, 4, 5]
    20 시 기준 이상치 :  0 , Boundary 이상치 :  0
    21 시 기준 이상치 :  0 , Boundary 이상치 :  0
    22 시 기준 이상치 :  0 , Boundary 이상치 :  0
    23 시 기준 이상치 :  0 , Boundary 이상치 :  0
    0 시 기준 이상치 :  0 , Boundary 이상치 :  0
    1 시 기준 이상치 :  0 , Boundary 이상치 :  0
    2 시 기준 이상치 :  0 , Boundary 이상치 :  0
    3 시 기준 이상치 :  0 , Boundary 이상치 :  0
    4 시 기준 이상치 :  0 , Boundary 이상치 :  0
    5 시 기준 이상치 :  3 , Boundary 이상치 :  0
    ======총  3 건 ======
    
    -------낮시간 이상치 확인---------
    시간 : [8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
    8 시 기준 이상치 :  27 , Boundary 이상치 :  0
    9 시 기준 이상치 :  19 , Boundary 이상치 :  0
    10 시 기준 이상치 :  15 , Boundary 이상치 :  0
    11 시 기준 이상치 :  14 , Boundary 이상치 :  0
    12 시 기준 이상치 :  15 , Boundary 이상치 :  0
    13 시 기준 이상치 :  15 , Boundary 이상치 :  0
    14 시 기준 이상치 :  14 , Boundary 이상치 :  0
    15 시 기준 이상치 :  15 , Boundary 이상치 :  0
    16 시 기준 이상치 :  24 , Boundary 이상치 :  0
    17 시 기준 이상치 :  235 , Boundary 이상치 :  0
    ======총  393 건 ======
    
    -------이상치 검출---------
    총 데이터 : 32458  이상치 :  396
    이상치 검출율 :  1.2200382032164643 %
    낮 기준 이상치 :  1.2107954895557336 %
    밤 기준 이상치 :  0.009242713660730791 %


### AM013	/ 삼성09B 태양광발전소


```python
pv_id = 'AM013'

# 해당 발전소 데이터 추출
df_tmp = df_jn[df_jn.PV_ID == pv_id]
df = df_tmp.copy()
df.drop(columns=['DETL_ADDR'], inplace = True)

# 발전소 데이터 요약정보 확인
print(df.STATS_VAL.describe())
print()

# 20시 부터 5시까지 일사량이 20 이상인 데이터 수
print("-------밤시간 이상치 확인---------")
night, df_night = check_stats_val(20, 5, 20, '>', df)
print()

# 6시부터 18시까지 일사량이 10 이하인 데이터 수
print("-------낮시간 이상치 확인---------")
daytime, df_day = check_stats_val(8, 17, 10, '<', df)
print()

# 이상치 검출율
print("-------이상치 검출---------")
print("총 데이터 :", df.shape[0], " 이상치 : ", night+daytime)
print("이상치 검출율 : ", ((night+daytime) / df.shape[0])*100, "%" )
print("낮 기준 이상치 : ", (daytime/ df.shape[0])*100, "%")
print("밤 기준 이상치 : ", (night/ df.shape[0])*100, "%")

# 이상치로 검출된 데이터 저장
df_sum = pd.concat([df_day, df_night]).sort_values(by=['DATE', 'TIME'], axis=0)
df_sum.to_csv('dataset/abnormal/' + pv_id + '_abnormal.csv', index=False, encoding="utf-8-sig")
```

    count    32439.000000
    mean       168.219611
    std        254.345005
    min          0.000000
    25%          0.000000
    50%          4.649900
    75%        277.766600
    max        962.216500
    Name: STATS_VAL, dtype: float64
    
    -------밤시간 이상치 확인---------
    시간 : [20, 21, 22, 23, 0, 1, 2, 3, 4, 5]
    20 시 기준 이상치 :  0 , Boundary 이상치 :  0
    21 시 기준 이상치 :  0 , Boundary 이상치 :  0
    22 시 기준 이상치 :  0 , Boundary 이상치 :  0
    23 시 기준 이상치 :  0 , Boundary 이상치 :  0
    0 시 기준 이상치 :  0 , Boundary 이상치 :  0
    1 시 기준 이상치 :  0 , Boundary 이상치 :  0
    2 시 기준 이상치 :  0 , Boundary 이상치 :  0
    3 시 기준 이상치 :  0 , Boundary 이상치 :  0
    4 시 기준 이상치 :  0 , Boundary 이상치 :  0
    5 시 기준 이상치 :  3 , Boundary 이상치 :  0
    ======총  3 건 ======
    
    -------낮시간 이상치 확인---------
    시간 : [8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
    8 시 기준 이상치 :  26 , Boundary 이상치 :  0
    9 시 기준 이상치 :  18 , Boundary 이상치 :  0
    10 시 기준 이상치 :  14 , Boundary 이상치 :  0
    11 시 기준 이상치 :  13 , Boundary 이상치 :  0
    12 시 기준 이상치 :  14 , Boundary 이상치 :  0
    13 시 기준 이상치 :  15 , Boundary 이상치 :  0
    14 시 기준 이상치 :  14 , Boundary 이상치 :  0
    15 시 기준 이상치 :  15 , Boundary 이상치 :  0
    16 시 기준 이상치 :  24 , Boundary 이상치 :  0
    17 시 기준 이상치 :  234 , Boundary 이상치 :  0
    ======총  387 건 ======
    
    -------이상치 검출---------
    총 데이터 : 32439  이상치 :  390
    이상치 검출율 :  1.2022565430500323 %
    낮 기준 이상치 :  1.1930084157958014 %
    밤 기준 이상치 :  0.009248127254231018 %


### AM014	/ 삼성09A 태양광발전소


```python
pv_id = 'AM014'

# 해당 발전소 데이터 추출
df_tmp = df_jn[df_jn.PV_ID == pv_id]
df = df_tmp.copy()
df.drop(columns=['DETL_ADDR'], inplace = True)

# 발전소 데이터 요약정보 확인
print(df.STATS_VAL.describe())
print()

# 20시 부터 5시까지 일사량이 20 이상인 데이터 수
print("-------밤시간 이상치 확인---------")
night, df_night = check_stats_val(20, 5, 20, '>', df)
print()

# 6시부터 18시까지 일사량이 10 이하인 데이터 수
print("-------낮시간 이상치 확인---------")
daytime, df_day = check_stats_val(8, 17, 10, '<', df)
print()

# 이상치 검출율
print("-------이상치 검출---------")
print("총 데이터 :", df.shape[0], " 이상치 : ", night+daytime)
print("이상치 검출율 : ", ((night+daytime) / df.shape[0])*100, "%" )
print("낮 기준 이상치 : ", (daytime/ df.shape[0])*100, "%")
print("밤 기준 이상치 : ", (night/ df.shape[0])*100, "%")

# 이상치로 검출된 데이터 저장
df_sum = pd.concat([df_day, df_night]).sort_values(by=['DATE', 'TIME'], axis=0)
df_sum.to_csv('dataset/abnormal/' + pv_id + '_abnormal.csv', index=False, encoding="utf-8-sig")
```

    count    30631.000000
    mean       114.876791
    std        193.794665
    min          0.000000
    25%          0.000000
    50%          0.650000
    75%        158.750000
    max        885.333300
    Name: STATS_VAL, dtype: float64
    
    -------밤시간 이상치 확인---------
    시간 : [20, 21, 22, 23, 0, 1, 2, 3, 4, 5]
    20 시 기준 이상치 :  0 , Boundary 이상치 :  0
    21 시 기준 이상치 :  0 , Boundary 이상치 :  0
    22 시 기준 이상치 :  0 , Boundary 이상치 :  0
    23 시 기준 이상치 :  0 , Boundary 이상치 :  0
    0 시 기준 이상치 :  0 , Boundary 이상치 :  0
    1 시 기준 이상치 :  0 , Boundary 이상치 :  0
    2 시 기준 이상치 :  0 , Boundary 이상치 :  0
    3 시 기준 이상치 :  0 , Boundary 이상치 :  0
    4 시 기준 이상치 :  0 , Boundary 이상치 :  0
    5 시 기준 이상치 :  0 , Boundary 이상치 :  0
    ======총  0 건 ======
    
    -------낮시간 이상치 확인---------
    시간 : [8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
    8 시 기준 이상치 :  64 , Boundary 이상치 :  0
    9 시 기준 이상치 :  21 , Boundary 이상치 :  0
    10 시 기준 이상치 :  6 , Boundary 이상치 :  0
    11 시 기준 이상치 :  2 , Boundary 이상치 :  0
    12 시 기준 이상치 :  3 , Boundary 이상치 :  0
    13 시 기준 이상치 :  3 , Boundary 이상치 :  0
    14 시 기준 이상치 :  5 , Boundary 이상치 :  0
    15 시 기준 이상치 :  23 , Boundary 이상치 :  0
    16 시 기준 이상치 :  74 , Boundary 이상치 :  0
    17 시 기준 이상치 :  430 , Boundary 이상치 :  0
    ======총  631 건 ======
    
    -------이상치 검출---------
    총 데이터 : 30631  이상치 :  631
    이상치 검출율 :  2.06000457053312 %
    낮 기준 이상치 :  2.06000457053312 %
    밤 기준 이상치 :  0.0 %


### AM015	/ 도덕1호 태양광발전소


```python
pv_id = 'AM015'

# 해당 발전소 데이터 추출
df_tmp = df_jn[df_jn.PV_ID == pv_id]
df = df_tmp.copy()
df.drop(columns=['DETL_ADDR'], inplace = True)

# 발전소 데이터 요약정보 확인
print(df.STATS_VAL.describe())
print()

# 20시 부터 5시까지 일사량이 20 이상인 데이터 수
print("-------밤시간 이상치 확인---------")
night, df_night = check_stats_val(20, 5, 20, '>', df)
print()

# 6시부터 18시까지 일사량이 10 이하인 데이터 수
print("-------낮시간 이상치 확인---------")
daytime, df_day = check_stats_val(8, 17, 10, '<', df)
print()

# 이상치 검출율
print("-------이상치 검출---------")
print("총 데이터 :", df.shape[0], " 이상치 : ", night+daytime)
print("이상치 검출율 : ", ((night+daytime) / df.shape[0])*100, "%" )
print("낮 기준 이상치 : ", (daytime/ df.shape[0])*100, "%")
print("밤 기준 이상치 : ", (night/ df.shape[0])*100, "%")

# 이상치로 검출된 데이터 저장
df_sum = pd.concat([df_day, df_night]).sort_values(by=['DATE', 'TIME'], axis=0)
df_sum.to_csv('dataset/abnormal/' + pv_id + '_abnormal.csv', index=False, encoding="utf-8-sig")
```

    count    30817.000000
    mean       110.043583
    std        185.378914
    min          0.000000
    25%          0.000000
    50%          0.000000
    75%        157.833100
    max        828.983600
    Name: STATS_VAL, dtype: float64
    
    -------밤시간 이상치 확인---------
    시간 : [20, 21, 22, 23, 0, 1, 2, 3, 4, 5]
    20 시 기준 이상치 :  0 , Boundary 이상치 :  0
    21 시 기준 이상치 :  0 , Boundary 이상치 :  0
    22 시 기준 이상치 :  0 , Boundary 이상치 :  0
    23 시 기준 이상치 :  0 , Boundary 이상치 :  0
    0 시 기준 이상치 :  0 , Boundary 이상치 :  0
    1 시 기준 이상치 :  0 , Boundary 이상치 :  0
    2 시 기준 이상치 :  0 , Boundary 이상치 :  0
    3 시 기준 이상치 :  0 , Boundary 이상치 :  0
    4 시 기준 이상치 :  0 , Boundary 이상치 :  0
    5 시 기준 이상치 :  0 , Boundary 이상치 :  0
    ======총  0 건 ======
    
    -------낮시간 이상치 확인---------
    시간 : [8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
    8 시 기준 이상치 :  113 , Boundary 이상치 :  0
    9 시 기준 이상치 :  59 , Boundary 이상치 :  0
    10 시 기준 이상치 :  38 , Boundary 이상치 :  0
    11 시 기준 이상치 :  33 , Boundary 이상치 :  0
    12 시 기준 이상치 :  31 , Boundary 이상치 :  0
    13 시 기준 이상치 :  29 , Boundary 이상치 :  0
    14 시 기준 이상치 :  35 , Boundary 이상치 :  0
    15 시 기준 이상치 :  56 , Boundary 이상치 :  0
    16 시 기준 이상치 :  124 , Boundary 이상치 :  0
    17 시 기준 이상치 :  488 , Boundary 이상치 :  0
    ======총  1006 건 ======
    
    -------이상치 검출---------
    총 데이터 : 30817  이상치 :  1006
    이상치 검출율 :  3.2644319693675565 %
    낮 기준 이상치 :  3.2644319693675565 %
    밤 기준 이상치 :  0.0 %


### AM016 / 삼성08B 태양광발전소


```python
pv_id = 'AM016'

# 해당 발전소 데이터 추출
df_tmp = df_jn[df_jn.PV_ID == pv_id]
df = df_tmp.copy()
df.drop(columns=['DETL_ADDR'], inplace = True)

# 발전소 데이터 요약정보 확인
print(df.STATS_VAL.describe())
print()

# 20시 부터 5시까지 일사량이 20 이상인 데이터 수
print("-------밤시간 이상치 확인---------")
night, df_night = check_stats_val(20, 5, 20, '>', df)
print()

# 6시부터 18시까지 일사량이 10 이하인 데이터 수
print("-------낮시간 이상치 확인---------")
daytime, df_day = check_stats_val(8, 17, 10, '<', df)
print()

# 이상치 검출율
print("-------이상치 검출---------")
print("총 데이터 :", df.shape[0], " 이상치 : ", night+daytime)
print("이상치 검출율 : ", ((night+daytime) / df.shape[0])*100, "%" )
print("낮 기준 이상치 : ", (daytime/ df.shape[0])*100, "%")
print("밤 기준 이상치 : ", (night/ df.shape[0])*100, "%")

# 이상치로 검출된 데이터 저장
df_sum = pd.concat([df_day, df_night]).sort_values(by=['DATE', 'TIME'], axis=0)
df_sum.to_csv('dataset/abnormal/' + pv_id + '_abnormal.csv', index=False, encoding="utf-8-sig")
```

    count    30336.000000
    mean       166.913800
    std        252.299477
    min          0.000000
    25%          0.000000
    50%          4.591600
    75%        276.920825
    max        962.216500
    Name: STATS_VAL, dtype: float64
    
    -------밤시간 이상치 확인---------
    시간 : [20, 21, 22, 23, 0, 1, 2, 3, 4, 5]
    20 시 기준 이상치 :  0 , Boundary 이상치 :  0
    21 시 기준 이상치 :  0 , Boundary 이상치 :  0
    22 시 기준 이상치 :  0 , Boundary 이상치 :  0
    23 시 기준 이상치 :  0 , Boundary 이상치 :  0
    0 시 기준 이상치 :  0 , Boundary 이상치 :  0
    1 시 기준 이상치 :  0 , Boundary 이상치 :  0
    2 시 기준 이상치 :  0 , Boundary 이상치 :  0
    3 시 기준 이상치 :  0 , Boundary 이상치 :  0
    4 시 기준 이상치 :  0 , Boundary 이상치 :  0
    5 시 기준 이상치 :  3 , Boundary 이상치 :  0
    ======총  3 건 ======
    
    -------낮시간 이상치 확인---------
    시간 : [8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
    8 시 기준 이상치 :  27 , Boundary 이상치 :  0
    9 시 기준 이상치 :  19 , Boundary 이상치 :  0
    10 시 기준 이상치 :  14 , Boundary 이상치 :  0
    11 시 기준 이상치 :  14 , Boundary 이상치 :  0
    12 시 기준 이상치 :  15 , Boundary 이상치 :  0
    13 시 기준 이상치 :  15 , Boundary 이상치 :  0
    14 시 기준 이상치 :  14 , Boundary 이상치 :  0
    15 시 기준 이상치 :  15 , Boundary 이상치 :  0
    16 시 기준 이상치 :  23 , Boundary 이상치 :  0
    17 시 기준 이상치 :  226 , Boundary 이상치 :  0
    ======총  382 건 ======
    
    -------이상치 검출---------
    총 데이터 : 30336  이상치 :  385
    이상치 검출율 :  1.2691191983122363 %
    낮 기준 이상치 :  1.2592299578059072 %
    밤 기준 이상치 :  0.009889240506329115 %


## 4-2. 전라북도 지역 이상치 검출 수행


```python
# 전라남도 발전소 시간별 일사량 데이터
df_jb = df_new[df_new['DETL_ADDR'].str.contains('전라북도')]

# 전라남도 발전소 리스트 확인
df_jb.drop_duplicates(subset=['PV_ID']).reset_index(drop=True).drop(columns=['STATS_VAL', 'DATE','TIME'])
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>PV_ID</th>
      <th>AREA_ID</th>
      <th>PV_KOR_NM</th>
      <th>FCLTY_CPCTY</th>
      <th>DETL_ADDR</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>AI025</td>
      <td>1842859</td>
      <td>지에프 상하 태양광발전소</td>
      <td>999.0000</td>
      <td>대한민국 전라북도 고창군 상하면 진암구시포로 412</td>
    </tr>
  </tbody>
</table>
</div>



### AI025 / 지에프 상하 태양광발전소


```python
pv_id = 'AI025'

# 해당 발전소 데이터 추출
df_tmp = df_jb[df_jb.PV_ID == pv_id]
df = df_tmp.copy()
df.drop(columns=['DETL_ADDR'], inplace = True)

# 발전소 데이터 요약정보 확인
print(df.STATS_VAL.describe())
print()

# 20시 부터 5시까지 일사량이 20 이상인 데이터 수
print("-------밤시간 이상치 확인---------")
night, df_night = check_stats_val(20, 5, 20, '>', df)
print()

# 6시부터 18시까지 일사량이 10 이하인 데이터 수
print("-------낮시간 이상치 확인---------")
daytime, df_day = check_stats_val(8, 17, 10, '<', df)
print()

# 이상치 검출율
print("-------이상치 검출---------")
print("총 데이터 :", df.shape[0], " 이상치 : ", night+daytime)
print("이상치 검출율 : ", ((night+daytime) / df.shape[0])*100, "%" )
print("낮 기준 이상치 : ", (daytime/ df.shape[0])*100, "%")
print("밤 기준 이상치 : ", (night/ df.shape[0])*100, "%")

# 이상치로 검출된 데이터 저장
df_sum = pd.concat([df_day, df_night]).sort_values(by=['DATE', 'TIME'], axis=0)
df_sum.to_csv('dataset/abnormal/' + pv_id + '_abnormal.csv', index=False, encoding="utf-8-sig")
```

    count    35867.000000
    mean       141.812347
    std        287.462894
    min        -56.815200
    25%          0.000000
    50%          1.314000
    75%        149.326200
    max       1750.002000
    Name: STATS_VAL, dtype: float64
    
    -------밤시간 이상치 확인---------
    시간 : [20, 21, 22, 23, 0, 1, 2, 3, 4, 5]
    20 시 기준 이상치 :  12 , Boundary 이상치 :  28
    21 시 기준 이상치 :  11 , Boundary 이상치 :  28
    22 시 기준 이상치 :  11 , Boundary 이상치 :  28
    23 시 기준 이상치 :  13 , Boundary 이상치 :  29
    0 시 기준 이상치 :  14 , Boundary 이상치 :  28
    1 시 기준 이상치 :  14 , Boundary 이상치 :  29
    2 시 기준 이상치 :  15 , Boundary 이상치 :  30
    3 시 기준 이상치 :  14 , Boundary 이상치 :  30
    4 시 기준 이상치 :  14 , Boundary 이상치 :  30
    5 시 기준 이상치 :  15 , Boundary 이상치 :  27
    ======총  420 건 ======
    
    -------낮시간 이상치 확인---------
    시간 : [8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
    8 시 기준 이상치 :  378 , Boundary 이상치 :  23
    9 시 기준 이상치 :  367 , Boundary 이상치 :  22
    10 시 기준 이상치 :  364 , Boundary 이상치 :  23
    11 시 기준 이상치 :  364 , Boundary 이상치 :  23
    12 시 기준 이상치 :  362 , Boundary 이상치 :  23
    13 시 기준 이상치 :  361 , Boundary 이상치 :  21
    14 시 기준 이상치 :  366 , Boundary 이상치 :  21
    15 시 기준 이상치 :  367 , Boundary 이상치 :  22
    16 시 기준 이상치 :  378 , Boundary 이상치 :  20
    17 시 기준 이상치 :  553 , Boundary 이상치 :  22
    ======총  4080 건 ======
    
    -------이상치 검출---------
    총 데이터 : 35867  이상치 :  4500
    이상치 검출율 :  12.546351799704464 %
    낮 기준 이상치 :  11.37535896506538 %
    밤 기준 이상치 :  1.1709928346390832 %


## 4-3. 경상남도 지역 이상치 검출 수행


```python
# 경상남도 발전소 시간별 일사량 데이터
df_gn = df_new[df_new['DETL_ADDR'].str.contains('경상남도')]

# 경상남도 발전소 리스트 확인
df_gn.drop_duplicates(subset=['PV_ID']).reset_index(drop=True).drop(columns=['STATS_VAL', 'DATE','TIME'])
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>PV_ID</th>
      <th>AREA_ID</th>
      <th>PV_KOR_NM</th>
      <th>FCLTY_CPCTY</th>
      <th>DETL_ADDR</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>AI023</td>
      <td>1842943</td>
      <td>그린 김해 태양광발전소</td>
      <td>999.1800</td>
      <td>대한민국 경상남도 김해시 장유면 신문리 52-8</td>
    </tr>
    <tr>
      <th>1</th>
      <td>AI037</td>
      <td>1846052</td>
      <td>의령1호</td>
      <td>992.3400</td>
      <td>대한민국 경상남도 의령군 화정면 상일리 산95</td>
    </tr>
    <tr>
      <th>2</th>
      <td>AI039</td>
      <td>1846052</td>
      <td>의령3호</td>
      <td>498.9600</td>
      <td>대한민국 경상남도 의령군 화정면 상일리 산95</td>
    </tr>
  </tbody>
</table>
</div>



### AI023 / 그린 김해 태양광발전소


```python
pv_id = 'AI023'

# 해당 발전소 데이터 추출
df_tmp = df_gn[df_gn.PV_ID == pv_id]
df = df_tmp.copy()
df.drop(columns=['DETL_ADDR'], inplace = True)

# 발전소 데이터 요약정보 확인
print(df.STATS_VAL.describe())
print()

# 20시 부터 5시까지 일사량이 20 이상인 데이터 수
print("-------밤시간 이상치 확인---------")
night, df_night = check_stats_val(20, 5, 20, '>', df)
print()

# 6시부터 18시까지 일사량이 10 이하인 데이터 수
print("-------낮시간 이상치 확인---------")
daytime, df_day = check_stats_val(8, 17, 10, '<', df)
print()

# 이상치 검출율
print("-------이상치 검출---------")
print("총 데이터 :", df.shape[0], " 이상치 : ", night+daytime)
print("이상치 검출율 : ", ((night+daytime) / df.shape[0])*100, "%" )
print("낮 기준 이상치 : ", (daytime/ df.shape[0])*100, "%")
print("밤 기준 이상치 : ", (night/ df.shape[0])*100, "%")

# 이상치로 검출된 데이터 저장
df_sum = pd.concat([df_day, df_night]).sort_values(by=['DATE', 'TIME'], axis=0)
df_sum.to_csv('dataset/abnormal/' + pv_id + '_abnormal.csv', index=False, encoding="utf-8-sig")
```

    count    40016.000000
    mean       193.575529
    std        282.785321
    min          0.000000
    25%          3.498000
    50%          9.191500
    75%        319.700075
    max       1104.666800
    Name: STATS_VAL, dtype: float64
    
    -------밤시간 이상치 확인---------
    시간 : [20, 21, 22, 23, 0, 1, 2, 3, 4, 5]
    20 시 기준 이상치 :  13 , Boundary 이상치 :  0
    21 시 기준 이상치 :  13 , Boundary 이상치 :  0
    22 시 기준 이상치 :  13 , Boundary 이상치 :  0
    23 시 기준 이상치 :  13 , Boundary 이상치 :  0
    0 시 기준 이상치 :  13 , Boundary 이상치 :  0
    1 시 기준 이상치 :  13 , Boundary 이상치 :  0
    2 시 기준 이상치 :  13 , Boundary 이상치 :  0
    3 시 기준 이상치 :  13 , Boundary 이상치 :  0
    4 시 기준 이상치 :  13 , Boundary 이상치 :  0
    5 시 기준 이상치 :  97 , Boundary 이상치 :  0
    ======총  214 건 ======
    
    -------낮시간 이상치 확인---------
    시간 : [8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
    8 시 기준 이상치 :  22 , Boundary 이상치 :  0
    9 시 기준 이상치 :  7 , Boundary 이상치 :  0
    10 시 기준 이상치 :  5 , Boundary 이상치 :  0
    11 시 기준 이상치 :  4 , Boundary 이상치 :  0
    12 시 기준 이상치 :  3 , Boundary 이상치 :  0
    13 시 기준 이상치 :  2 , Boundary 이상치 :  0
    14 시 기준 이상치 :  4 , Boundary 이상치 :  0
    15 시 기준 이상치 :  5 , Boundary 이상치 :  0
    16 시 기준 이상치 :  34 , Boundary 이상치 :  0
    17 시 기준 이상치 :  336 , Boundary 이상치 :  0
    ======총  422 건 ======
    
    -------이상치 검출---------
    총 데이터 : 40016  이상치 :  636
    이상치 검출율 :  1.5893642542982807 %
    낮 기준 이상치 :  1.054578168732507 %
    밤 기준 이상치 :  0.5347860855657737 %


### AI037 / 의령1호


```python
pv_id = 'AI037'

# 해당 발전소 데이터 추출
df_tmp = df_gn[df_gn.PV_ID == pv_id]
df = df_tmp.copy()
df.drop(columns=['DETL_ADDR'], inplace = True)

# 발전소 데이터 요약정보 확인
print(df.STATS_VAL.describe())
print()

# 20시 부터 5시까지 일사량이 20 이상인 데이터 수
print("-------밤시간 이상치 확인---------")
night, df_night = check_stats_val(20, 5, 20, '>', df)
print()

# 6시부터 18시까지 일사량이 10 이하인 데이터 수
print("-------낮시간 이상치 확인---------")
daytime, df_day = check_stats_val(8, 17, 10, '<', df)
print()

# 이상치 검출율
print("-------이상치 검출---------")
print("총 데이터 :", df.shape[0], " 이상치 : ", night+daytime)
print("이상치 검출율 : ", ((night+daytime) / df.shape[0])*100, "%" )
print("낮 기준 이상치 : ", (daytime/ df.shape[0])*100, "%")
print("밤 기준 이상치 : ", (night/ df.shape[0])*100, "%")

# 이상치로 검출된 데이터 저장
df_sum = pd.concat([df_day, df_night]).sort_values(by=['DATE', 'TIME'], axis=0)
df_sum.to_csv('dataset/abnormal/' + pv_id + '_abnormal.csv', index=False, encoding="utf-8-sig")
```

    count     4437.000000
    mean      5032.862526
    std      12352.077616
    min       -789.818700
    25%          0.000000
    50%          0.000000
    75%          0.000000
    max      59743.250500
    Name: STATS_VAL, dtype: float64
    
    -------밤시간 이상치 확인---------
    시간 : [20, 21, 22, 23, 0, 1, 2, 3, 4, 5]
    20 시 기준 이상치 :  0 , Boundary 이상치 :  19
    21 시 기준 이상치 :  0 , Boundary 이상치 :  19
    22 시 기준 이상치 :  0 , Boundary 이상치 :  19
    23 시 기준 이상치 :  0 , Boundary 이상치 :  19
    0 시 기준 이상치 :  0 , Boundary 이상치 :  19
    1 시 기준 이상치 :  1 , Boundary 이상치 :  19
    2 시 기준 이상치 :  0 , Boundary 이상치 :  19
    3 시 기준 이상치 :  1 , Boundary 이상치 :  19
    4 시 기준 이상치 :  1 , Boundary 이상치 :  19
    5 시 기준 이상치 :  0 , Boundary 이상치 :  19
    ======총  193 건 ======
    
    -------낮시간 이상치 확인---------
    시간 : [8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
    8 시 기준 이상치 :  91 , Boundary 이상치 :  91
    9 시 기준 이상치 :  91 , Boundary 이상치 :  94
    10 시 기준 이상치 :  91 , Boundary 이상치 :  93
    11 시 기준 이상치 :  90 , Boundary 이상치 :  95
    12 시 기준 이상치 :  90 , Boundary 이상치 :  94
    13 시 기준 이상치 :  90 , Boundary 이상치 :  95
    14 시 기준 이상치 :  90 , Boundary 이상치 :  95
    15 시 기준 이상치 :  90 , Boundary 이상치 :  94
    16 시 기준 이상치 :  90 , Boundary 이상치 :  92
    17 시 기준 이상치 :  90 , Boundary 이상치 :  62
    ======총  1808 건 ======
    
    -------이상치 검출---------
    총 데이터 : 4437  이상치 :  2001
    이상치 검출율 :  45.09803921568628 %
    낮 기준 이상치 :  40.748253324318235 %
    밤 기준 이상치 :  4.349785891368041 %


### AI039 / 의령2호


```python
pv_id = 'AI039'

# 해당 발전소 데이터 추출
df_tmp = df_gn[df_gn.PV_ID == pv_id]
df = df_tmp.copy()
df.drop(columns=['DETL_ADDR'], inplace = True)

# 발전소 데이터 요약정보 확인
print(df.STATS_VAL.describe())
print()

# 20시 부터 5시까지 일사량이 20 이상인 데이터 수
print("-------밤시간 이상치 확인---------")
night, df_night = check_stats_val(20, 5, 20, '>', df)
print()

# 6시부터 18시까지 일사량이 10 이하인 데이터 수
print("-------낮시간 이상치 확인---------")
daytime, df_day = check_stats_val(8, 17, 10, '<', df)
print()

# 이상치 검출율
print("-------이상치 검출---------")
print("총 데이터 :", df.shape[0], " 이상치 : ", night+daytime)
print("이상치 검출율 : ", ((night+daytime) / df.shape[0])*100, "%" )
print("낮 기준 이상치 : ", (daytime/ df.shape[0])*100, "%")
print("밤 기준 이상치 : ", (night/ df.shape[0])*100, "%")

# 이상치로 검출된 데이터 저장
df_sum = pd.concat([df_day, df_night]).sort_values(by=['DATE', 'TIME'], axis=0)
df_sum.to_csv('dataset/abnormal/' + pv_id + '_abnormal.csv', index=False, encoding="utf-8-sig")
```

    count    4438.000000
    mean      160.350283
    std       252.747548
    min       -13.126400
    25%         0.000000
    50%         0.000000
    75%       273.735100
    max      1015.096400
    Name: STATS_VAL, dtype: float64
    
    -------밤시간 이상치 확인---------
    시간 : [20, 21, 22, 23, 0, 1, 2, 3, 4, 5]
    20 시 기준 이상치 :  1 , Boundary 이상치 :  18
    21 시 기준 이상치 :  1 , Boundary 이상치 :  18
    22 시 기준 이상치 :  1 , Boundary 이상치 :  17
    23 시 기준 이상치 :  1 , Boundary 이상치 :  18
    0 시 기준 이상치 :  1 , Boundary 이상치 :  16
    1 시 기준 이상치 :  1 , Boundary 이상치 :  16
    2 시 기준 이상치 :  1 , Boundary 이상치 :  17
    3 시 기준 이상치 :  1 , Boundary 이상치 :  17
    4 시 기준 이상치 :  1 , Boundary 이상치 :  16
    5 시 기준 이상치 :  1 , Boundary 이상치 :  16
    ======총  179 건 ======
    
    -------낮시간 이상치 확인---------
    시간 : [8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
    8 시 기준 이상치 :  10 , Boundary 이상치 :  0
    9 시 기준 이상치 :  9 , Boundary 이상치 :  0
    10 시 기준 이상치 :  9 , Boundary 이상치 :  0
    11 시 기준 이상치 :  8 , Boundary 이상치 :  0
    12 시 기준 이상치 :  8 , Boundary 이상치 :  0
    13 시 기준 이상치 :  8 , Boundary 이상치 :  0
    14 시 기준 이상치 :  7 , Boundary 이상치 :  0
    15 시 기준 이상치 :  8 , Boundary 이상치 :  0
    16 시 기준 이상치 :  9 , Boundary 이상치 :  0
    17 시 기준 이상치 :  37 , Boundary 이상치 :  17
    ======총  130 건 ======
    
    -------이상치 검출---------
    총 데이터 : 4438  이상치 :  309
    이상치 검출율 :  6.962595763857593 %
    낮 기준 이상치 :  2.9292474087426768 %
    밤 기준 이상치 :  4.033348355114916 %


## 4-4. 경상북도 지역 이상치 검출 수행


```python
# 경상북도 발전소 시간별 일사량 데이터
df_gb = df_new[df_new['DETL_ADDR'].str.contains('경상북도')]

# 경상북도 발전소 리스트 확인
df_gb.drop_duplicates(subset=['PV_ID']).reset_index(drop=True).drop(columns=['STATS_VAL', 'DATE','TIME'])
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>PV_ID</th>
      <th>AREA_ID</th>
      <th>PV_KOR_NM</th>
      <th>FCLTY_CPCTY</th>
      <th>DETL_ADDR</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>AI017</td>
      <td>1832384</td>
      <td>공제회 영주 발전소</td>
      <td>889.8000</td>
      <td>대한민국 경상북도 영주시 적서동 255-2</td>
    </tr>
  </tbody>
</table>
</div>



### AI017 / 공제회 영주 발전소


```python
pv_id = 'AI017'

# 해당 발전소 데이터 추출
df_tmp = df_gb[df_gb.PV_ID == pv_id]
df = df_tmp.copy()
df.drop(columns=['DETL_ADDR'], inplace = True)

# 발전소 데이터 요약정보 확인
print(df.STATS_VAL.describe())
print()

# 20시 부터 5시까지 일사량이 20 이상인 데이터 수
print("-------밤시간 이상치 확인---------")
night, df_night = check_stats_val(20, 5, 20, '>', df)
print()

# 6시부터 18시까지 일사량이 10 이하인 데이터 수
print("-------낮시간 이상치 확인---------")
daytime, df_day = check_stats_val(8, 17, 10, '<', df)
print()

# 이상치 검출율
print("-------이상치 검출---------")
print("총 데이터 :", df.shape[0], " 이상치 : ", night+daytime)
print("이상치 검출율 : ", ((night+daytime) / df.shape[0])*100, "%" )
print("낮 기준 이상치 : ", (daytime/ df.shape[0])*100, "%")
print("밤 기준 이상치 : ", (night/ df.shape[0])*100, "%")

# 이상치로 검출된 데이터 저장
df_sum = pd.concat([df_day, df_night]).sort_values(by=['DATE', 'TIME'], axis=0)
df_sum.to_csv('dataset/abnormal/' + pv_id + '_abnormal.csv', index=False, encoding="utf-8-sig")
```

    count    40476.000000
    mean       156.605349
    std        727.271780
    min       -437.502000
    25%          0.000000
    50%         11.295000
    75%        212.918975
    max      26057.502000
    Name: STATS_VAL, dtype: float64
    
    -------밤시간 이상치 확인---------
    시간 : [20, 21, 22, 23, 0, 1, 2, 3, 4, 5]
    20 시 기준 이상치 :  38 , Boundary 이상치 :  94
    21 시 기준 이상치 :  28 , Boundary 이상치 :  88
    22 시 기준 이상치 :  24 , Boundary 이상치 :  80
    23 시 기준 이상치 :  18 , Boundary 이상치 :  74
    0 시 기준 이상치 :  15 , Boundary 이상치 :  70
    1 시 기준 이상치 :  14 , Boundary 이상치 :  59
    2 시 기준 이상치 :  13 , Boundary 이상치 :  52
    3 시 기준 이상치 :  19 , Boundary 이상치 :  49
    4 시 기준 이상치 :  18 , Boundary 이상치 :  47
    5 시 기준 이상치 :  130 , Boundary 이상치 :  43
    ======총  973 건 ======
    
    -------낮시간 이상치 확인---------
    시간 : [8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
    8 시 기준 이상치 :  2 , Boundary 이상치 :  99
    9 시 기준 이상치 :  1 , Boundary 이상치 :  99
    10 시 기준 이상치 :  0 , Boundary 이상치 :  100
    11 시 기준 이상치 :  0 , Boundary 이상치 :  104
    12 시 기준 이상치 :  1 , Boundary 이상치 :  103
    13 시 기준 이상치 :  0 , Boundary 이상치 :  106
    14 시 기준 이상치 :  0 , Boundary 이상치 :  107
    15 시 기준 이상치 :  1 , Boundary 이상치 :  106
    16 시 기준 이상치 :  1 , Boundary 이상치 :  108
    17 시 기준 이상치 :  273 , Boundary 이상치 :  105
    ======총  1316 건 ======
    
    -------이상치 검출---------
    총 데이터 : 40476  이상치 :  2289
    이상치 검출율 :  5.655203083308628 %
    낮 기준 이상치 :  3.2513094179266724 %
    밤 기준 이상치 :  2.403893665381955 %


## 4-5. 충청북도 지역 이상치 검출 수행


```python
# 충청북도 발전소 시간별 일사량 데이터
df_cb = df_new[df_new['DETL_ADDR'].str.contains('충청북도')]

# 충청북도 발전소 리스트 확인
df_cb.drop_duplicates(subset=['PV_ID']).reset_index(drop=True).drop(columns=['STATS_VAL', 'DATE','TIME'])
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>PV_ID</th>
      <th>AREA_ID</th>
      <th>PV_KOR_NM</th>
      <th>FCLTY_CPCTY</th>
      <th>DETL_ADDR</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>AE004</td>
      <td>1846095</td>
      <td>탑프라</td>
      <td>1116.9000</td>
      <td>대한민국 충청북도 음성군 맹동면 쌍정리 748</td>
    </tr>
    <tr>
      <th>1</th>
      <td>AI026</td>
      <td>1842944</td>
      <td>지에프 영동 태양광발전소</td>
      <td>815.0000</td>
      <td>대한민국 충청북도 영동군 매곡면 괘방령로 730-20</td>
    </tr>
  </tbody>
</table>
</div>



### AE004 / 탑프라


```python
pv_id = 'AE004'

# 해당 발전소 데이터 추출
df_tmp = df_cb[df_cb.PV_ID == pv_id]
df = df_tmp.copy()
df.drop(columns=['DETL_ADDR'], inplace = True)

# 발전소 데이터 요약정보 확인
print(df.STATS_VAL.describe())
print()

# 20시 부터 5시까지 일사량이 20 이상인 데이터 수
print("-------밤시간 이상치 확인---------")
night, df_night = check_stats_val(20, 5, 20, '>', df)
print()

# 6시부터 18시까지 일사량이 10 이하인 데이터 수
print("-------낮시간 이상치 확인---------")
daytime, df_day = check_stats_val(8, 17, 10, '<', df)
print()

# 이상치 검출율
print("-------이상치 검출---------")
print("총 데이터 :", df.shape[0], " 이상치 : ", night+daytime)
print("이상치 검출율 : ", ((night+daytime) / df.shape[0])*100, "%" )
print("낮 기준 이상치 : ", (daytime/ df.shape[0])*100, "%")
print("밤 기준 이상치 : ", (night/ df.shape[0])*100, "%")

# 이상치로 검출된 데이터 저장
df_sum = pd.concat([df_day, df_night]).sort_values(by=['DATE', 'TIME'], axis=0)
df_sum.to_csv('dataset/abnormal/' + pv_id + '_abnormal.csv', index=False, encoding="utf-8-sig")
```

    count    23753.000000
    mean       122.496428
    std        200.067677
    min          0.000000
    25%          0.000000
    50%          0.316800
    75%        179.966700
    max        872.983200
    Name: STATS_VAL, dtype: float64
    
    -------밤시간 이상치 확인---------
    시간 : [20, 21, 22, 23, 0, 1, 2, 3, 4, 5]
    20 시 기준 이상치 :  0 , Boundary 이상치 :  0
    21 시 기준 이상치 :  0 , Boundary 이상치 :  0
    22 시 기준 이상치 :  0 , Boundary 이상치 :  0
    23 시 기준 이상치 :  0 , Boundary 이상치 :  0
    0 시 기준 이상치 :  0 , Boundary 이상치 :  0
    1 시 기준 이상치 :  0 , Boundary 이상치 :  0
    2 시 기준 이상치 :  0 , Boundary 이상치 :  0
    3 시 기준 이상치 :  0 , Boundary 이상치 :  0
    4 시 기준 이상치 :  0 , Boundary 이상치 :  0
    5 시 기준 이상치 :  7 , Boundary 이상치 :  0
    ======총  7 건 ======
    
    -------낮시간 이상치 확인---------
    시간 : [8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
    8 시 기준 이상치 :  78 , Boundary 이상치 :  0
    9 시 기준 이상치 :  66 , Boundary 이상치 :  0
    10 시 기준 이상치 :  66 , Boundary 이상치 :  0
    11 시 기준 이상치 :  67 , Boundary 이상치 :  0
    12 시 기준 이상치 :  67 , Boundary 이상치 :  0
    13 시 기준 이상치 :  67 , Boundary 이상치 :  0
    14 시 기준 이상치 :  68 , Boundary 이상치 :  0
    15 시 기준 이상치 :  72 , Boundary 이상치 :  0
    16 시 기준 이상치 :  80 , Boundary 이상치 :  0
    17 시 기준 이상치 :  300 , Boundary 이상치 :  0
    ======총  931 건 ======
    
    -------이상치 검출---------
    총 데이터 : 23753  이상치 :  938
    이상치 검출율 :  3.948974866332674 %
    낮 기준 이상치 :  3.919504904643624 %
    밤 기준 이상치 :  0.029469961689049803 %


### AI026 / 지에프 영동 태양광발전소


```python
pv_id = 'AI026'

# 해당 발전소 데이터 추출
df_tmp = df_cb[df_cb.PV_ID == pv_id]
df = df_tmp.copy()
df.drop(columns=['DETL_ADDR'], inplace = True)

# 발전소 데이터 요약정보 확인
print(df.STATS_VAL.describe())
print()

# 20시 부터 5시까지 일사량이 20 이상인 데이터 수
print("-------밤시간 이상치 확인---------")
night, df_night = check_stats_val(20, 5, 20, '>', df)
print()

# 6시부터 18시까지 일사량이 10 이하인 데이터 수
print("-------낮시간 이상치 확인---------")
daytime, df_day = check_stats_val(8, 17, 10, '<', df)
print()

# 이상치 검출율
print("-------이상치 검출---------")
print("총 데이터 :", df.shape[0], " 이상치 : ", night+daytime)
print("이상치 검출율 : ", ((night+daytime) / df.shape[0])*100, "%" )
print("낮 기준 이상치 : ", (daytime/ df.shape[0])*100, "%")
print("밤 기준 이상치 : ", (night/ df.shape[0])*100, "%")

# 이상치로 검출된 데이터 저장
df_sum = pd.concat([df_day, df_night]).sort_values(by=['DATE', 'TIME'], axis=0)
df_sum.to_csv('dataset/abnormal/' + pv_id + '_abnormal.csv', index=False, encoding="utf-8-sig")
```

    count    36615.000000
    mean       147.531697
    std        230.295382
    min          0.000000
    25%          0.438000
    50%          3.966300
    75%        229.837000
    max       1417.012100
    Name: STATS_VAL, dtype: float64
    
    -------밤시간 이상치 확인---------
    시간 : [20, 21, 22, 23, 0, 1, 2, 3, 4, 5]
    20 시 기준 이상치 :  22 , Boundary 이상치 :  1
    21 시 기준 이상치 :  24 , Boundary 이상치 :  0
    22 시 기준 이상치 :  24 , Boundary 이상치 :  0
    23 시 기준 이상치 :  26 , Boundary 이상치 :  0
    0 시 기준 이상치 :  24 , Boundary 이상치 :  0
    1 시 기준 이상치 :  27 , Boundary 이상치 :  0
    2 시 기준 이상치 :  30 , Boundary 이상치 :  0
    3 시 기준 이상치 :  33 , Boundary 이상치 :  0
    4 시 기준 이상치 :  34 , Boundary 이상치 :  0
    5 시 기준 이상치 :  36 , Boundary 이상치 :  0
    ======총  281 건 ======
    
    -------낮시간 이상치 확인---------
    시간 : [8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
    8 시 기준 이상치 :  68 , Boundary 이상치 :  2
    9 시 기준 이상치 :  56 , Boundary 이상치 :  1
    10 시 기준 이상치 :  56 , Boundary 이상치 :  1
    11 시 기준 이상치 :  55 , Boundary 이상치 :  0
    12 시 기준 이상치 :  53 , Boundary 이상치 :  2
    13 시 기준 이상치 :  57 , Boundary 이상치 :  1
    14 시 기준 이상치 :  55 , Boundary 이상치 :  1
    15 시 기준 이상치 :  59 , Boundary 이상치 :  1
    16 시 기준 이상치 :  77 , Boundary 이상치 :  0
    17 시 기준 이상치 :  463 , Boundary 이상치 :  1
    ======총  1009 건 ======
    
    -------이상치 검출---------
    총 데이터 : 36615  이상치 :  1290
    이상치 검출율 :  3.5231462515362555 %
    낮 기준 이상치 :  2.7557012153489007 %
    밤 기준 이상치 :  0.7674450361873548 %


## 4-6. 대전광역시 지역 이상치 검출 수행


```python
# 대전광역시 발전소 시간별 일사량 데이터
df_dj = df_new[df_new['DETL_ADDR'].str.contains('대전광역')]

# 대전광역시 발전소 리스트 확인
df_dj.drop_duplicates(subset=['PV_ID']).reset_index(drop=True).drop(columns=['STATS_VAL', 'DATE','TIME'])
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>PV_ID</th>
      <th>AREA_ID</th>
      <th>PV_KOR_NM</th>
      <th>FCLTY_CPCTY</th>
      <th>DETL_ADDR</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>AI016</td>
      <td>1835235</td>
      <td>공제회 신탄진 발전소</td>
      <td>825.4000</td>
      <td>대한민국 대전광역시 대덕구 평촌동 100</td>
    </tr>
  </tbody>
</table>
</div>



### AI016 / 지에프 영동 태양광발전소


```python
pv_id = 'AI016'

# 해당 발전소 데이터 추출
df_tmp = df_dj[df_dj.PV_ID == pv_id]
df = df_tmp.copy()
df.drop(columns=['DETL_ADDR'], inplace = True)

# 발전소 데이터 요약정보 확인
print(df.STATS_VAL.describe())
print()

# 20시 부터 5시까지 일사량이 20 이상인 데이터 수
print("-------밤시간 이상치 확인---------")
night, df_night = check_stats_val(20, 5, 20, '>', df)
print()

# 6시부터 18시까지 일사량이 10 이하인 데이터 수
print("-------낮시간 이상치 확인---------")
daytime, df_day = check_stats_val(8, 17, 10, '<', df)
print()

# 이상치 검출율
print("-------이상치 검출---------")
print("총 데이터 :", df.shape[0], " 이상치 : ", night+daytime)
print("이상치 검출율 : ", ((night+daytime) / df.shape[0])*100, "%" )
print("낮 기준 이상치 : ", (daytime/ df.shape[0])*100, "%")
print("밤 기준 이상치 : ", (night/ df.shape[0])*100, "%")

# 이상치로 검출된 데이터 저장
df_sum = pd.concat([df_day, df_night]).sort_values(by=['DATE', 'TIME'], axis=0)
df_sum.to_csv('dataset/abnormal/' + pv_id + '_abnormal.csv', index=False, encoding="utf-8-sig")
```

    count    40855.000000
    mean       241.473303
    std        373.973649
    min          0.000000
    25%          0.000000
    50%         41.096300
    75%        381.048200
    max       1750.002000
    Name: STATS_VAL, dtype: float64
    
    -------밤시간 이상치 확인---------
    시간 : [20, 21, 22, 23, 0, 1, 2, 3, 4, 5]
    20 시 기준 이상치 :  192 , Boundary 이상치 :  53
    21 시 기준 이상치 :  190 , Boundary 이상치 :  55
    22 시 기준 이상치 :  191 , Boundary 이상치 :  53
    23 시 기준 이상치 :  188 , Boundary 이상치 :  55
    0 시 기준 이상치 :  191 , Boundary 이상치 :  54
    1 시 기준 이상치 :  191 , Boundary 이상치 :  54
    2 시 기준 이상치 :  193 , Boundary 이상치 :  54
    3 시 기준 이상치 :  192 , Boundary 이상치 :  55
    4 시 기준 이상치 :  187 , Boundary 이상치 :  60
    5 시 기준 이상치 :  195 , Boundary 이상치 :  59
    ======총  2462 건 ======
    
    -------낮시간 이상치 확인---------
    시간 : [8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
    8 시 기준 이상치 :  3 , Boundary 이상치 :  67
    9 시 기준 이상치 :  1 , Boundary 이상치 :  68
    10 시 기준 이상치 :  0 , Boundary 이상치 :  87
    11 시 기준 이상치 :  0 , Boundary 이상치 :  105
    12 시 기준 이상치 :  0 , Boundary 이상치 :  103
    13 시 기준 이상치 :  0 , Boundary 이상치 :  97
    14 시 기준 이상치 :  0 , Boundary 이상치 :  86
    15 시 기준 이상치 :  1 , Boundary 이상치 :  87
    16 시 기준 이상치 :  9 , Boundary 이상치 :  74
    17 시 기준 이상치 :  314 , Boundary 이상치 :  63
    ======총  1165 건 ======
    
    -------이상치 검출---------
    총 데이터 : 40855  이상치 :  3627
    이상치 검출율 :  8.877738342920082 %
    낮 기준 이상치 :  2.851548158120181 %
    밤 기준 이상치 :  6.026190184799902 %


## 4-7. 경기도 지역 이상치 검출 수행


```python
# 경기도 발전소 시간별 일사량 데이터
df_kk = df_new[df_new['DETL_ADDR'].str.contains('경기도')]

# 경기도 발전소 리스트 확인
df_kk.drop_duplicates(subset=['PV_ID']).reset_index(drop=True).drop(columns=['STATS_VAL', 'DATE','TIME'])
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>PV_ID</th>
      <th>AREA_ID</th>
      <th>PV_KOR_NM</th>
      <th>FCLTY_CPCTY</th>
      <th>DETL_ADDR</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>AE016</td>
      <td>1839652</td>
      <td>그린 오산 태양광발전소</td>
      <td>1922.0000</td>
      <td>대한민국 경기도 오산시 부산동 34-3</td>
    </tr>
    <tr>
      <th>1</th>
      <td>AI024</td>
      <td>1843702</td>
      <td>지엘 이천 태양광발전소</td>
      <td>999.1800</td>
      <td>대한민국 경기도 이천시 마장면 이장로311번길 91</td>
    </tr>
  </tbody>
</table>
</div>



### AE016 / 그린 오산 태양광발전소


```python
pv_id = 'AE016'

# 해당 발전소 데이터 추출
df_tmp = df_kk[df_kk.PV_ID == pv_id]
df = df_tmp.copy()
df.drop(columns=['DETL_ADDR'], inplace = True)

# 발전소 데이터 요약정보 확인
print(df.STATS_VAL.describe())
print()

# 20시 부터 5시까지 일사량이 20 이상인 데이터 수
print("-------밤시간 이상치 확인---------")
night, df_night = check_stats_val(20, 5, 20, '>', df)
print()

# 6시부터 18시까지 일사량이 10 이하인 데이터 수
print("-------낮시간 이상치 확인---------")
daytime, df_day = check_stats_val(8, 17, 10, '<', df)
print()

# 이상치 검출율
print("-------이상치 검출---------")
print("총 데이터 :", df.shape[0], " 이상치 : ", night+daytime)
print("이상치 검출율 : ", ((night+daytime) / df.shape[0])*100, "%" )
print("낮 기준 이상치 : ", (daytime/ df.shape[0])*100, "%")
print("밤 기준 이상치 : ", (night/ df.shape[0])*100, "%")

# 이상치로 검출된 데이터 저장
df_sum = pd.concat([df_day, df_night]).sort_values(by=['DATE', 'TIME'], axis=0)
df_sum.to_csv('dataset/abnormal/' + pv_id + '_abnormal.csv', index=False, encoding="utf-8-sig")
```

    count    39644.000000
    mean       153.784741
    std        232.672328
    min          0.000000
    25%          0.876000
    50%          5.032350
    75%        247.276850
    max        947.822200
    Name: STATS_VAL, dtype: float64
    
    -------밤시간 이상치 확인---------
    시간 : [20, 21, 22, 23, 0, 1, 2, 3, 4, 5]
    20 시 기준 이상치 :  23 , Boundary 이상치 :  0
    21 시 기준 이상치 :  23 , Boundary 이상치 :  0
    22 시 기준 이상치 :  23 , Boundary 이상치 :  0
    23 시 기준 이상치 :  23 , Boundary 이상치 :  0
    0 시 기준 이상치 :  23 , Boundary 이상치 :  0
    1 시 기준 이상치 :  23 , Boundary 이상치 :  0
    2 시 기준 이상치 :  23 , Boundary 이상치 :  0
    3 시 기준 이상치 :  23 , Boundary 이상치 :  0
    4 시 기준 이상치 :  23 , Boundary 이상치 :  0
    5 시 기준 이상치 :  24 , Boundary 이상치 :  0
    ======총  231 건 ======
    
    -------낮시간 이상치 확인---------
    시간 : [8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
    8 시 기준 이상치 :  23 , Boundary 이상치 :  0
    9 시 기준 이상치 :  5 , Boundary 이상치 :  0
    10 시 기준 이상치 :  2 , Boundary 이상치 :  0
    11 시 기준 이상치 :  1 , Boundary 이상치 :  0
    12 시 기준 이상치 :  0 , Boundary 이상치 :  0
    13 시 기준 이상치 :  0 , Boundary 이상치 :  0
    14 시 기준 이상치 :  1 , Boundary 이상치 :  0
    15 시 기준 이상치 :  11 , Boundary 이상치 :  0
    16 시 기준 이상치 :  29 , Boundary 이상치 :  0
    17 시 기준 이상치 :  442 , Boundary 이상치 :  0
    ======총  514 건 ======
    
    -------이상치 검출---------
    총 데이터 : 39644  이상치 :  745
    이상치 검출율 :  1.879225103420442 %
    낮 기준 이상치 :  1.2965391988699424 %
    밤 기준 이상치 :  0.5826859045504994 %


### AI024 / 지엘 이천 태양광발전소


```python
pv_id = 'AI024'

# 해당 발전소 데이터 추출
df_tmp = df_kk[df_kk.PV_ID == pv_id]
df = df_tmp.copy()
df.drop(columns=['DETL_ADDR'], inplace = True)

# 발전소 데이터 요약정보 확인
print(df.STATS_VAL.describe())
print()

# 20시 부터 5시까지 일사량이 20 이상인 데이터 수
print("-------밤시간 이상치 확인---------")
night, df_night = check_stats_val(20, 5, 20, '>', df)
print()

# 6시부터 18시까지 일사량이 10 이하인 데이터 수
print("-------낮시간 이상치 확인---------")
daytime, df_day = check_stats_val(8, 17, 10, '<', df)
print()

# 이상치 검출율
print("-------이상치 검출---------")
print("총 데이터 :", df.shape[0], " 이상치 : ", night+daytime)
print("이상치 검출율 : ", ((night+daytime) / df.shape[0])*100, "%" )
print("낮 기준 이상치 : ", (daytime/ df.shape[0])*100, "%")
print("밤 기준 이상치 : ", (night/ df.shape[0])*100, "%")

# 이상치로 검출된 데이터 저장
df_sum = pd.concat([df_day, df_night]).sort_values(by=['DATE', 'TIME'], axis=0)
df_sum.to_csv('dataset/abnormal/' + pv_id + '_abnormal.csv', index=False, encoding="utf-8-sig")
```

    count    39962.000000
    mean       163.705334
    std        256.795834
    min          0.000000
    25%          1.441900
    50%          4.267350
    75%        249.824650
    max       1086.991600
    Name: STATS_VAL, dtype: float64
    
    -------밤시간 이상치 확인---------
    시간 : [20, 21, 22, 23, 0, 1, 2, 3, 4, 5]
    20 시 기준 이상치 :  0 , Boundary 이상치 :  0
    21 시 기준 이상치 :  0 , Boundary 이상치 :  0
    22 시 기준 이상치 :  0 , Boundary 이상치 :  0
    23 시 기준 이상치 :  0 , Boundary 이상치 :  0
    0 시 기준 이상치 :  0 , Boundary 이상치 :  0
    1 시 기준 이상치 :  0 , Boundary 이상치 :  0
    2 시 기준 이상치 :  0 , Boundary 이상치 :  0
    3 시 기준 이상치 :  0 , Boundary 이상치 :  0
    4 시 기준 이상치 :  0 , Boundary 이상치 :  0
    5 시 기준 이상치 :  13 , Boundary 이상치 :  0
    ======총  13 건 ======
    
    -------낮시간 이상치 확인---------
    시간 : [8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
    8 시 기준 이상치 :  33 , Boundary 이상치 :  0
    9 시 기준 이상치 :  7 , Boundary 이상치 :  0
    10 시 기준 이상치 :  4 , Boundary 이상치 :  0
    11 시 기준 이상치 :  0 , Boundary 이상치 :  0
    12 시 기준 이상치 :  0 , Boundary 이상치 :  0
    13 시 기준 이상치 :  0 , Boundary 이상치 :  0
    14 시 기준 이상치 :  4 , Boundary 이상치 :  0
    15 시 기준 이상치 :  8 , Boundary 이상치 :  0
    16 시 기준 이상치 :  48 , Boundary 이상치 :  0
    17 시 기준 이상치 :  505 , Boundary 이상치 :  0
    ======총  609 건 ======
    
    -------이상치 검출---------
    총 데이터 : 39962  이상치 :  622
    이상치 검출율 :  1.5564786547219858 %
    낮 기준 이상치 :  1.5239477503628447 %
    밤 기준 이상치 :  0.03253090435914119 %


## 4-8. 강원도 지역 이상치 검출 수행


```python
# 강원도 발전소 시간별 일사량 데이터
df_kw = df_new[df_new['DETL_ADDR'].str.contains('강원도')]

# 강원도 발전소 리스트 확인
df_kw.drop_duplicates(subset=['PV_ID']).reset_index(drop=True).drop(columns=['STATS_VAL', 'DATE','TIME'])
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>PV_ID</th>
      <th>AREA_ID</th>
      <th>PV_KOR_NM</th>
      <th>FCLTY_CPCTY</th>
      <th>DETL_ADDR</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>AA003</td>
      <td>1832257</td>
      <td>㈜영월에너지스테이션 제2공구</td>
      <td>19060.1100</td>
      <td>대한민국 강원도 영월군 남면 창원리 산2</td>
    </tr>
    <tr>
      <th>1</th>
      <td>AA004</td>
      <td>1832257</td>
      <td>㈜영월에너지스테이션 제3공구</td>
      <td>11528.8200</td>
      <td>대한민국 강원도 영월군 남면 연당리 산252</td>
    </tr>
    <tr>
      <th>2</th>
      <td>AE024</td>
      <td>1832257</td>
      <td>㈜영월에너지스테이션 제1공구</td>
      <td>8326.8000</td>
      <td>대한민국 강원도 영월군 남면 연당리 산238</td>
    </tr>
  </tbody>
</table>
</div>



### AA003 / ㈜영월에너지스테이션 제2공구


```python
pv_id = 'AA003'

# 해당 발전소 데이터 추출
df_tmp = df_kw[df_kw.PV_ID == pv_id]
df = df_tmp.copy()
df.drop(columns=['DETL_ADDR'], inplace = True)

# 발전소 데이터 요약정보 확인
print(df.STATS_VAL.describe())
print()

# 20시 부터 5시까지 일사량이 20 이상인 데이터 수
print("-------밤시간 이상치 확인---------")
night, df_night = check_stats_val(20, 5, 20, '>', df)
print()

# 6시부터 18시까지 일사량이 10 이하인 데이터 수
print("-------낮시간 이상치 확인---------")
daytime, df_day = check_stats_val(8, 17, 10, '<', df)
print()

# 이상치 검출율
print("-------이상치 검출---------")
print("총 데이터 :", df.shape[0], " 이상치 : ", night+daytime)
print("이상치 검출율 : ", ((night+daytime) / df.shape[0])*100, "%" )
print("낮 기준 이상치 : ", (daytime/ df.shape[0])*100, "%")
print("밤 기준 이상치 : ", (night/ df.shape[0])*100, "%")

# 이상치로 검출된 데이터 저장
df_sum = pd.concat([df_day, df_night]).sort_values(by=['DATE', 'TIME'], axis=0)
df_sum.to_csv('dataset/abnormal/' + pv_id + '_abnormal.csv', index=False, encoding="utf-8-sig")
```

    count    23546.000000
    mean       792.280803
    std       4982.237124
    min         -5.583600
    25%          0.000000
    50%          0.000000
    75%        286.258775
    max      65535.000000
    Name: STATS_VAL, dtype: float64
    
    -------밤시간 이상치 확인---------
    시간 : [20, 21, 22, 23, 0, 1, 2, 3, 4, 5]
    20 시 기준 이상치 :  9 , Boundary 이상치 :  143
    21 시 기준 이상치 :  9 , Boundary 이상치 :  141
    22 시 기준 이상치 :  9 , Boundary 이상치 :  141
    23 시 기준 이상치 :  8 , Boundary 이상치 :  140
    0 시 기준 이상치 :  10 , Boundary 이상치 :  138
    1 시 기준 이상치 :  8 , Boundary 이상치 :  138
    2 시 기준 이상치 :  8 , Boundary 이상치 :  138
    3 시 기준 이상치 :  8 , Boundary 이상치 :  138
    4 시 기준 이상치 :  8 , Boundary 이상치 :  139
    5 시 기준 이상치 :  34 , Boundary 이상치 :  127
    ======총  1494 건 ======
    
    -------낮시간 이상치 확인---------
    시간 : [8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
    8 시 기준 이상치 :  432 , Boundary 이상치 :  122
    9 시 기준 이상치 :  433 , Boundary 이상치 :  123
    10 시 기준 이상치 :  433 , Boundary 이상치 :  125
    11 시 기준 이상치 :  433 , Boundary 이상치 :  125
    12 시 기준 이상치 :  434 , Boundary 이상치 :  125
    13 시 기준 이상치 :  432 , Boundary 이상치 :  125
    14 시 기준 이상치 :  433 , Boundary 이상치 :  125
    15 시 기준 이상치 :  431 , Boundary 이상치 :  123
    16 시 기준 이상치 :  438 , Boundary 이상치 :  121
    17 시 기준 이상치 :  523 , Boundary 이상치 :  122
    ======총  5658 건 ======
    
    -------이상치 검출---------
    총 데이터 : 23546  이상치 :  7152
    이상치 검출율 :  30.374585916928567 %
    낮 기준 이상치 :  24.029559160791642 %
    밤 기준 이상치 :  6.345026756136924 %


### AA004 / ㈜영월에너지스테이션 제3공구


```python
pv_id = 'AA004'

# 해당 발전소 데이터 추출
df_tmp = df_kw[df_kw.PV_ID == pv_id]
df = df_tmp.copy()
df.drop(columns=['DETL_ADDR'], inplace = True)

# 발전소 데이터 요약정보 확인
print(df.STATS_VAL.describe())
print()

# 20시 부터 5시까지 일사량이 20 이상인 데이터 수
print("-------밤시간 이상치 확인---------")
night, df_night = check_stats_val(20, 5, 20, '>', df)
print()

# 6시부터 18시까지 일사량이 10 이하인 데이터 수
print("-------낮시간 이상치 확인---------")
daytime, df_day = check_stats_val(8, 17, 10, '<', df)
print()

# 이상치 검출율
print("-------이상치 검출---------")
print("총 데이터 :", df.shape[0], " 이상치 : ", night+daytime)
print("이상치 검출율 : ", ((night+daytime) / df.shape[0])*100, "%" )
print("낮 기준 이상치 : ", (daytime/ df.shape[0])*100, "%")
print("밤 기준 이상치 : ", (night/ df.shape[0])*100, "%")

# 이상치로 검출된 데이터 저장
df_sum = pd.concat([df_day, df_night]).sort_values(by=['DATE', 'TIME'], axis=0)
df_sum.to_csv('dataset/abnormal/' + pv_id + '_abnormal.csv', index=False, encoding="utf-8-sig")
```

    count    27672.000000
    mean       444.593067
    std       1102.727663
    min         -6.983900
    25%          0.834700
    50%         35.416900
    75%        582.075000
    max      61163.867000
    Name: STATS_VAL, dtype: float64
    
    -------밤시간 이상치 확인---------
    시간 : [20, 21, 22, 23, 0, 1, 2, 3, 4, 5]
    20 시 기준 이상치 :  11 , Boundary 이상치 :  124
    21 시 기준 이상치 :  12 , Boundary 이상치 :  125
    22 시 기준 이상치 :  11 , Boundary 이상치 :  125
    23 시 기준 이상치 :  12 , Boundary 이상치 :  122
    0 시 기준 이상치 :  11 , Boundary 이상치 :  119
    1 시 기준 이상치 :  12 , Boundary 이상치 :  119
    2 시 기준 이상치 :  13 , Boundary 이상치 :  118
    3 시 기준 이상치 :  12 , Boundary 이상치 :  119
    4 시 기준 이상치 :  12 , Boundary 이상치 :  119
    5 시 기준 이상치 :  61 , Boundary 이상치 :  119
    ======총  1376 건 ======
    
    -------낮시간 이상치 확인---------
    시간 : [8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
    8 시 기준 이상치 :  33 , Boundary 이상치 :  119
    9 시 기준 이상치 :  32 , Boundary 이상치 :  120
    10 시 기준 이상치 :  32 , Boundary 이상치 :  122
    11 시 기준 이상치 :  33 , Boundary 이상치 :  122
    12 시 기준 이상치 :  32 , Boundary 이상치 :  122
    13 시 기준 이상치 :  32 , Boundary 이상치 :  122
    14 시 기준 이상치 :  32 , Boundary 이상치 :  121
    15 시 기준 이상치 :  34 , Boundary 이상치 :  119
    16 시 기준 이상치 :  37 , Boundary 이상치 :  118
    17 시 기준 이상치 :  249 , Boundary 이상치 :  120
    ======총  1751 건 ======
    
    -------이상치 검출---------
    총 데이터 : 27672  이상치 :  3127
    이상치 검출율 :  11.30023128071697 %
    낮 기준 이상치 :  6.3276958658571845 %
    밤 기준 이상치 :  4.972535414859786 %


### AE024 / ㈜영월에너지스테이션 제2공구


```python
pv_id = 'AE024'

# 해당 발전소 데이터 추출
df_tmp = df_kw[df_kw.PV_ID == pv_id]
df = df_tmp.copy()
df.drop(columns=['DETL_ADDR'], inplace = True)

# 발전소 데이터 요약정보 확인
print(df.STATS_VAL.describe())
print()

# 20시 부터 5시까지 일사량이 20 이상인 데이터 수
print("-------밤시간 이상치 확인---------")
night, df_night = check_stats_val(20, 5, 20, '>', df)
print()

# 6시부터 18시까지 일사량이 10 이하인 데이터 수
print("-------낮시간 이상치 확인---------")
daytime, df_day = check_stats_val(8, 17, 10, '<', df)
print()

# 이상치 검출율
print("-------이상치 검출---------")
print("총 데이터 :", df.shape[0], " 이상치 : ", night+daytime)
print("이상치 검출율 : ", ((night+daytime) / df.shape[0])*100, "%" )
print("낮 기준 이상치 : ", (daytime/ df.shape[0])*100, "%")
print("밤 기준 이상치 : ", (night/ df.shape[0])*100, "%")

# 이상치로 검출된 데이터 저장
df_sum = pd.concat([df_day, df_night]).sort_values(by=['DATE', 'TIME'], axis=0)
df_sum.to_csv('dataset/abnormal/' + pv_id + '_abnormal.csv', index=False, encoding="utf-8-sig")
```

    count    28234.000000
    mean       610.542061
    std       3081.717892
    min         -4.415700
    25%         -0.350600
    50%         41.741550
    75%        609.245375
    max      65534.966700
    Name: STATS_VAL, dtype: float64
    
    -------밤시간 이상치 확인---------
    시간 : [20, 21, 22, 23, 0, 1, 2, 3, 4, 5]
    20 시 기준 이상치 :  9 , Boundary 이상치 :  139
    21 시 기준 이상치 :  9 , Boundary 이상치 :  140
    22 시 기준 이상치 :  9 , Boundary 이상치 :  139
    23 시 기준 이상치 :  10 , Boundary 이상치 :  138
    0 시 기준 이상치 :  11 , Boundary 이상치 :  135
    1 시 기준 이상치 :  10 , Boundary 이상치 :  136
    2 시 기준 이상치 :  9 , Boundary 이상치 :  137
    3 시 기준 이상치 :  11 , Boundary 이상치 :  133
    4 시 기준 이상치 :  10 , Boundary 이상치 :  133
    5 시 기준 이상치 :  45 , Boundary 이상치 :  123
    ======총  1486 건 ======
    
    -------낮시간 이상치 확인---------
    시간 : [8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
    8 시 기준 이상치 :  10 , Boundary 이상치 :  122
    9 시 기준 이상치 :  5 , Boundary 이상치 :  123
    10 시 기준 이상치 :  4 , Boundary 이상치 :  125
    11 시 기준 이상치 :  4 , Boundary 이상치 :  125
    12 시 기준 이상치 :  3 , Boundary 이상치 :  125
    13 시 기준 이상치 :  3 , Boundary 이상치 :  125
    14 시 기준 이상치 :  3 , Boundary 이상치 :  125
    15 시 기준 이상치 :  5 , Boundary 이상치 :  123
    16 시 기준 이상치 :  12 , Boundary 이상치 :  121
    17 시 기준 이상치 :  276 , Boundary 이상치 :  122
    ======총  1561 건 ======
    
    -------이상치 검출---------
    총 데이터 : 28234  이상치 :  3047
    이상치 검출율 :  10.791952964510873 %
    낮 기준 이상치 :  5.528795069774032 %
    밤 기준 이상치 :  5.263157894736842 %

