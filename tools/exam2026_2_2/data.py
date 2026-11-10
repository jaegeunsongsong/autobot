"""2026학년도 2학기 2차 정기시험 — §5 원자료와 교사/과목 메타데이터.

모든 수치는 이 파일의 COMBOS에서 직접 계산한다. 추측 금지.
"""
import os
from collections import Counter
from itertools import combinations

RAW = """
ABCDEFGH 8
ABCDEFGJ 5
ABCDEFHN 1
ABCDEFIK 4
ABCDEFIM 2
ABCDEFIN 1
ABCDEFIO 2
ABCDEFJK 1
ABCDEFKL 1
ABCDEFLM 2
ABCDEFNO 1
ABCDEFOP 1
ABCDEGHJ 3
ABCDEGHN 1
ABCDEGJK 2
ABCDEGJL 2
ABCDEGJM 1
ABCDEGJN 1
ABCDEGJP 1
ABCDEHJN 1
ABCDEIJK 1
ABCDEIJL 1
ABCDEIJP 1
ABCDEIKL 8
ABCDEIKM 1
ABCDEIKO 2
ABCDEIKP 2
ABCDEILN 1
ABCDEILO 7
ABCDEILP 1
ABCDEIMN 2
ABCDEIMO 1
ABCDEIMP 3
ABCDEIOP 4
ABCDEJKP 1
ABCDEJMP 1
ABCDEKLM 3
ABCDEKLN 3
ABCDEKLO 2
ABCDEKOP 1
ABCDELMO 1
ABCDFGHI 1
ABCDFGHJ 18
ABCDFGHL 1
ABCDFGHM 10
ABCDFGHN 3
ABCDFGJM 2
ABCDFGKO 1
ABCDFHIM 1
ABCDFHJM 1
ABCDFHMN 1
ABCDFIKO 1
ABCDFILM 2
ABCDFILO 1
ABCDFKLN 2
ABCDFLNO 1
ABCDGHIL 1
ABCDGHIN 1
ABCDGHJL 1
ABCDGHJN 8
ABCDGHJP 1
ABCDGHKM 2
ABCDGHMN 5
ABCDGIJL 1
ABCDGJKM 2
ABCDGJKN 1
ABCDHIMN 1
ABCDHIMO 1
ABCDHKOP 1
ABCDIJKN 1
ABCDIJMN 1
ABCDIKLM 1
ABCDIKLO 2
ABCDIKOP 1
ABCDKLNO 1
ABCEFHIO 1
ABCEFIKL 1
ABCEFIKO 1
ABCEFILM 1
ABCEFILO 1
ABCEIKMP 1
ABCFHIMN 1
ABCFILMN 1
ABCFKLNO 1
"""

COMBOS = []  # list of (frozenset(subjects), count, label)
for line in RAW.strip().splitlines():
    combo, n = line.split()
    COMBOS.append((combo, int(n)))

SUBJECTS = "ABCDEFGHIJKLMNOP"
SUBJ_IDX = {s: i for i, s in enumerate(SUBJECTS)}

# 과목 정보
NAMES = {
    "A": "독서와작문", "B": "미적분I", "C": "영어II", "D": "확률과통계",
    "E": "인문학과윤리", "F": "인공지능기초", "G": "화학반응의세계", "H": "역학과에너지",
    "I": "한국지리탐구", "J": "세포와물질대사", "K": "경제", "L": "심화일본어",
    "M": "지구시스템과학", "N": "프로그래밍", "O": "동아시아역사기행", "P": "심화중국어",
}
TEACHERS = {
    "A": ["한영희", "박우정", "임서정"], "B": ["김강미", "구성희", "류진표"],
    "C": ["남혜은", "손유진", "이민경"], "D": ["송재근", "구성희"],
    "E": ["김미애", "김경서"], "F": ["김다은"], "G": ["김은경"], "H": ["최진호"],
    "I": ["노석환"], "J": ["배태안"], "K": ["김경민"], "L": ["신향숙"],
    "M": ["조세라"], "N": ["송경희"], "O": ["정인광", "손경준"], "P": ["전이슬"],
}
FIELD = {
    "A": "국어", "B": "수학", "C": "영어", "D": "수학", "E": "사회", "F": "정보",
    "G": "과학", "H": "과학", "I": "사회", "J": "과학", "K": "사회", "L": "제2외국어",
    "M": "과학", "N": "정보", "O": "사회", "P": "제2외국어",
}
# 1학년 과목
G1 = {
    "한국사2": ["정인광", "손경준"],
    "통합사회2": ["김미애", "노석환", "박현수", "윤정희"],
    "공통국어2": ["김태현", "곽준철"],
    "통합과학2": ["최진호", "이호성", "박경애", "조세라"],
    "공통수학2": ["김순선", "최지혜"],
    "공통영어2": ["강승희", "이바다"],
}
# 1학년 배치 모드. A: 통합사회2 월요일 고정(박현수 예외 1건). B: 통합사회2를 금요일(한국사2와 함께), 월요일은 공통국어2+통합과학2
G1_MODE = os.environ.get("G1_MODE", "A")

