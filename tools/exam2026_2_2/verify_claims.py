"""보고서에 적을 최적성 주장들을 rows_full.pkl 로 검증."""
import pickle
from collections import Counter
rows = pickle.load(open("rows_full.pkl", "rb"))
assert all(r["t2"] == 0 for r in rows), "k 선택 후 교사 2과목은 0이어야"
tue2 = [r for r in rows if r["tue3_all"] == 0]
tue3 = [r for r in rows if r["tue3_all"] > 0]
claims = {}
claims["전체 요일배정 수"] = len(rows)
claims["화3+ 0 해 수 (= 화 2유닛)"] = len(tue2)
claims["화3+ 0 & 화 유닛수 분포"] = dict(Counter(len(set(r["periods"]["화"].values())) for r in tue2))
claims["화2: 예외 분포"] = dict(Counter(r["exc"] for r in tue2))
e1 = [r for r in tue2 if r["exc"] == 1]
claims["화2·예외1: 수"] = len(e1)
claims["화2·예외1: 목요일 교시수 분포"] = dict(Counter(len(set(r["periods"]["목"].values())) for r in e1))
claims["화2·예외1: 연속 최소(인원)"] = min(r["consec_n"] for r in e1)
claims["화2·예외1: 연속 최소(건수)"] = min(r["consec_cnt"] for r in e1)
claims["화2·예외1: 3과목최대 최소"] = min(r["max3"] for r in e1)
claims["화2·예외1: 3과목합 최소"] = min(r["sum3"] for r in e1)
claims["화2·예외1: 계열 최소(인원)"] = min(r["dup_n"] for r in e1)
claims["화2·예외1: 계열 최소(건수)"] = min(r["dup_cnt"] for r in e1)
claims["화2·예외1: 계열47인 해"] = [(r["days"], r["consec_n"], r["max3"]) for r in e1 if r["dup_n"] == 47]
claims["화2·예외1: 3과목최대36인 해"] = [(r["days"], r["consec_n"], r["dup_n"]) for r in e1 if r["max3"] == 36]
claims["화2·예외1: 연속1인 해"] = [(r["days"], r["max3"], r["dup_n"]) for r in e1 if r["consec_n"] == 1]
claims["화2 전체: 연속0 해"] = dict(Counter((r["exc"], r["shape"]) for r in tue2 if r["consec_n"] == 0))
claims["화2·연속0: 3과목최대 분포"] = dict(Counter(r["max3"] for r in tue2 if r["consec_n"] == 0))
claims["화2·연속0: 계열 분포"] = dict(Counter(r["dup_n"] for r in tue2 if r["consec_n"] == 0))
claims["화2: 계열 최소 전체"] = min(r["dup_n"] for r in tue2)
claims["화2: 3과목최대 최소 전체"] = min(r["max3"] for r in tue2)
claims["화2·예외2: 최소들"] = {k: min(r[k] for r in tue2 if r["exc"] == 2) for k in ("consec_n", "max3", "dup_n")}
claims["계열0: 수"] = len([r for r in rows if r["dup_cnt"] == 0])
claims["계열0: 화3+ 최소"] = min(r["tue3_all"] for r in rows if r["dup_cnt"] == 0)
claims["계열0: 예외 분포"] = dict(Counter(r["exc"] for r in rows if r["dup_cnt"] == 0))
claims["계열0·예외1: 화3+ 최소"] = min(r["tue3_all"] for r in rows if r["dup_cnt"] == 0 and r["exc"] == 1)
d0 = [r for r in rows if r["dup_cnt"] == 0 and r["tue3_all"] == 4]
claims["계열0·화3+4: 수/예외/3과목최대/연속"] = (len(d0), dict(Counter(r["exc"] for r in d0)), sorted(set(r["max3"] for r in d0)), sorted(set(r["consec_n"] for r in d0)))
claims["화3이상: 화3+ 최소"] = min(r["tue3_all"] for r in tue3)
claims["화3이상·화3+1: 수/예외/3과목최대/계열/연속"] = (len([r for r in tue3 if r["tue3_all"] == 1]), dict(Counter((r["exc"], r["max3"], r["dup_n"], r["consec_n"]) for r in tue3 if r["tue3_all"] == 1)))
claims["화3이상·예외1: 화3+ 최소"] = min(r["tue3_all"] for r in tue3 if r["exc"] == 1)
claims["전역 3과목최대 최소"] = (min(r["max3"] for r in rows), dict(Counter((r["tue3_all"], r["exc"]) for r in rows if r["max3"] == min(x["max3"] for x in rows))))
claims["전역 3과목합 최소"] = min(r["sum3"] for r in rows)
claims["연속0 해: 모양/예외"] = dict(Counter((r["shape"], r["exc"], r["tue3_all"]) for r in rows if r["consec_n"] == 0 and r["consec_cnt"] == 0))
claims["화 4유닛: 화3+ 최소"] = min(r["tue3_all"] for r in rows if len(set(r["periods"]["화"].values())) == 4)
claims["모양별 수"] = dict(Counter(r["shape"] for r in rows))
for k, v in claims.items():
    print(f"{k}: {v}")
pickle.dump(claims, open("claims.pkl", "wb"))
