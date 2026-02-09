#!/usr/bin/env python3
"""
대중용 데일리 리포트 생성기 (투자자, 파트너사, 커뮤니티용)
Usage: python generate_public_report.py --date 2026-02-03

특징:
- 기술 용어 최소화
- 비즈니스 성과 및 마일스톤 중심
- 전략적 방향성 강조
- 내부 액션아이템 제외
- PR 친화적 톤앤매너
"""

import csv
import sys
import re
import argparse
from collections import defaultdict
from pathlib import Path
from datetime import date

csv.field_size_limit(sys.maxsize)

# ============================================================================
# 설정
# ============================================================================

NAME_MAP = {
    'YEONGJU BAK': 'Zena',
    'Jason Hwang': 'Jason',
    'Harvey Jo': 'Harvey',
    'Aryan Soni': 'Aryan',
    'Suhyeon Lee': 'Suhyeon',
    'Sahil Wasnik': 'Sahil',
    'Singh Shailendra': 'Singh',
    'Praveen Surendran': 'Praveen',
    'Manish Kumar': 'Manish',
    'Mehdi Beriane': 'Mehdi',
    'Nam Tiến': 'Nam',
    'Bernard Lee': 'Bernard',
    'Jaden Lee': 'Jaden',
    'Jaden Kong': 'Jaden',
    'Irene Kim': 'Irene',
    'Irene Bae': 'Irene',
    'Kevin Lee': 'Kevin',
    'Kevin Kim': 'Kevin',
    'Theo Lee': 'Theo',
    'Monica Kim': 'Monica',
    'Eugenie Nguyen': 'Eugenie',
    'Eugenie Park': 'Eugenie',
    'George Negru': 'George',
}

EXCLUDED_PATTERNS = [
    r'^Project\s', r'^DRB\s', r'^TRH\s', r'^Upgrade\s', r'^Meeting\s',
    r'^Notes\s', r'^Attachments', r'^Invited', r'^Summary', r'^Details',
    r'^Recording', r'^Transcript', r'^Gemini', r'Seminar'
]

DEFAULT_CSV_FILES = [
    'irene.recordings.csv',
    'jaden.recordings.csv',
    'shared.recordings.csv'
]

# 기술 용어 -> 대중 친화적 표현 매핑
TECH_TO_PUBLIC = {
    # 블록체인/암호화
    'ZKP': '영지식 증명 기술',
    'zero-knowledge proof': '영지식 증명 기술',
    'fraud proof': '보안 검증 시스템',
    'fault proof': '오류 검증 시스템',
    'rollup': '확장성 솔루션',
    'optimistic rollup': '낙관적 확장 솔루션',
    'L1': '메인 블록체인',
    'L2': '레이어2 확장 네트워크',
    'staking': '토큰 예치',
    'slashing': '부정행위 페널티',
    'sequencer': '트랜잭션 처리자',
    'challenger': '검증자',
    'validator': '검증자',
    'bisection': '분할 검증',
    'dispute': '검증 분쟁',
    'smart contract': '스마트 컨트랙트',
    'contract': '컨트랙트',
    'SDK': '개발 도구',
    'API': '연동 인터페이스',
    'DRB': '분산 랜덤 비콘',
    'PR': '코드 기여',
    'PRs': '코드 기여',
    'merge': '통합',
    'branch': '개발 브랜치',
    'refactoring': '코드 최적화',
    'end-to-end testing': '통합 테스트',
    'libP2P': '네트워크 통신 모듈',
    'RPC': '원격 호출',
    'database pool': '데이터베이스 연결',
    'cryptographic': '암호화',
    'BLS': '암호화 서명',
    # 일반 기술
    'bug': '오류',
    'debug': '오류 수정',
    'deploy': '배포',
    'implementation': '구현',
    'integration': '연동',
    'scalability': '확장성',
    'bottleneck': '성능 제약',
    'audit': '보안 감사',
    'auditing': '보안 감사',
}

# ============================================================================
# 유틸리티 함수
# ============================================================================

