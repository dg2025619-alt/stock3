import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# 1. 웹페이지 기본 설정
st.set_page_config(
    page_title="국내 주식 수익률 분석기",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. 타이틀 및 앱 소개
st.title("🇰🇷 대한민국 대표 주식 수익률 비교 분석기")
st.markdown("""
당곡고등학교 학생 여러분을 위한 **국내 주식 전용 데이터 분석기**입니다. 
코스피와 코스닥의 주요 기업들의 주가 데이터를 시각화하고, 서로 다른 주가를 가진 기업들의 **누적 수익률(%)**을 공평하게 비교해 봅시다.
""")

# 3. 대표적인 국내 주식 정보 매핑 사전
# 코스피는 .KS, 코스닥은 .KQ를 붙여야 yfinance에서 인식합니다.
korean_stocks = {
    "삼성전자 (KOSPI)": "005930.KS",
    "SK하이닉스 (KOSPI)": "000660.KS",
    "현대차 (KOSPI)": "005380.KS",
    "LG에너지솔루션 (KOSPI)": "373220.KS",
    "NAVER (KOSPI)": "003542.KS",
    "카카오 (KOSPI)": "035720.KS",
    "에코프로비엠 (KOSDAQ)": "247540.KQ",
    "알테오젠 (KOSDAQ)": "196170.KQ",
    "셀트리온 (KOSPI)": "068270.KS"
}

# 4. 사이드바 설정 (사용자 입력 컨트롤러)
st.sidebar.header("⚙️ 분석 및 종목 설정")

# (선택 기능 1) 기본 제공 종목 다중 선택
selected_stock_names = st.sidebar.multiselect(
    "비교할 대표 종목을 선택하세요:",
    options=list(korean_stocks.keys()),
    default=["삼성전자 (KOSPI)", "SK하이닉스 (KOSPI)", "카카오 (KOSPI)"]
)

# (선택 기능 2) 직접 종목코드 입력하여 추가하기 (학생들의 주체적 탐구 유도!)
st.sidebar.subheader("🔍 종목 직접 추가하기")
custom_name = st.sidebar.text_input("추가할 종목 이름 (예: 기아)", value="")
custom_code = st.sidebar.text_input("종목 코드 6자리 (예: 000270)", value="")
market_type = st.sidebar.selectbox("시장 선택", ["코스피 (.KS)", "코스닥 (.KQ)"])

# 날짜 범위 설정 (기본값: 최근 6개월)
start_date = st.sidebar.date_input("조회 시작일", datetime.now() - timedelta(days=180))
end_date = st.sidebar.date_input("조회 종료일", datetime.now())

# 5. 사용자 입력 종목 처리 및 데이터 다운로드 사전 구성
active_stocks = {}
for name in selected_stock_names:
    active_stocks[name] = korean_stocks[name]

# 직접 입력한 종목이 있다면 딕셔너리에 추가
if custom_name and custom_code:
    suffix = ".KS" if "코스피" in market_type else ".KQ"
    full_ticker = f"{custom_code.strip()}{suffix}"
    custom_label = f"{custom_name} (사용자 추가)"
    active_stocks[custom_label] = full_ticker

# 6. 데이터 수집 함수 (캐싱 적용)
@st.cache_data
def load_korean_data(tickers, start, end):
    data = pd.DataFrame()
    for name, ticker in tickers.items():
        try:
            # 주가 데이터 수집
            ticker_df = yf.download(ticker, start=start, end=end)
            if not ticker_df.empty:
                # 한국 주식은 배당락, 권리락 등이 있으므로 수정 종가(Adj Close)를 사용하는 것이 정확합니다.
                if 'Adj Close' in ticker_df.columns:
                    series = ticker_df['Adj Close']
                else:
                    series = ticker_df['Close']
                
                # Multi-index 처리 방지
                if isinstance(series, pd.DataFrame):
                    series = series.iloc[:, 0]
                    
                data[name] = series
        except Exception as e:
            st.error(f"'{name}' 데이터를 가져오는 중 오류가 발생했습니다. 종목코드가 올바른지 확인해 주세요. 오류: {e}")
    return data

# 7. 메인 화면 로직 실행
if not active_stocks:
    st.info("💡 왼쪽 사이드바에서 비교할 종목을 선택하거나 직접 입력해 주세요!")
else:
    with st.spinner("한국 거래소 주가 데이터를 가져오는 중..."):
        df = load_korean_data(active_stocks, start_date, end_date)
        
    if df.empty:
        st.error("데이터를 불러오지 못했습니다. 선택하신 날짜나 종목을 다시 한 번 확인해주세요.")
    else:
        # 주말 및 공휴일 결측치 보정 (직전 거래일 주가로 채우기)
        df = df.ffill().bfill()
        
        # 누적 수익률 계산
        df_return = (df / df.iloc[0] - 1) * 100
        
        # 시각화 영역과 요약 정보 영역 구성
        tab1, tab2 = st.tabs(["📈 수익률 추이 차트", "📊 상세 데이터"])
        
        with tab1:
            st.subheader("기간 내 누적 수익률 비교")
            # Plotly 라인 차트 생성
            fig = px.line(
                df_return,
                x=df_return.index,
                y=df_return.columns,
                labels={'value': '누적 수익률 (%)', 'Date': '날짜', 'variable': '종목명'},
                title="시작일 기준 누적 수익률 변화"
            )
            fig.update_layout(
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # 수익률 분석 요약 표
            st.subheader("최종 성과 요약")
            summary_list = []
            for col in df_return.columns:
                start_p = df[col].iloc[0]
                end_p = df[col].iloc[-1]
                total_ret = df_return[col].iloc[-1]
                
                summary_list.append({
                    "종목명": col,
                    "시작일 주가": f"{int(start_p):,} 원",
                    "종료일 주가": f"{int(end_p):,} 원",
                    "누적 수익률": f"{total_ret:+.2f}%"
                })
            
            summary_df = pd.DataFrame(summary_list)
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
            
        with tab2:
            st.subheader("실제 원본 주가 데이터 (수정 종가)")
            st.write(df)
            
            # CSV 다운로드 기능 제공
            csv = df.to_csv().encode('utf-8-sig') # 한글 깨짐 방지를 위해 utf-8-sig 사용
            st.download_button(
                label="📥 원본 데이터 CSV로 다운로드 받기",
                data=csv,
                file_name="korean_stock_data.csv",
                mime="text/csv"
            )

# 8. 배움과 생각을 넓히는 탐구 영역
st.markdown("""
---
### 💡 스스로 탐구해보는 학습 과제
1. **네이버 금융이나 다음 금융에서 평소 좋아하는 기업을 검색해 보세요.**
   - 예를 들어, '기아'의 종목코드는 `000270`입니다.
   - 왼쪽 사이드바의 **[종목 직접 추가하기]** 기능에 이름과 6자리 코드를 입력하고 코스피를 선택하면, 차트에 바로 반영되는 것을 확인할 수 있습니다! 내가 좋아하는 기업은 어떤 흐름을 보이고 있나요?
2. **코스피(KOSPI) 대형주와 코스닥(KOSDAQ) 기술주의 변동성 비교:**
   - 삼성전자(코스피)와 에코프로비엠(코스닥)의 누적 수익률 곡선을 비교해 보세요. 어느 쪽이 그래프의 굴곡(변동성)이 더 심한가요? 그 이유는 무엇일지 기업의 규모나 시장의 특성과 연결 지어 생각해 봅시다.
""")
