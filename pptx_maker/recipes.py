# -*- coding: utf-8 -*-
"""용도(intent) → 테마·움직임·슬라이드 뼈대·쓰는 법. 어떤 AI 든 뼈대를 받아 내용만 채우면 디자이너가 짠 흐름이 된다.

    plan("pitch", topic="반려식물 돌봄 앱", minutes=10) → 명세 뼈대(JSON) — 'TODO' 를 내용으로 바꿔 pptx_build 로 만든다.
"""
from __future__ import annotations

import json
import math

# 뼈대: (종류, 할 일 안내, 덧붙일 칸) — '@sec' 은 장마다 되풀이하는 묶음의 시작
RECIPES = {
    "training": {
        "label": "교사 연수·직무 연수", "theme": "studio", "alt": ["editorial", "civic"], "motion": "build",
        "keys": ["연수", "직무", "교원", "교사 대상", "워크숍", "역량", "training"],
        "tone": "현장 사례 → 원리 → 실습 순서. 장마다 질문으로 열고 실습·점검으로 닫는다. 화면 캡처는 shot, 일정은 schedule, 자료는 qr.",
        "skeleton": [("cover", "연수 제목(결론형)·연수명·강사·날짜"), ("statement", "청중이 공감할 질문 한 문장"),
                     ("rows", "오늘 얻어 갈 세 가지(목표)"), ("agenda", "장 목록(자동)"),
                     ("@sec", ""), ("section", "장 표지"), ("statement", "이 장의 질문"), ("bullets", "핵심 개념"), ("compare", "흔한 것 ↔ 고친 것"),
                     ("shot", "화면·자료 보여 주기(캡처 사진)"), ("workshop", "실습(단계·시간·결과물)"),
                     ("@end", ""), ("takeaways", "핵심 정리 3가지"), ("qr", "자료·설문 주소"), ("closing", "질문과 나눔")]},
    "lecture": {
        "label": "강의·설명회(성인)", "theme": "editorial", "alt": ["studio", "minimal"], "motion": "subtle",
        "keys": ["강의", "설명", "특강", "교육", "lecture", "세미나"],
        "tone": "한 장 한 메시지. 제목만 이어 읽어도 강의 줄거리가 되게.",
        "skeleton": [("cover", "강의 제목"), ("statement", "여는 질문"), ("agenda", "차례"),
                     ("@sec", ""), ("section", "장 표지"), ("bullets", "핵심"), ("chart", "근거 그래프 또는 table"), ("quote", "사례·목소리"),
                     ("@end", ""), ("takeaways", "정리"), ("closing", "마무리")]},
    "class_kids": {
        "label": "초등 수업", "theme": "classroom", "alt": ["festival"], "motion": "build",
        "keys": ["초등", "어린이", "수업", "학생", "1학년", "2학년", "3학년", "4학년", "5학년", "6학년", "놀이", "방과후"],
        "tone": "글자는 크게·짧게(한 장 1~2줄). 활동마다 정한 색(생각=하늘 sky, 활동=해바라기 sun, 정리=초록 forest). 질문·퀴즈로 참여.",
        "skeleton": [("cover", "오늘의 수업 제목(재미있게)"), ("photo", "궁금증을 여는 사진 한 장 + 질문"), ("takeaways", "오늘 배울 것 2~3"),
                     ("@sec", ""), ("section", "활동 표지(생각·활동·정리)"), ("statement", "생각 열기 질문"), ("features", "알아볼 것(아이콘)"),
                     ("workshop", "활동 방법(단계·시간)"), ("@end", ""), ("faq", "퀴즈(질문·답)"), ("takeaways", "오늘 배운 것"), ("closing", "다음 시간 예고")]},
    "class_teen": {
        "label": "중등·고등 수업", "theme": "classroom", "alt": ["editorial", "studio"], "motion": "build",
        "keys": ["중학", "고등", "중등", "수업", "단원", "교과"],
        "tone": "단원 질문 → 개념 → 예시 → 활동 → 정리. 개념은 definition, 비교는 versus·compare.",
        "skeleton": [("cover", "단원·차시 제목"), ("statement", "핵심 질문"), ("agenda", "학습 흐름"),
                     ("@sec", ""), ("section", "활동"), ("definition", "핵심 개념"), ("compare", "예시 비교"), ("workshop", "활동"),
                     ("@end", ""), ("takeaways", "정리"), ("qr", "제출·자료 주소"), ("closing", "다음 차시")]},
    "parents": {
        "label": "학부모 설명회", "theme": "civic", "alt": ["calm", "classroom"], "motion": "subtle", "accent": "forest", "scale": 1.15,
        "keys": ["학부모", "설명회", "보호자", "가정", "입학"],
        "tone": "존댓말, 큰 글자(본문 20pt 이상), 일정·연락처·QR 을 분명히. 규칙은 표 한 장으로.",
        "skeleton": [("cover", "설명회 제목·학교·날짜"), ("statement", "인사와 오늘의 목적"), ("schedule", "오늘 순서(시간)"),
                     ("features", "운영의 세 기둥(아이콘)"), ("roadmap", "한 해 일정"), ("table", "평가·생활 규칙"), ("checklist", "가정에서 도와주실 일"),
                     ("qr", "연락 창구·설문"), ("closing", "질의응답")]},
    "public": {
        "label": "공공 보고·정책 브리핑", "theme": "civic", "alt": ["report", "consulting"], "motion": "subtle",
        "keys": ["정책", "공공", "기관", "교육청", "행정", "사업 계획", "추진", "브리핑", "보고"],
        "tone": "핵심 요약을 맨 앞에. 추진 배경 → 현황·문제 → 비전·목표·전략 → 세부 과제 → 일정 → 예산 → 기대 효과. 기준일 표기.",
        "skeleton": [("cover", "사업명·기관·날짜"), ("takeaways", "핵심 요약 3줄"), ("@sec", ""), ("section", "장 표지"), ("bullets", "배경·현황"),
                     ("chart", "현황 수치"), ("pyramid", "비전–목표–전략"), ("table", "세부 과제"), ("@end", ""), ("roadmap", "추진 일정"),
                     ("kpi", "예산·성과 지표"), ("closing", "협조 사항")]},
    "report": {
        "label": "결과 보고·연구 보고", "theme": "editorial", "alt": ["report", "academic"], "motion": "subtle",
        "keys": ["결과", "성과", "운영 보고", "연구학교", "실적", "결과보고"],
        "tone": "결론형 제목. 숫자에는 기준·단위·출처. 사전→사후 비교는 dumbbell·slope, 반응은 likert.",
        "skeleton": [("cover", "보고 제목"), ("takeaways", "핵심 결과 3가지"), ("agenda", "차례"), ("@sec", ""), ("section", "장 표지"),
                     ("stats", "핵심 숫자"), ("chart", "변화 그래프"), ("quote", "현장의 목소리"), ("@end", ""), ("two", "결론과 제언"), ("closing", "마무리")]},
    "data": {
        "label": "데이터·KPI 보고", "theme": "report", "alt": ["consulting"], "motion": "subtle",
        "keys": ["kpi", "지표", "대시보드", "데이터 보고", "분석 결과", "실적", "매출", "월간", "주간"],
        "tone": "첫 장에 상태 한 줄('5개 중 3개 달성'). 모든 숫자에 비교 기준(목표·지난해). 상태 색(초록·빨강)은 상태에만.",
        "skeleton": [("cover", "보고 제목·기간"), ("kpi", "핵심 지표(첫 타일 크게, delta 포함)"), ("chart", "추세(line, target)"),
                     ("chart", "요인 분해(waterfall)"), ("chart", "부문 비교(column 또는 bars)"), ("progress", "목표 대비"), ("table", "이슈·조치"),
                     ("closing", "다음 단계")]},
    "weekly": {
        "label": "주간·월간 업무 보고", "theme": "report", "alt": ["consulting", "editorial"], "motion": "none",
        "keys": ["주간", "월간", "업무 보고", "진행 상황", "스탠드업"],
        "tone": "짧게. 지난 기간 결과 → 지표 → 이슈 → 다음 계획.",
        "skeleton": [("cover", "보고 제목·기간"), ("kpi", "이번 주 지표"), ("checklist", "완료한 일"), ("table", "이슈·담당·기한"),
                     ("roadmap", "다음 계획"), ("closing", "요청 사항")]},
    "strategy": {
        "label": "경영 전략·컨설팅 보고", "theme": "consulting", "alt": ["report", "civic"], "motion": "subtle",
        "keys": ["전략", "컨설팅", "이사회", "경영", "사업 검토", "진단", "strategy"],
        "tone": "상황–문제–해결(SCR). 액션 타이틀(결론 문장)만 읽어도 이야기가 되게. 장마다 아래 핵심 막대(note).",
        "skeleton": [("cover", "보고 제목·고객사·날짜"), ("takeaways", "경영진 요약(결론 + 근거 3)"), ("@sec", ""), ("section", "장 표지"),
                     ("chart", "근거 그래프(+note 핵심 막대)"), ("matrix", "선택지 평가 2×2"), ("table", "비교표"), ("@end", ""),
                     ("roadmap", "실행 단계(웨이브)"), ("bullets", "위험과 대응"), ("closing", "다음 단계")]},
    "pitch": {
        "label": "투자 피치·창업 발표", "theme": "pitch", "alt": ["keynote", "swiss"], "motion": "dynamic",
        "keys": ["피치", "투자", "창업", "스타트업", "ir", "데모데이", "pitch", "사업계획"],
        "tone": "10~14장. 문제는 숫자 하나로, 해결은 제품 사진으로. 성장은 위로 가는 그래프 하나. 마지막은 요청 금액과 쓰임.",
        "skeleton": [("cover", "한 줄 정의"), ("bignum", "문제의 크기(숫자 하나)"), ("statement", "왜 지금인가"), ("split", "해결책(제품 사진)"),
                     ("features", "핵심 기능 3"), ("chart", "시장 크기(column: TAM·SAM·SOM)"), ("kpi", "성과·지표"), ("chart", "성장(line)"),
                     ("matrix", "경쟁 구도 2×2"), ("pricing", "수익 모델"), ("team", "팀"), ("roadmap", "이정표"), ("bignum", "투자 요청 금액"),
                     ("closing", "연락처")]},
    "launch": {
        "label": "제품 출시·키노트", "theme": "keynote", "alt": ["pitch", "tech"], "motion": "morph",
        "keys": ["출시", "런칭", "키노트", "신제품", "발표회", "launch", "keynote"],
        "tone": "한 장에 한 가지 놀라움. 큰 사진·큰 숫자·한 문장. Morph 로 제품이 이어서 움직이게.",
        "skeleton": [("cover", "제품 이름"), ("photo", "제품 사진 + 한 문장"), ("bignum", "가장 놀라운 숫자"), ("features", "새로운 점"),
                     ("versus", "이전 vs 새것"), ("gallery", "사용 장면"), ("pricing", "가격·구성"), ("closing", "출시일·구매처")]},
    "marketing": {
        "label": "마케팅 제안·브랜드 이야기", "theme": "magazine", "alt": ["poster", "gallery"], "motion": "subtle",
        "keys": ["마케팅", "브랜드", "캠페인 제안", "광고", "기획안", "제안서"],
        "tone": "소비자 통찰(인용) → 문제 → 핵심 아이디어(한 줄, 아주 크게) → 실행 예시 → 일정·지표·예산.",
        "skeleton": [("cover", "제안 제목(대표 사진)"), ("quote", "소비자의 한마디"), ("statement", "브랜드 과제"), ("team", "타깃(사람 묘사)"),
                     ("statement", "핵심 아이디어(아주 크게)"), ("gallery", "무드보드"), ("features", "실행 아이디어"), ("roadmap", "채널·일정"),
                     ("kpi", "목표 지표"), ("closing", "함께할 이유")]},
    "campaign": {
        "label": "캠페인·동기 부여 강연·선언", "theme": "poster", "alt": ["festival", "minimal"], "motion": "dynamic",
        "keys": ["캠페인", "동기", "비전", "선언", "다짐", "슬로건"],
        "tone": "짧고 강한 문장. 장마다 한 색 면. 숫자는 크게.",
        "skeleton": [("cover", "슬로건"), ("statement", "문제 제기"), ("bignum", "충격적인 숫자"), ("section", "약속 1"), ("statement", "약속 문장"),
                     ("section", "약속 2"), ("statement", "약속 문장"), ("takeaways", "행동 3가지"), ("closing", "함께하자")]},
    "academic": {
        "label": "학회 발표·논문 심사", "theme": "academic", "alt": ["minimal", "editorial"], "motion": "none",
        "keys": ["학회", "논문", "학위", "심사", "연구 발표", "thesis", "conference", "연구 방법"],
        "tone": "주장–근거(assertion–evidence): 제목은 결론 문장, 본문은 그림 하나. 출처·그림 번호. 마지막은 기여 3가지·한계·향후 과제.",
        "skeleton": [("cover", "논문 제목·저자·소속·지도교수·날짜"), ("bullets", "연구 배경"), ("statement", "연구 질문(빈틈)"), ("rows", "연구 가설·목적"),
                     ("flow", "연구 방법(절차)"), ("table", "연구 대상·도구"), ("chart", "결과 1(그림)"), ("chart", "결과 2(그림)"), ("text", "논의"),
                     ("bullets", "한계"), ("takeaways", "기여 3가지"), ("closing", "질의응답")]},
    "tech": {
        "label": "개발자 발표·IT·AI 교육", "theme": "tech", "alt": ["keynote", "swiss"], "motion": "dynamic",
        "keys": ["개발", "코드", "ai", "인공지능", "프로그래밍", "it", "기술", "llm", "api", "해커톤", "컨퍼런스"],
        "tone": "문제 이야기 → 동작 원리(도식) → 코드(12줄 이하, 강조 줄) → 데모 → 성능 → 함정 → 정리.",
        "skeleton": [("cover", "발표 제목·발표자"), ("team", "나는 누구(한 명)"), ("statement", "겪은 문제"), ("flow", "동작 원리"),
                     ("code", "핵심 코드(focus 줄 강조)"), ("shot", "데모 화면"), ("chart", "성능 비교(column)"), ("faq", "흔한 함정"),
                     ("takeaways", "정리"), ("qr", "저장소·자료"), ("closing", "고맙습니다")]},
    "portfolio": {
        "label": "디자인 포트폴리오·크리에이티브", "theme": "swiss", "alt": ["gallery", "minimal"], "motion": "dynamic",
        "keys": ["포트폴리오", "디자인", "건축", "작품", "크리에이티브", "portfolio"],
        "tone": "프로젝트마다: 전면 사진 → 과제 → 과정 격자 → 결과(숫자·인용).",
        "skeleton": [("cover", "이름·분야"), ("agenda", "프로젝트 목록"), ("@sec", ""), ("section", "프로젝트 표지(사진)"), ("text", "과제·역할"),
                     ("gallery", "과정"), ("bignum", "결과 숫자"), ("@end", ""), ("closing", "연락처")]},
    "event": {
        "label": "축제·체육대회·행사 안내", "theme": "festival", "alt": ["poster", "classroom"], "motion": "dynamic",
        "keys": ["축제", "체육대회", "행사", "페스티벌", "대회", "공연", "운동회", "festival"],
        "tone": "언제·어디·누구 를 크게. 시간표는 schedule(지금 행 hi), 경기·부스마다 한 장, 안전·시상, 행사장 화면이면 auto_advance.",
        "skeleton": [("cover", "행사 이름·날짜·장소"), ("stats", "언제·어디·누가(3칸)"), ("schedule", "시간표"), ("@sec", ""), ("section", "종목·부스"),
                     ("features", "규칙·방법"), ("@end", ""), ("checklist", "안전 수칙"), ("pricing", "시상"), ("qr", "참가 신청·안내"), ("closing", "함께해요")]},
    "ceremony": {
        "label": "시상식·졸업식·의전", "theme": "noir", "alt": ["minimal", "magazine"], "motion": "subtle",
        "keys": ["시상", "졸업", "입학", "기념식", "의전", "수여", "취임", "개회", "ceremony", "award"],
        "tone": "가운데 정렬, 천천히 나타나기. 순서마다 표지 한 장. 수상자는 이름·사진·공적 한 줄.",
        "skeleton": [("cover", "행사 이름·날짜"), ("schedule", "식순"), ("section", "개회"), ("statement", "환영의 말"), ("section", "시상"),
                     ("team", "수상자"), ("quote", "축사 한 줄"), ("closing", "폐회")]},
    "counseling": {
        "label": "상담·심리·건강·마음 챙김", "theme": "calm", "alt": ["minimal"], "motion": "subtle",
        "keys": ["상담", "심리", "마음", "건강", "스트레스", "명상", "복지", "정서", "회복"],
        "tone": "부드럽고 여유 있게. 빨강 없이. 마지막에 도움 받을 곳(연락처)을 분명히.",
        "skeleton": [("cover", "주제"), ("statement", "마음 열기 질문"), ("bignum", "공감 숫자(부드럽게)"), ("definition", "개념"),
                     ("steps", "따라 하기(시간)"), ("statement", "돌아보기 질문"), ("features", "도움 받을 곳"), ("closing", "연락처")]},
    "talk": {
        "label": "강연·인문·오프닝(말이 주인공)", "theme": "minimal", "alt": ["magazine", "gallery"], "motion": "subtle",
        "keys": ["강연", "인문", "철학", "에세이", "북토크", "ted", "이야기"],
        "tone": "글자보다 말. 한 장에 문장 하나·사진 하나. 숫자는 하나만 크게.",
        "skeleton": [("cover", "강연 제목"), ("statement", "첫 문장"), ("photo", "장면"), ("statement", "전환"), ("bignum", "숫자 하나"),
                     ("quote", "인용"), ("text", "이야기"), ("statement", "마지막 문장"), ("closing", "고맙습니다")]},
    "exhibition": {
        "label": "전시·문화 기획서", "theme": "gallery", "alt": ["magazine", "swiss"], "motion": "subtle",
        "keys": ["전시", "문화", "기획서", "예술", "공간", "큐레이션"],
        "tone": "여백과 선. 작품·공간 사진을 크게.",
        "skeleton": [("cover", "전시 이름"), ("text", "기획 의도"), ("gallery", "주요 작품"), ("roadmap", "일정"), ("table", "예산"), ("closing", "문의")]},
    "workshop": {
        "label": "워크숍·회의 진행", "theme": "studio", "alt": ["editorial"], "motion": "build",
        "keys": ["워크숍", "회의", "브레인스토밍", "퍼실리테이션", "협의회"],
        "tone": "목표 → 규칙 → 활동(시간) → 나눔 → 결정 사항.",
        "skeleton": [("cover", "워크숍 이름"), ("takeaways", "오늘의 목표"), ("schedule", "진행 순서"), ("checklist", "함께 지킬 것"),
                     ("workshop", "활동 1"), ("workshop", "활동 2"), ("matrix", "모은 생각 정리 2×2"), ("table", "결정 사항·담당"), ("closing", "다음 만남")]},
    "recruit": {
        "label": "회사·기관 소개·채용 설명회", "theme": "keynote", "alt": ["pitch", "editorial"], "motion": "dynamic",
        "keys": ["채용", "회사 소개", "기관 소개", "리크루팅", "인재", "복지"],
        "tone": "숫자와 사람 중심. 일하는 방식·성장·복지·지원 방법.",
        "skeleton": [("cover", "회사 이름·한 줄 소개"), ("stats", "회사 숫자"), ("features", "일하는 방식"), ("team", "함께할 사람들"),
                     ("testimonials", "구성원의 목소리"), ("table", "복지·제도"), ("flow", "지원 절차"), ("qr", "지원 주소"), ("closing", "연락처")]},
}