def get_short_name(full_name: str) -> str:
    """풀네임을 짧은 이름으로 변환"""
    if full_name in NAME_MAP:
        return NAME_MAP[full_name]
    if ' ' in full_name:
        return full_name.split()[0]
    return full_name


def replace_names_in_text(text: str) -> str:
    """텍스트 내 풀네임을 짧은 이름으로 변환"""
    for full, short in NAME_MAP.items():
        text = text.replace(full, short)
    return text


def simplify_tech_terms(text: str) -> str:
    """기술 용어를 대중 친화적 표현으로 변환"""
    result = text
    for tech, public in TECH_TO_PUBLIC.items():
        # 대소문자 구분 없이 치환
        pattern = re.compile(re.escape(tech), re.IGNORECASE)
        result = pattern.sub(public, result)
    return result


def is_valid_speaker(name: str) -> bool:
    """유효한 화자인지 확인"""
    for pattern in EXCLUDED_PATTERNS:
        if re.match(pattern, name, re.IGNORECASE):
            return False
    if name in NAME_MAP:
        return True
    words = name.split()
    if len(words) != 2:
        return False
    for w in words:
        if len(w) < 2 or len(w) > 15:
            return False
        if not w[0].isupper():
            return False
        if not re.match(r'^[A-Za-zÀ-ỹ]+$', w):
            return False
    return True


def truncate_to_sentence(text: str, max_len: int = 250) -> str:
    """텍스트를 문장 단위로 자르기"""
    if len(text) <= max_len:
        return text

    truncated = text[:max_len]

    sentence_end_patterns = [
        r'다\.\s', r'요\.\s', r'음\.\s', r'임\.\s',
        r'다\.$', r'요\.$', r'음\.$', r'임\.$',
        r'\)\.\s', r'\)\.$',
        r'[a-zA-Z]\.\s', r'[a-zA-Z]\.$',
        r'\?\s', r'\?$', r'!\s', r'!$',
    ]

    last_end = -1
    for pattern in sentence_end_patterns:
        matches = list(re.finditer(pattern, truncated))
        if matches:
            pos = matches[-1].end()
            if pos > last_end:
                last_end = pos

    if last_end > 80:
        return text[:last_end].strip()

    for i in range(len(truncated) - 1, 50, -1):
        if truncated[i] == '.':
            if i > 0 and not truncated[i-1].isdigit():
                return text[:i + 1].strip()

    last_space = truncated.rfind(' ')
    if last_space > 100:
        return text[:last_space].strip() + "..."

    return truncated.strip() + "..."


def categorize_meeting(name: str, summary: str) -> str:
    """회의를 대중 친화적 카테고리로 분류"""
    name_lower = name.lower()
    summary_lower = summary.lower()
    combined = name_lower + ' ' + summary_lower

    if any(kw in combined for kw in ['seminar', '세미나', 'research', 'paper', 'academic']):
        return '🔬 연구 & 기술 혁신'
    elif any(kw in combined for kw in ['security', 'audit', 'fraud', 'fault', 'dispute', 'slashing']):
        return '🛡️ 보안 & 안정성'
    elif any(kw in combined for kw in ['integration', 'sdk', 'platform', 'setup', 'api']):
        return '🔗 플랫폼 & 연동'
    elif any(kw in combined for kw in ['upgrade', 'improvement', 'optimization', 'scalability']):
        return '⚡ 성능 & 확장성'
    elif any(kw in combined for kw in ['weekly', 'progress', 'update', 'status']):
        return '📊 프로젝트 진행'
    elif any(kw in combined for kw in ['data', 'dashboard', 'report', 'analytics']):
        return '📈 데이터 & 분석'
    else:
        return '💼 팀 협업'