HOMEROOM3 = {"최광진", "배태안", "박현수", "김영주", "변영민", "남재현", "손경준", "김수현", "정재훈"}

# 면제 학생
EXEMPT_ALL = "ABCEFHIO"      # 도움반 1명: 0과목·4과목 모두 허용
EXEMPT_FOUR = "ABCDFILM"     # 체육부 2명: 4과목 허용, 0과목 불가

DAYS = ["목", "금", "월", "화"]
DATES = {"목": "12/10(목)", "금": "12/11(금)", "월": "12/14(월)", "화": "12/15(화)"}
PERIOD_TIME = {1: "08:40~09:30", 2: "09:45~10:35", 3: "10:50~11:40", 4: "11:55~12:45",
               5: "13:45~14:35", 6: "14:50~15:40", 7: "15:55~16:45"}
CONSEC = [(1, 2), (2, 3), (3, 4), (5, 6), (6, 7)]

# 목요일 1학년 수업으로 막히는 교시 (2학년 과목 담당자 기준)
THU_BLOCK = {"E": {1, 4}, "H": {3, 4}, "I": {4}, "M": {2, 6}, "O": {1, 2, 4, 5, 7}}
# 전이슬: 화·목 1~4교시 출장
P_BLOCK = {"목": {1, 2, 3, 4}, "화": {1, 2, 3, 4}}


def enrol(s):
    return sum(n for c, n in COMBOS if s in c)


def overlap(*subs):
    return sum(n for c, n in COMBOS if all(s in c for s in subs))


def check():
    total = sum(n for _, n in COMBOS)
    assert total == 176, total
    assert len(COMBOS) == 84, len(COMBOS)
    for c, _ in COMBOS:
        assert len(c) == 8 and len(set(c)) == 8, c
        assert set(c) <= set(SUBJECTS), c
    expected = dict(A=176, B=176, C=176, D=167, E=94, F=83, G=83, H=74, I=69, J=59,
                    K=52, L=51, M=51, N=41, O=36, P=20)
    for s, v in expected.items():
        assert enrol(s) == v, (s, enrol(s), v)
    assert overlap("E", "I") == 50
    assert overlap("H", "J") == 33
    assert overlap("E", "O") == 25
    assert overlap("L", "P") == 1
    assert overlap("N", "L") == 10
    assert overlap("J", "O") == 0
    assert overlap("N", "P") == 0
    zero = [(a, b) for a, b in combinations(SUBJECTS, 2) if overlap(a, b) == 0]
    assert zero == [("J", "O"), ("N", "P")], zero
    assert sum(n for c, n in COMBOS if c == EXEMPT_ALL) == 1
    assert sum(n for c, n in COMBOS if c == EXEMPT_FOUR) == 2
    return True


if __name__ == "__main__":
    check()
    print("검산 OK: 84개 조합, 176명, 과목별 인원·교차 인원 모두 일치")
    print("겹침 0 쌍:", [(a, b) for a, b in combinations(SUBJECTS, 2) if overlap(a, b) == 0])
    small = sorted(((overlap(a, b), a + b) for a, b in combinations(SUBJECTS, 2)))[:25]
    print("겹침 적은 쌍:", small)
    # 계열 쌍 겹침
    print("같은 계열 쌍 겹침:")
    for a, b in combinations(SUBJECTS, 2):
        if FIELD[a] == FIELD[b]:
            print(f"  {a}+{b} ({FIELD[a]}): {overlap(a,b)}")
