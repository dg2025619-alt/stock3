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
            st.error(f"{name} 데이터를 가져
        