def extract_business_highlights(content: str) -> dict:
    """비즈니스 관점의 하이라이트 추출"""
    content = content.replace('\\r\\n', '\n').replace('\r\n', '\n')

    result = {
        'summary': '',
        'achievements': [],    # 성과/마일스톤
        'strategic': [],       # 전략적 결정
        'partnerships': [],    # 파트너십/협력
        'next_milestones': []  # 다음 마일스톤
    }

    # 요약 추출
    summary_patterns = [
        r'요약\s*\n(.+?)(?=\n\n세부정보|\n\nDetails|\n\n\n)',
        r'Summary\s*\n(.+?)(?=\n\nDetails|\n\n\n)',
    ]

    for pattern in summary_patterns:
        match = re.search(pattern, content, re.DOTALL)
        if match:
            raw_summary = match.group(1).strip()
            # 이름 변환 및 기술 용어 단순화
            result['summary'] = simplify_tech_terms(replace_names_in_text(raw_summary))
            break

    # 세부정보에서 비즈니스 하이라이트 추출
    details_patterns = [
        r'세부정보\s*\n(.+?)(?=\n추천하는 다음 단계|\n\n\n|$)',
        r'Details\s*\n(.+?)(?=\nSuggested next steps|\n\n\n|$)',
    ]

    details_text = ''
    for pattern in details_patterns:
        match = re.search(pattern, content, re.DOTALL)
        if match:
            details_text = match.group(1).strip()
            break

    if details_text:
        bullets = re.findall(r'\* ([^\n]+(?:\n(?!\*)[^\n]+)*)', details_text)

        for bullet in bullets:
            bullet_lower = bullet.lower()
            bullet_clean = simplify_tech_terms(replace_names_in_text(bullet))
            first_line = bullet_clean.split('\n')[0]

            # 성과/마일스톤 (완료, 달성, 출시 등)
            if any(kw in bullet_lower for kw in ['완료', 'completed', 'finished', 'achieved', 'launched',
                                                   'released', 'delivered', 'milestone', '달성', '출시']):
                result['achievements'].append(first_line)
            # 전략적 결정
            elif any(kw in bullet_lower for kw in ['결정', 'decided', 'agreed', 'strategy', 'plan',
                                                    '전략', 'approach', 'direction']):
                result['strategic'].append(first_line)
            # 파트너십/협력
            elif any(kw in bullet_lower for kw in ['partner', 'collaboration', 'integration', 'cooperation',
                                                    '협력', '파트너', '연동']):
                result['partnerships'].append(first_line)

    # 다음 마일스톤 추출 (액션아이템에서 비즈니스 관련만)
    action_patterns = [
        r'추천하는 다음 단계\s*\n(.+?)(?=\n\n|$)',
        r'Suggested next steps\s*\n(.+?)(?=\n\n|$)',
    ]

    for pattern in action_patterns:
        match = re.search(pattern, content, re.DOTALL)
        if match:
            steps = match.group(1).strip()
            items = re.findall(r'\* (.+)', steps)
            for item in items:
                item_lower = item.lower()
                # 기술적 세부사항 제외, 비즈니스 마일스톤만 포함
                if any(kw in item_lower for kw in ['fix', 'bug', 'test', 'review pr', 'merge',
                                                    'refactor', 'debug', 'check']):
                    continue
                cleaned = simplify_tech_terms(replace_names_in_text(item))
                # 담당자 이름 제거 (대외용이므로)
                cleaned = re.sub(r'^[A-Za-z가-힣]+님은?\s*(은|는)?\s*', '', cleaned)
                if len(cleaned) > 20:  # 너무 짧은 것 제외
                    result['next_milestones'].append(cleaned)

    return result


def parse_speakers_for_public(content: str) -> list:
    """참여자 목록만 추출 (발화시간 제외)"""
    speakers = set()
    content = content.replace('\\r\\n', '\n').replace('\r\n', '\n')

    transcript_markers = ['📖 Transcript', '📖 스크립트']
    transcript_start = -1
    for marker in transcript_markers:
        pos = content.find(marker)
        if pos != -1:
            transcript_start = pos
            break

    if transcript_start == -1:
        return []

    transcript_text = content[transcript_start:]
    speaker_pattern = r'^([A-Za-zÀ-ỹ][A-Za-zÀ-ỹ\s]{1,28}):\s*(.+)$'

    for line in transcript_text.split('\n'):
        line = line.strip()
        if not line:
            continue
        sp_match = re.match(speaker_pattern, line)
        if sp_match:
            speaker_name = sp_match.group(1).strip()
            if is_valid_speaker(speaker_name):
                speakers.add(get_short_name(speaker_name))

    return sorted(list(speakers))


