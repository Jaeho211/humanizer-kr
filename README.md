# Humanizer KR v0.1 — OMP · AGY · Codex · Claude

한국어 글의 어색한 AI식 표현을 줄이는 **공통 Agent Skill**. DeepSeek-V4.1-Flash, Claude Opus 5.5, Gemini 4 Argon을 주요 평가 대상으로 설계했습니다. 해당 모델에서 실제 품질 검증을 완료했다는 뜻은 아닙니다.

[참고·라이선스](NOTICE.md) · [스킬 원문](skills/humanizer-kr/SKILL.md) · [패턴 가이드](skills/humanizer-kr/references/patterns.md)

## 설치

저장소를 내려받은 뒤 프로젝트 루트에서 아래 명령 하나만 실행하세요.

```bash
bash install.sh
```

OMP, **AGY CLI**, Codex, Claude Code에 모두 설치합니다. 다시 실행하면 변경된 스킬을 자동 갱신하고 기존 파일은 백업합니다. AGY IDE는 설치 대상이 아닙니다.

## 사용

- OMP: `/skill:humanizer-kr 아래 문단을 자연스럽게 다듬어줘: ...`
- AGY CLI: `/humanizer-kr 아래 글을 최소 수정으로 윤문해줘: ...`
- Codex: `$humanizer-kr 이 Markdown 문서에서 번역투만 고쳐줘`
- Claude Code: `/humanizer-kr 다음 이메일을 윤문해줘: ...`
- 자연어 요청: `humanizer-kr 스킬을 사용해서 이 글의 AI 문체를 줄이고 숫자·고유명사는 유지해줘.`

스킬은 **요청 시 선택되는 편집 워크플로**입니다. 모든 답변에 자동 적용하는 전역 정책은 아닙니다. 항상 적용하려면 아래의 선택적 짧은 지침을 각 에이전트의 상위 컨텍스트 파일에 추가하되, 기술 출력의 정확성이 더 중요할 때는 적용하지 마세요.

```
한국어 산문 답변에서는 결론을 먼저 말하고 군더더기·과장·무의미한 도입/마무리를 피한다.
숫자, 불확실성, 전문용어, 코드, 조건은 정확히 보존한다.
사용자가 특정 글을 윤문해 달라고 요청할 때에만 humanizer-kr 스킬을 적용한다.
```

## 감사 검사 (선택)

```bash
python3 skills/humanizer-kr/scripts/audit.py --input original.md --output rewritten.md
python3 skills/humanizer-kr/scripts/audit.py --input original.md --output rewritten.md --json
python3 -m unittest discover -s tests -v
```

검사는 숫자·코드·URL·템플릿 보존을 확인하며, 표현상 주의 신호의 전후 개수를 제시합니다. 실제 모델을 호출하지 않고 윤문을 생성하지도 않습니다. 의미 보존이나 자연스러움을 자동 판별하지 않습니다. 코드 0은 검사 항목 통과, 코드 2는 리터럴 위반입니다.

## 아키텍처

```mermaid
flowchart LR
 A[한국어 원문] --> B[장르·말투 파악]
 B --> C[패턴 진단]
 C --> D[국소 윤문]
 D --> E[의미·톤 대조]
 E --> F[선택: 리터럴 감사]
 F --> G[결과]
```

공통 `SKILL.md`는 하나이고, 4개 런타임의 발견 경로에 복사하거나 심링크합니다. 런타임별 명령 호출 방식만 다르고 핵심 규칙과 평가 항목은 같습니다.

## 후속 작업

1. 3개 모델에 `examples/fixtures.jsonl` 등 동일한 평가 세트를 입력하고 자연스러움·의미보존·문체유지 3축을 사람 평가로 측정.
2. 실제 실패 사례에서 한국어 규칙을 보강. 무작정 규칙을 100개 이상 늘리기보다 정밀도 우선.
3. 필요한 경우 파일 백업, 청킹, API 기반 배치 평가, 회귀 테스트 자동화 추가.

## 범위 및 주의

- 복사/설치 로직과 단위 테스트만 이 패키지 안에서 검증합니다. OMP·AGY·Codex·Claude 실행 환경에서의 실제 스킬 로딩·윤문 품질은 미검증입니다.
- AI 탐지 도구 우회 성공을 보장하지 않습니다. 목표는 자연스러운 한국어와 원문의 정확성입니다.
- 사용자가 특정 문서의 수정을 요청하지 않는 한 설치 자체는 문서를 바꾸지 않습니다.
