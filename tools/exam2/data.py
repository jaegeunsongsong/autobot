# -*- coding: utf-8 -*-
"""2026학년도 2학기 2차 정기시험 — 입력 데이터 (§2~§5 그대로)."""

SUBJECTS = "ABCDEFGHIJKLMNOP"
NAME = {
    "A": "독서와작문", "B": "미적분I", "C": "영어II", "D": "확률과통계",
    "E": "인문학과윤리", "F": "인공지능기초", "G": "화학반응의세계", "H": "역학과에너지",
    "I": "한국지리탐구", "J": "세포와물질대사", "K": "경제", "L": "심화일본어",
    "M": "지구시스템과학", "N": "프로그래밍", "O": "동아시아역사기행", "P": "심화중국어",
}
ENROLL = {"A": 176, "B": 176, "C": 176, "D": 167, "E": 94, "F": 83, "G": 83, "H": 74,
          "I": 69, "J": 59, "K": 52, "L": 51, "M": 51, "N": 41, "O": 36, "P": 20}
TEACHERS = {
    "A": ["한영희", "박우정", "임서정"], "B": ["김강미", "구성희", "류진표"],
    "C": ["남혜은", "손유진", "이민경"], "D": ["송재근", "구성희"],
    "E": ["김미애", "김경서"], "F": ["김다은"], "G": ["김은경"], "H": ["최진호"],
    "I": ["노석환"], "J": ["배태안"], "K": ["김경민"], "L": ["신향숙"],
    "M": ["조세라"], "N": ["송경희"], "O": ["정인광", "손경준"], "P": ["전이슬"],
}
SERIES = {"A": "국어", "B": "수학", "C": "영어", "D": "수학", "E": "사회", "F": "정보",
          "G": "과학", "H": "과학", "I": "사회", "J": "과학", "K": "사회", "L": "제2외국어",
          "M": "과학", "N": "정보", "O": "사회", "P": "제2외국어"}

# 1학년 6과목
G1 = {
    "한국사2": ["정인광", "손경준"],
    "통합사회2": ["김미애", "노석환", "박현수", "윤정희"],
    "통합과학2": ["최진호", "이호성", "박경애", "조세라"],
    "공통국어2": ["김태현", "곽준철"],
    "공통수학2": ["김순선", "최지혜"],
    "공통영어2": ["강승희", "이바다"],
}
G1_FIXED_DAY = {"한국사2": "금", "통합사회2": "월", "통합과학2": "화"}

DAYS = ["목", "금", "월", "화"]
DATES = {"목": "12/10(목)", "금": "12/11(금)", "월": "12/14(월)", "화": "12/15(화)"}
PERIOD_TIME = {1: "08:40~09:30", 2: "09:45~10:35", 3: "10:50~11:40", 4: "11:55~12:45",
               5: "13:45~14:35", 6: "14:50~15:40", 7: "15:55~16:45"}
CONSEC_PAIRS = [(1, 2), (2, 3), (3, 4), (5, 6), (6, 7)]  # 4-5 사이는 점심

# 목요일 1학년 수업 담당표 (교시 -> 1~8반 담당 교사)
THU_G1_CLASS = {
    1: "윤정희 손경준 곽준철 박경애 이바다 김미애 김태현 최지혜",
    2: "이바다 김태현 강승희 강진원 손경준 조세라 유경희 최가연",
    3: "유경희 문준성 박경애 곽준철 최지혜 강승희 김순선 최진호",
    4: "최지혜 최진호 김미애 노석환 최가연 이바다 박경애 손경준",
    5: "김태현 강승희 김순선 이바다 박현수 곽준철 정인광 유경희",
    6: "조세라 최지혜 문준성 유경희 곽준철 박경애 강승희 김태현",
    7: "이호성 윤정희 석경훈 김순선 정인광 최지혜 최가연 박경애",
}
THU_G1_CLASS = {p: set(s.split()) for p, s in THU_G1_CLASS.items()}

# 3학년 담임(+정재훈): 월·화 배정 금지, 예외는 2교시만
HR3 = {"최광진", "배태안", "박현수", "김영주", "변영민", "남재현", "손경준", "김수현", "정재훈"}

# 전이슬 출장: 화·목 1~4교시
JEON_AWAY = {("화", 1), ("화", 2), ("화", 3), ("화", 4), ("목", 1), ("목", 2), ("목", 3), ("목", 4)}

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
COMBOS = []  # [(combo_str, count)]
for line in RAW.strip().splitlines():
    c, n = line.split()
    COMBOS.append((c, int(n)))

# 면제 학생 (§4-다). 한수오 조합 'ABDEHIKO'는 §5 데이터에 없음(모든 조합이 C 포함) → 식별 불가.
EXEMPT = {
    "한수오": {"combo": "ABDEHIKO", "type": "도움반"},   # 0과목·4과목 모두 허용, 모든 인원 제약 면제
    "조명근": {"combo": "ABCDEFGH", "type": "체육부"},   # 4과목 허용, 0과목 불가
    "최진영": {"combo": "ABCDFILM", "type": "체육부"},
}