# ============================================================================
# 리포트 생성
# ============================================================================

def load_meetings(csv_files: list, target_date: str) -> list:
    """CSV 파일들에서 특정 날짜의 회의 데이터 로드"""
    meetings = []

    date_patterns = [
        target_date.replace('-', '/'),
        f"{target_date[:4]}년 {int(target_date[5:7])}월 {int(target_date[8:10])}일"
    ]

    for csv_file in csv_files:
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    name = row.get('name', '')
                    content = row.get('content', '')

                    if not content:
                        continue

                    if not any(dp in name for dp in date_patterns):
                        continue

                    if "summary wasn't produced" in content.lower():
                        continue

                    # 파싱
                    highlights = extract_business_highlights(content)
                    participants = parse_speakers_for_public(content)

                    if not highlights['summary'] and not participants:
                        continue

                    # 회의명 정리 및 카테고리 분류
                    short_name = name
                    if ' – ' in short_name:
                        short_name = short_name.split(' – ')[0]
                    if ' - Gemini' in short_name:
                        short_name = short_name.split(' - Gemini')[0]
                    if 'KST에 시작한 회의' in short_name:
                        short_name = short_name.replace('에 시작한 회의', '')

                    # 날짜/시간 제거하여 더 깔끔하게
                    short_name = re.sub(r'\d{4}/\d{2}/\d{2}\s*\d{2}:\d{2}\s*(KST|GMT[^\s]*)?', '', short_name).strip()
                    if not short_name or short_name.isspace():
                        short_name = "팀 미팅"

                    category = categorize_meeting(name, highlights['summary'])

                    meetings.append({
                        'name': short_name.strip(),
                        'category': category,
                        'participants': participants,
                        'summary': highlights['summary'],
                        'achievements': highlights['achievements'],
                        'strategic': highlights['strategic'],
                        'partnerships': highlights['partnerships'],
                        'next_milestones': highlights['next_milestones']
                    })
        except FileNotFoundError:
            print(f"⚠️  파일 없음: {csv_file}")
            continue

    return meetings