def pick_intent(text):
    """주제 글에서 용도를 고른다(키워드 점수). 못 고르면 'lecture'."""
    t = (text or "").lower()
    best, score = "lecture", 0
    for k, r in RECIPES.items():
        if k == t:
            return k
        n = sum(1 for kw in r.get("keys", []) if kw.lower() in t)
        if r["label"] in text:
            n += 3
        if n > score:
            best, score = k, n
    return best


def recipes_doc():
    out = []
    for k, r in RECIPES.items():
        flow = " → ".join(t for t, _ in r["skeleton"] if not t.startswith("@"))
        out.append(f"- **{k}** ({r['label']}) — 테마 {r['theme']} (대안: {', '.join(r.get('alt', []))}), 움직임 {r['motion']}\n  흐름: {flow}\n  쓰는 법: {r['tone']}")
    return "\n".join(out)


TEMPLATES = {   # 종류별 채울 칸 예(모델이 그대로 바꿔 쓰게)
    "cover": {"kicker": "TODO 행사·과정 이름", "title": "TODO 결론형 제목\n**강조할 말**", "sub": "TODO 부제 한 줄", "presenter": "TODO 발표자", "date": "TODO 2026. 10."},
    "statement": {"lines": ["TODO 청중에게 던지는", "**한 문장**"], "sub": "TODO 덧붙임(생략 가능)"},
    "agenda": {"title": "오늘의 흐름"},
    "section": {"sub": "TODO 이 장에서 다룰 것"},
    "bullets": {"title": "TODO 결론형 제목", "items": ["TODO 근거 1 **강조**", "TODO 근거 2", "TODO 근거 3"]},
    "rows": {"title": "TODO 제목", "rows": [["TODO 항목", "TODO 설명"], ["TODO", "TODO"], ["TODO", "TODO"]]},
    "compare": {"title": "TODO 제목", "before": "TODO 흔한 방식", "after": "TODO **고친 방식**", "before_label": "TODO", "after_label": "TODO"},
    "shot": {"title": "TODO 제목", "image": "TODO 사진 이름", "items": ["TODO 볼 곳 1", "TODO 볼 곳 2"], "caption": "TODO 캡션"},
    "workshop": {"n": 1, "title": "TODO 실습 제목", "minutes": 10, "steps": ["TODO 단계 1", "TODO 단계 2", "TODO 단계 3"], "out": "TODO 결과물"},
    "takeaways": {"title": "TODO 정리 제목", "items": ["TODO 핵심 1", "TODO 핵심 2", "TODO 핵심 3"]},
    "qr": {"title": "TODO 자료·설문은 여기에서", "url": "https://TODO", "text": "TODO 설명"},
    "closing": {"title": "질문과 나눔", "sub": "TODO 한 줄", "presenter": "TODO", "contact": ["TODO 메일·주소"]},
    "photo": {"image": "TODO 사진 이름", "title": "TODO 사진 위 한 문장"},
    "features": {"title": "TODO 제목", "items": [{"icon": "TODO 아이콘(예: 학교)", "title": "TODO", "body": "TODO"}] * 3},
    "faq": {"title": "TODO 퀴즈", "items": [["TODO 질문", "TODO 답"]] * 3},
    "definition": {"term": "TODO 낱말", "body": "TODO 뜻", "example": "TODO 보기"},
    "schedule": {"title": "TODO 시간표", "rows": [["09:30", "TODO 순서", "TODO 장소"]] * 4},
    "roadmap": {"title": "TODO 일정", "periods": ["TODO 1월", "2월", "3월", "4월"], "lanes": [{"name": "TODO 과제", "bars": [[0, 1, "TODO"]]}]},
    "table": {"title": "TODO 제목", "headers": ["TODO", "TODO", "TODO"], "rows": [["TODO", "TODO", "TODO"]] * 3},
    "checklist": {"title": "TODO 점검표", "items": ["TODO 항목"] * 4},
    "kpi": {"title": "TODO 지표 제목", "items": [{"value": "TODO", "label": "TODO", "delta": "+TODO"}] * 4, "hi": [0]},
    "chart": {"title": "TODO 결론형 제목", "chart": "column", "data": {"labels": ["TODO"], "values": [0]}, "side_title": "TODO", "side": ["TODO"]},
    "stats": {"title": "TODO 제목", "items": [["TODO 숫자", "TODO 이름", "TODO 설명"]] * 3},
    "bignum": {"value": "TODO 숫자", "label": "TODO 무엇의 숫자", "sub": "TODO 설명", "context": "TODO 기준·출처"},
    "split": {"title": "TODO 제목", "image": "TODO 사진", "body": "TODO 설명", "items": ["TODO"]},
    "matrix": {"title": "TODO 제목", "cells": [{"title": "TODO", "body": "TODO"}] * 4, "xname": "TODO", "yname": "TODO"},
    "pricing": {"title": "TODO 제목", "plans": [{"name": "TODO", "price": "TODO", "features": ["TODO"]}] * 3, "hi": 1},
    "team": {"title": "TODO 제목", "people": [{"name": "TODO", "role": "TODO", "desc": "TODO"}] * 3},
    "versus": {"title": "TODO 제목", "left": {"title": "TODO", "items": ["TODO"]}, "right": {"title": "TODO", "items": ["TODO"], "hi": True}},
    "gallery": {"title": "TODO 제목", "images": ["TODO 사진1", "TODO 사진2", "TODO 사진3"]},
    "quote": {"text": "TODO 인용 문장", "who": "TODO 누구(가명)"},
    "flow": {"title": "TODO 제목", "steps": [["TODO 단계", "TODO 설명"]] * 4},
    "steps": {"title": "TODO 제목", "steps": [["TODO 단계", "TODO 설명"]] * 4},
    "pyramid": {"title": "TODO 제목", "levels": [["TODO 비전", "TODO"], ["TODO 목표", "TODO"], ["TODO 전략", "TODO"]]},
    "progress": {"title": "TODO 제목", "items": [["TODO 항목", 70, 80]] * 3},
    "text": {"title": "TODO 제목", "body": "TODO 문단 1\nTODO 문단 2", "pull": "TODO 강조 한 문장"},
    "code": {"title": "TODO 제목", "code": "TODO 코드", "lang": "python", "focus": [1]},
    "two": {"title": "TODO 제목", "left": {"label": "TODO", "title": "TODO", "items": ["TODO"]}, "right": {"label": "TODO", "title": "TODO", "items": ["TODO"]}},
    "testimonials": {"title": "TODO 제목", "items": [{"text": "TODO 후기", "who": "TODO"}] * 3},
}


