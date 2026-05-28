import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# 1. 웹페이지 기본 설정
st.set_page_config(
    page_title="국내 4대 주식 수익률 비교기",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. 타이틀 및 앱 소개
st.title("🇰🇷 국내 주요 4대 기업 주식 수익률 비교 분석기")
st.markdown("""
당곡고등학교 친구들 반갑습니다! 첫 번째 코드에 등장했던 **삼성전자, SK하이닉스, NAVER, 카카오** 4대 기업만을 집중 비교하는 대시보드입니다.
서로 다른 주가 규모를 가진 기업들의 **누적 수익률(%)**을 직관적으로 확인해 봅시다.
""")

# 3. 첫 번째 코드에 있던 국내 주식 정보 매핑 사전
korean_stocks = {
    "삼성전자 (KS)": "005930.KS",
    "SK하이닉스 (KS)": "000660.KS",
    "NAVER (KS)": "003542.KS",
    "카카오 (KS)": "035720.KS"
}

# 4. 사이드바 설정 (사용자 입력 컨트롤러)
st.sidebar.header("⚙️ 분석 옵션 설정")

# 비교할 주식 선택 (기본값으로 모두 선택되어 있도록 지정)
selected_stock_names = st.sidebar.multiselect(
    "비교할 주식을 선택하세요 (복수 선택 가능):",
    options=list(korean_stocks.keys()),
    default=list(korean_stocks.keys())
)

# 날짜 범위 설정 (기본값: 최근 1년)
start_date = st.sidebar.date_input("조회 시작일", datetime.now() - timedelta(days=365))
end_date = st.sidebar.date_input("조회 종료일", datetime.now())

# 5. yfinance 데이터 수집 함수 (캐싱 처리)
@st.cache_data
def load_data(tickers, start, end):
    data = pd.DataFrame()
    for name, ticker in tickers.items():
        try:
            ticker_df = yf.download(ticker, start=start, end=end)
            if not ticker_df.empty:
                # 수정 종가(Adj Close)를 사용하여 배당 및 분할 등이 반영된 가치 계산
                if 'Adj Close' in ticker_df.columns:
                    series = ticker_df['Adj Close']
                else:
                    series = ticker_df['Close']
                
                # multi-index 처리 방지
                if isinstance(series, pd.DataFrame):
                    series = series.iloc[:, 0]
                
                data[name] = series
        except Exception as e:
            st.error(f"{name} 데이터를 가져오는 중 오류가 발생했습니다: {e}")
    return data

# 6. 메인 로직 실행
if not selected_stock_names:
    st.warning("⚠️ 왼쪽 사이드바에서 비교할 국내 주식을 최소 하나 이상 선택해 주세요!")
else:
    # 선택된 주식 정보 필터링
    selected_tickers = {name: korean_stocks[name] for name in selected_stock_names}
    
    with st.spinner("야후 파이낸스로부터 국내 주가 데이터를 안전하게 불러오는 중..."):
        df = load_data(selected_tickers, start_date, end_date)
        
    if df.empty:
        st.error("불러온 데이터가 없습니다. 선택하신 주식이나 날짜 범위를 다시 확인해 주세요.")
    else:
        # 공휴일 및 휴장일 결측치를 직전 거래일 주가로 보완
        df = df.ffill().bfill()
        
        # 💡 누적 수익률 계산 공식: ((현재 주가 / 시작일 주가) - 1) * 100
        df_return = (df / df.iloc[0] - 1) * 100
        
        # 화면 레이아웃 분할 (왼쪽: 차트, 오른쪽: 요약 표)
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader("📈 선택 기간 누적 수익률 비교 추이")
            
            # Plotly Express를 활용한 인터랙티브 선그래프 시각화
            fig = px.line(
                df_return, 
                x=df_return.index, 
                y=df_return.columns,
                labels={'value': '누적 수익률 (%)', 'Date': '날짜', 'variable': '기업명'},
                title="시간 경과에 따른 누적 수익률 (%)"
            )
            fig.update_layout(
                hovermode="x unified",  # 마우스를 대면 모든 종목 수치가 한눈에 보임
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            st.subheader("📊 핵심 지표 요약")
            st.write("조회 기간 마지막 날 기준 성과입니다.")
            
            summary_list = []
            for col in df_return.columns:
                start_price = df[col].iloc[0]
                end_price = df[col].iloc[-1]
                total_return = df_return[col].iloc[-1]
                
                summary_list.append({
                    "기업명": col,
                    "시작일 가격": f"{int(start_price):,} 원",
                    "종료일 가격": f"{int(end_price):,} 원",
                    "최종 수익률": f"{total_return:+.2f}%"
                })
                
            summary_df = pd.DataFrame(summary_list)
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
            
        # 7. 세부 원본 데이터 보기
        with st.expander("🔍 날짜별 실제 수정 종가 원본 데이터 보기"):
            st.dataframe(df)

# 당곡고 학생들을 위한 스스로 생각하기 영역
st.markdown("""
---
### 💡 스스로 탐구하고 생각해보는 질문 목록
1. **업종별 차이 분석:** 
   - 우리 코드 속 주식은 **제조/반도체 대장주**(삼성전자, SK하이닉스)와 **IT 플랫폼 대장주**(NAVER, 카카오)로 묶어볼 수 있습니다. 
   - 최근 1년간 반도체 그룹과 플랫폼 그룹 중 어느 업종의 누적 수익률이 더 좋았나요? 그 시기 한국 및 글로벌 경제 트렌드와 연결지어 설명해보세요.
2. **동조화 현상(Coupling):**
   - 삼성전자와 SK하이닉스 두 그래프의 흐름이 서로 얼마나 닮아 있는지(또는 다른지) 관찰해 보세요. 경쟁 관계인 두 기업의 주가가 비슷하게 움직이는 이유에 대해 반도체 산업의 구조적 특성으로 분석해볼 수 있을까요?
""")
