import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# 1. 웹페이지 기본 설정
st.set_page_config(
    page_title="미국 주요 주식 수익률 비교기",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. 타이틀 및 앱 소개
st.title("🇺🇸 미국 주요 주식 & 지수 수익률 비교 분석기")
st.markdown("""
당곡고등학교 학생 여러분 반갑습니다! 첫 번째 코드에 등장했던 **미국의 대표 기술주 4종**과 **시장 대표 지수 2종**만을 집중 비교하는 대시보드입니다.
세계 금융의 중심인 미국 시장의 흐름과 개별 주식 vs 지수의 수익률 차이를 분석해 봅시다.
""")

# 3. 첫 번째 코드에 있던 미국 주식 및 지수 정보 매핑 사전
us_stocks = {
    "애플 (AAPL)": "AAPL",
    "마이크로소프트 (MSFT)": "MSFT",
    "테슬라 (TSLA)": "TSLA",
    "엔비디아 (NVDA)": "NVDA",
    "S&P 500 지수 (SPY)": "SPY",
    "나스닥 100 지수 (QQQ)": "QQQ"
}

# 4. 사이드바 설정 (사용자 입력 컨트롤러)
st.sidebar.header("⚙️ 분석 옵션 설정")

# 비교할 주식 선택 (기본값으로 애플, 테슬라, S&P 500 지수가 선택되도록 설정)
selected_stock_names = st.sidebar.multiselect(
    "비교할 주식 및 지수를 선택하세요 (복수 선택 가능):",
    options=list(us_stocks.keys()),
    default=["애플 (AAPL)", "테슬라 (TSLA)", "S&P 500 지수 (SPY)"]
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
                # 수정 종가(Adj Close) 사용
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
    st.warning("⚠️ 왼쪽 사이드바에서 비교할 미국 주식을 최소 하나 이상 선택해 주세요!")
else:
    # 선택된 주식 정보 필터링
    selected_tickers = {name: us_stocks[name] for name in selected_stock_names}
    
    with st.spinner("야후 파이낸스로부터 미국 금융 데이터를 안전하게 불러오는 중..."):
        df = load_data(selected_tickers, start_date, end_date)
        
    if df.empty:
        st.error("불러온 데이터가 없습니다. 선택하신 주식이나 날짜 범위를 다시 확인해 주세요.")
    else:
        # 결측치를 직전 거래일 주가로 보완 (미국 시장 내 소규모 거래 정지 등 대비)
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
                labels={'value': '누적 수익률 (%)', 'Date': '날짜', 'variable': '자산명'},
                title="시간 경과에 따른 누적 수익률 (%)"
            )
            fig.update_layout(
                hovermode="x unified",  # 마우스를 대면 모든 자산의 수치가 한눈에 보임
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            st.subheader("📊 핵심 지표 요약")
            st.write("조회 기간 마지막 거래일 기준 최종 성과입니다.")
            
            summary_list = []
            for col in df_return.columns:
                start_price = df[col].iloc[0]
                end_price = df[col].iloc[-1]
                total_return = df_return[col].iloc[-1]
                
                # 미국 주식이므로 달러($) 기호와 센트 단위(소수점 둘째 자리) 적용
                summary_list.append({
                    "자산명": col,
                    "시작일 가격": f"${start_price:,.2f}",
                    "종료일 가격": f"${end_price:,.2f}",
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
1. **개별 종목 vs 시장 지수 (ETF):**
   - **지수(SPY, QQQ)**의 그래프 흐름과 **개별 주식(AAPL, TSLA, NVDA, MSFT)**의 그래프 흐름을 비교해 보세요. 
   - 개별 주식들의 등락 폭(변동성)이 지수보다 훨씬 크거나 작게 나타나는 이유는 무엇일까요? '분산 투자'와 '포트폴리오 효과'라는 경제학 개념과 연결해 탐구해 봅시다.
2. **트렌드 주도주 분석:**
   - 최근 1년간 **엔비디아(NVDA)**와 **나스닥 100 지수(QQQ)**의 수익률을 비교해 보세요. 최근 인공지능(AI) 산업의 성장과 엔비디아의 주가 움직임이 전체 기술주 중심 지수(QQQ)에 어떤 영향을 주었을지 이야기해 봅시다.
""")