def plan(intent=None, topic="", minutes=None, sections=None, audience=""):
    """용도별 명세 뼈대. sections 를 주면 그 장 제목으로, minutes 로 장 안 묶음 수를 조절한다."""
    it = intent if intent in RECIPES else pick_intent((intent or "") + " " + (topic or ""))
    r = RECIPES[it]
    sk = r["skeleton"]
    if "@sec" in [t for t, _ in sk]:
        a = [t for t, _ in sk].index("@sec")
        b = [t for t, _ in sk].index("@end")
        head, block, tail = sk[:a], sk[a + 1:b], sk[b + 1:]
    else:
        head, block, tail = sk, [], []
    n_sec = len(sections) if sections else 0
    if block and not n_sec:
        per = max(1, len(block))
        total = (minutes or 20) / (1.3 if it in ("training", "lecture", "class_kids", "class_teen") else 1.0)
        n_sec = max(2, min(6, round((total - len(head) - len(tail)) / per)))
    secs = []
    if block:
        names = sections or [f"TODO 장 {i + 1} 제목" for i in range(n_sec)]
        from .theme import get_theme
        pal = get_theme(r["theme"]).d.get("section_accents") or ["blue"]
        for i, nm in enumerate(names):
            secs.append({"key": f"p{i + 1}", "label": f"PART {i + 1}", "title": nm, "accent": pal[i % len(pal)], "desc": "TODO 한 줄 설명"})
    slides = []

    def add(typ, hint, sec=None):
        sp = {"type": typ}
        if sec:
            sp["section"] = sec
        sp.update(json.loads(json.dumps(TEMPLATES.get(typ, {"title": "TODO 제목"}), ensure_ascii=False)))
        if typ == "section":
            sp.pop("title", None)
        sp["notes"] = f"TODO 발표 대본 — {hint}"
        sp["_hint"] = hint
        slides.append(sp)
    for t, h in head:
        add(t, h)
    for s in secs:
        for t, h in block:
            add(t, h, s["key"])
    for t, h in tail:
        add(t, h)
    spec = {"intent": it, "theme": r["theme"], "motion": r["motion"], "title": topic or "TODO 덱 제목", "images": ["photos"],
            "sections": secs, "slides": slides}
    if r.get("accent"):
        spec["accent"] = r["accent"]
    return {"intent": it, "label": r["label"], "tone": r["tone"], "alt_themes": r.get("alt", []),
            "how": "slides 의 TODO 를 내용으로 바꾸고 _hint 는 지운다(남겨도 무시됨). 같은 종류가 3장 이어지면 다른 종류로 바꾼다. 모든 장에 notes.",
            "spec": spec}
