import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# 1. 웹페이지 기본 설정
st.set_page_config(
    page_title="한-미 주요 주식 수익률 비교기",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. 타이틀 및 앱 소개
st.title("📊 한국 & 미국 주요 주식 수익률 비교 분석기")
st.markdown("""
당곡고등학교 학생 여러분 반갑습니다! 이 웹앱은 `yfinance` API를 활용하여 한국과 미국의 주요 기업 주가 데이터를 가져온 뒤, 
서로 다른 주가 규모를 가진 주식들의 **누적 수익률(%)**을 직관적으로 비교해 볼 수 있는 학습용 데이터 분석 도구입니다.
""")

# 3. 주식 정보 매핑 사전 (이름: 야후파이낸스 티커)
# 한국 주식은 끝에 .KS(코스피) 또는 .KQ(코스닥)를 붙여야 합니다.
stock_dict = {
    # 한국 주식
    "삼성전자 (KS)": "005930.KS",
    "SK하이닉스 (KS)": "000660.KS",
    "NAVER (KS)": "003542.KS",
    "카카오 (KS)": "035720.KS",
    # 미국 주식
    "애플 (AAPL)": "AAPL",
    "마이크로소프트 (MSFT)": "MSFT",
    "테슬라 (TSLA)": "TSLA",
    "엔비디아 (NVDA)": "NVDA",
    "S&P 500 지수 (SPY)": "SPY",
    "나스닥 100 지수 (QQQ)": "QQQ"
}

# 4. 사이드바 설정 (사용자 입력 컨트롤러)
st.sidebar.header("⚙️ 분석 옵션 설정")

# 주식 선택 (기본값으로 삼성전자, 애플, 테슬라 지정)
selected_stock_names = st.sidebar.multiselect(
    "비교할 주식을 선택하세요 (복수 선택 가능):",
    options=list(stock_dict.keys()),
    default=["삼성전자 (KS)", "애플 (AAPL)", "테슬라 (TSLA)"]
)

# 날짜 범위 설정 (기본값: 오늘부터 1년 전까지)
start_date = st.sidebar.date_input("조회 시작일", datetime.now() - timedelta(days=365))
end_date = st.sidebar.date_input("조회 종료일", datetime.now())

# 5. yfinance 데이터 수집 함수 (캐싱 처리하여 속도 향상)
@st.cache_data
def load_data(tickers, start, end):
    data = pd.DataFrame()
    for name, ticker in tickers.items():
        try:
            # 개별 주식 데이터 다운로드
            ticker_df = yf.download(ticker, start=start, end=end)
            if not ticker_df.empty:
                # 수정 종가(Adj Close)를 사용하여 배당이나 주식 분할 등이 반영된 실제 가치를 구함
                if 'Adj Close' in ticker_df.columns:
                    series = ticker_df['Adj Close']
                else:
                    series = ticker_df['Close']
                
                # 가끔 multi-index 형태로 가져오는 에러 방지
                if isinstance(series, pd.DataFrame):
                    series = series.iloc[:, 0]
                
                data[name] = series
        except Exception as e:
            st.error(f"{name}({ticker}) 데이터를 가져오는 중 오류가 발생했습니다: {e}")
    return data

# 6. 메인 로직 실행
if not selected_stock_names:
    st.warning("⚠️ 왼쪽 사이드바에서 비교할 주식을 최소 하나 이상 선택해 주세요!")
else:
    # 사용자가 선택한 주식 이름들만 모아서 티커 사전 재구성
    selected_tickers = {name: stock_dict[name] for name in selected_stock_names}
    
    with st.spinner("야후 파이낸스로부터 금융 데이터를 안전하게 불러오는 중..."):
        df = load_data(selected_tickers, start_date, end_date)
        
    if df.empty:
        st.error("불러온 데이터가 없습니다. 선택하신 주식이나 날짜 범위를 다시 확인해 주세요.")
    else:
        # 한국과 미국의 시차 및 휴장일 차이로 발생하는 결측치(NaN) 해결을 위해 앞/뒤 데이터로 채움
        df = df.ffill().bfill()
        
        # 💡 누적 수익률 계산 공식: ((현재 주가 / 시작일 주가) - 1) * 100
        # 이 방식을 쓰면 서로 다른 주가(예: 7만원 삼성전자 vs 200달러 애플)를 '0%' 기준선에서 공평하게 비교 가능해요!
        df_return = (df / df.iloc[0] - 1) * 100
        
        # 화면 레이아웃 분할 (왼쪽: 차트, 오른쪽: 요약 표)
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader("📈 선택한 기간 누적 수익률 비교 추이")
            
            # Plotly Express를 활용한 인터랙티브 선그래프 시각화
            fig = px.line(
                df_return, 
                x=df_return.index, 
                y=df_return.columns,
                labels={'value': '누적 수익률 (%)', 'Date': '날짜', 'variable': '기업명'},
                title="시간 경과에 따른 누적 수익률 (%)"
            )
            fig.update_layout(
                hovermode="x unified",  # 마우스를 올렸을 때 동일 날짜의 모든 주식 데이터를 한 번에 표시
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            st.subheader("📊 핵심 지표 요약")
            st.write("조회 기간의 마지막 거래일 기준 최종 성과입니다.")
            
            summary_list = []
            for col in df_return.columns:
                start_price = df[col].iloc[0]
                end_price = df[col].iloc[-1]
                total_return = df_return[col].iloc[-1]
                
                # 한국 주식과 미국 주식 단위 다름을 인지하고 유연하게 표시
                unit = "$" if "KS" not in col else "원"
                
                summary_list.append({
                    "기업명": col,
                    "시작일 가격": f"{start_price:,.1f} {unit}",
                    "종료일 가격": f"{end_price:,.1f} {unit}",
                    "최종 누적 수익률": f"{total_return:+.2f}%"
                })
                
            summary_df = pd.DataFrame(summary_list)
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
            
        # 7. 세부 원본 데이터(접이식 버튼 메뉴로 제공)
        with st.expander("🔍 날짜별 실제 수정 종가 원본 데이터 보기"):
            st.dataframe(df)

# 당곡고 학생들의 주체적 탐구를 유도하는 영역
st.markdown("""
---
### 💡 스스로 탐구하고 생각해보는 질문 목록 (데이터 분석가 되어보기!)
1. **한국과 미국 시장의 시차/휴장일 처리:** 
   코드 속 `df.ffill().bfill()` 구문은 결측치(NaN)를 직전 거래일이나 직후 거래일의 주가로 채우는 역할을 합니다. 두 국가의 휴장일이 다를 때 왜 이 처리가 필수적일지 생각해 보세요.
2. **트렌드 분석:** 
   최근 1년간 한국의 IT 대장주(삼성전자, SK하이닉스)와 미국의 빅테크 기업(엔비디아, 애플) 중 어느 쪽이 우세한 누적 수익률을 보였나요? 왜 그런 차이가 발생했을지 금리, 산업 동향 등과 연결지어 추론해보세요.
3. **날짜 범위 좁히기:** 
   날짜 조절기(Date Input)를 활용해 특정 경제 뉴스(예: 금리 인상 발표일, 주요 기업 실적 발표일)가 있었던 주로 기간을 좁혀보고, 주가가 뉴스를 반영하는 속도를 관찰해보세요.
""")