def generate_public_report(meetings: list, target_date: str) -> str:
    """대중용 마크다운 리포트 생성"""

    year, month, day = target_date.split('-')
    weekdays = ['월', '화', '수', '목', '금', '토', '일']
    weekday = weekdays[date(int(year), int(month), int(day)).weekday()]
    date_str = f"{year}년 {int(month)}월 {int(day)}일 ({weekday})"

    output = []

    # 헤더
    output.append("# 📣 Daily Progress Report")
    output.append("")
    output.append(f"## 📅 {date_str}")
    output.append("")
    output.append("> 오늘의 주요 진행 상황을 공유합니다.")
    output.append("")
    output.append("---")
    output.append("")

    # 카테고리별로 그룹화
    categories = defaultdict(list)
    for m in meetings:
        categories[m['category']].append(m)

    # 오늘의 하이라이트 (전체 성과 요약)
    all_achievements = []
    all_strategic = []
    all_milestones = []
    all_participants = set()

    for m in meetings:
        all_achievements.extend(m['achievements'])
        all_strategic.extend(m['strategic'])
        all_milestones.extend(m['next_milestones'])
        all_participants.update(m['participants'])

    # 핵심 요약
    output.append("## 🎯 오늘의 핵심 요약")
    output.append("")
    output.append(f"- **{len(meetings)}건**의 주요 미팅 진행")
    output.append(f"- **{len(all_participants)}명**의 팀원 참여")
    if all_achievements:
        output.append(f"- **{len(all_achievements)}건**의 성과 달성")
    output.append("")
    output.append("---")
    output.append("")

    # 주요 성과 (있는 경우)
    if all_achievements:
        output.append("## 🏆 주요 성과")
        output.append("")
        for achievement in all_achievements[:5]:
            output.append(f"- ✅ {truncate_to_sentence(achievement, 150)}")
        output.append("")
        output.append("---")
        output.append("")

    # 전략적 결정 (있는 경우)
    if all_strategic:
        output.append("## 🎯 전략적 결정")
        output.append("")
        for strategic in all_strategic[:4]:
            output.append(f"- {truncate_to_sentence(strategic, 150)}")
        output.append("")
        output.append("---")
        output.append("")

    # 카테고리별 상세
    output.append("## 📋 분야별 진행 상황")
    output.append("")

    category_order = [
        '🔬 연구 & 기술 혁신',
        '🛡️ 보안 & 안정성',
        '⚡ 성능 & 확장성',
        '🔗 플랫폼 & 연동',
        '📊 프로젝트 진행',
        '📈 데이터 & 분석',
        '💼 팀 협업'
    ]

    for cat in category_order:
        if cat not in categories:
            continue

        output.append(f"### {cat}")
        output.append("")

        for m in categories[cat]:
            # 회의 제목 (있는 경우만)
            if m['name'] and m['name'] != "팀 미팅":
                output.append(f"**{m['name']}**")
                output.append("")

            # 요약
            if m['summary']:
                summary = truncate_to_sentence(m['summary'], 300)
                output.append(f"> {summary}")
                output.append("")

            # 참여자 (간략히)
            if m['participants']:
                participants_str = ', '.join(m['participants'][:5])
                if len(m['participants']) > 5:
                    participants_str += f" 외 {len(m['participants']) - 5}명"
                output.append(f"*참여: {participants_str}*")
                output.append("")

        output.append("---")
        output.append("")

    # 다음 마일스톤
    if all_milestones:
        output.append("## 🚀 다음 단계")
        output.append("")
        seen = set()
        for milestone in all_milestones[:5]:
            # 중복 제거
            milestone_short = milestone[:50]
            if milestone_short in seen:
                continue
            seen.add(milestone_short)
            output.append(f"- {truncate_to_sentence(milestone, 150)}")
        output.append("")
        output.append("---")
        output.append("")

    # 푸터
    output.append("")
    output.append("---")
    output.append("")
    output.append("*본 리포트는 팀의 일일 활동을 요약한 것입니다.*")
    output.append("")
    output.append("**문의**: [team@example.com](mailto:team@example.com)")

    return '\n'.join(output)


# ============================================================================
# 메인
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='대중용 데일리 리포트 생성기')
    parser.add_argument('--date', '-d', required=True, help='분석할 날짜 (YYYY-MM-DD)')
    parser.add_argument('--output', '-o', help='출력 파일 경로')
    parser.add_argument('--csv', '-c', nargs='+', default=DEFAULT_CSV_FILES, help='입력 CSV 파일들')

    args = parser.parse_args()

    try:
        from datetime import datetime
        datetime.strptime(args.date, '%Y-%m-%d')
    except ValueError:
        print(f"❌ 잘못된 날짜 형식: {args.date} (YYYY-MM-DD 형식 필요)")
        sys.exit(1)

    print(f"📅 {args.date} 대중용 리포트 생성 중...")

    meetings = load_meetings(args.csv, args.date)

    if not meetings:
        print(f"⚠️  {args.date}에 해당하는 회의를 찾을 수 없습니다.")
        sys.exit(0)

    print(f"✅ {len(meetings)}건의 회의 발견")

    report = generate_public_report(meetings, args.date)

    if args.output:
        output_path = args.output
    else:
        date_compact = args.date.replace('-', '')
        output_path = f"public_report_{date_compact}.md"

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"✅ 대중용 리포트 저장 완료: {output_path}")
    print()
    print("=" * 60)
    print(report[:2500])
    if len(report) > 2500:
        print("...")
        print(f"(총 {len(report)} 문자)")


if __name__ == '__main__':
    main()
